"""
機器學習模型工具和特徵工程管道
參考 test.py 的邏輯
"""
import pandas as pd
import numpy as np
import re
import joblib
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer


# 系統代碼對應
SYS_MAP = {
    "DR": 0,
    "SW": 1,
    "WW": 2,
    "PW": 3,
    "RW": 4,
    "IE": 5,
}

# 預測閾值
THRESHOLD = 0.3

# Sentence Transformer 模型名稱
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# 全域變數儲存載入的模型（避免重複載入）
_model = None
_pca = None
_type_embedding_map = None
_embed_model = None


class ModelNotFoundError(Exception):
    """當資料庫中找不到啟用的模型時拋出"""
    pass


def load_models():
    """載入所有模型（singleton pattern）"""
    global _model, _pca, _type_embedding_map, _embed_model
    
    # 延遲導入避免循環依賴
    from .models import MLModel
    
    if _model is None:
        print("Loading XGBoost model from database...")
        try:
            ml_model = MLModel.objects.get(model_type='xgboost', is_active=True)
            _model = joblib.load(ml_model.file.path)
        except MLModel.DoesNotExist:
            raise ModelNotFoundError(
                "找不到啟用的 XGBoost 模型。請在 Django admin 中上傳並啟用 XGBoost 模型。"
            )
    
    if _pca is None:
        print("Loading PCA model from database...")
        try:
            ml_model = MLModel.objects.get(model_type='pca', is_active=True)
            _pca = joblib.load(ml_model.file.path)
        except MLModel.DoesNotExist:
            raise ModelNotFoundError(
                "找不到啟用的 PCA 模型。請在 Django admin 中上傳並啟用 PCA 模型。"
            )
    
    if _type_embedding_map is None:
        print("Loading type embedding map from database...")
        try:
            ml_model = MLModel.objects.get(model_type='embedding_map', is_active=True)
            _type_embedding_map = joblib.load(ml_model.file.path)
        except MLModel.DoesNotExist:
            raise ModelNotFoundError(
                "找不到啟用的 Embedding Map。請在 Django admin 中上傳並啟用 Embedding Map。"
            )
    
    if _embed_model is None:
        print("Loading Sentence Transformer model...")
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    
    return _model, _pca, _type_embedding_map, _embed_model



def clean_revit_type(text: str) -> str:
    """清理 Revit 類型名稱"""
    if pd.isna(text) or not text:
        return ""
    text = text.lower()
    text = text.replace("×", "x")
    text = re.sub(r"[^\w\u4e00-\u9fff\s\.x]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_embedding(text: str, embed_model, type_embedding_map) -> np.ndarray:
    """取得文字嵌入（含快取）"""
    if text in type_embedding_map:
        return type_embedding_map[text]
    
    emb = embed_model.encode(
        [text],
        normalize_embeddings=True
    )[0]
    type_embedding_map[text] = emb
    return emb


def records_to_dataframe(records):
    """將 records 轉換為 DataFrame"""
    df = pd.DataFrame(records)
    
    # 重命名欄位以符合 test.py 的格式
    df = df.rename(columns={
        'distance': '衝突距離',
        'item1_count': '項目1出現次數',
        'item1_system': '項目1系統',
        'item1_type': '項目1Revit類型名稱',
        'item2_count': '項目2出現次數',
        'item2_system': '項目2系統',
        'item2_type': '項目2Revit類型名稱',
        'status': '標註',
    })
    
    return df


def engineer_features(df, pca, embed_model, type_embedding_map):
    """
    特徵工程管道
    參考 test.py 的完整流程
    """
    # 1. 清理 Revit 類型名稱
    df["type1_clean"] = df["項目1Revit類型名稱"].apply(clean_revit_type)
    df["type2_clean"] = df["項目2Revit類型名稱"].apply(clean_revit_type)
    
    # 2. 生成嵌入
    emb1 = np.vstack(df["type1_clean"].apply(
        lambda x: get_embedding(x, embed_model, type_embedding_map)
    ).values)
    emb2 = np.vstack(df["type2_clean"].apply(
        lambda x: get_embedding(x, embed_model, type_embedding_map)
    ).values)
    
    # 3. 計算嵌入差值
    emb_diff = np.abs(emb1 - emb2)
    
    # 4. PCA 降維
    emb_diff_pca = pca.transform(emb_diff)
    
    # 填回 DataFrame
    for i in range(emb_diff_pca.shape[1]):
        df[f"embed_pca_{i}"] = emb_diff_pca[:, i]
    
    # 5. 距離特徵
    df["clash_distance_abs"] = df["衝突距離"].abs()
    df["is_overlap"] = (df["衝突距離"] < 0).astype(int)
    df["log_distance"] = np.log1p(df["clash_distance_abs"])
    
    # 6. 出現次數特徵
    df["comp1_count_log"] = np.log1p(df["項目1出現次數"])
    df["comp2_count_log"] = np.log1p(df["項目2出現次數"])
    df["count_diff"] = abs(df["項目1出現次數"] - df["項目2出現次數"])
    
    # 7. 系統編碼
    df["sys1_code"] = df["項目1系統"].map(SYS_MAP).fillna(-1).astype(int)
    df["sys2_code"] = df["項目2系統"].map(SYS_MAP).fillna(-1).astype(int)
    
    df["sys_pair"] = df.apply(
        lambda r: min(r.sys1_code, r.sys2_code) * 10 + max(r.sys1_code, r.sys2_code),
        axis=1
    )
    
    return df


def predict_clash_classification(records):
    """
    對碰撞記錄進行分類預測
    
    Args:
        records: list of dict，從 HTML 解析出的碰撞記錄
    
    Returns:
        list of dict: [{'label': 0 or 1, 'probability': float}, ...]
    """
    # 載入模型
    model, pca, type_embedding_map, embed_model = load_models()
    
    # 轉換為 DataFrame
    df = records_to_dataframe(records)
    
    # 特徵工程
    df = engineer_features(df, pca, embed_model, type_embedding_map)
    
    # 準備特徵欄位
    feature_cols = [
        "clash_distance_abs",
        "is_overlap",
        "log_distance",
        "comp1_count_log",
        "comp2_count_log",
        "count_diff",
        "sys1_code",
        "sys2_code",
        "sys_pair",
    ] + [f"embed_pca_{i}" for i in range(pca.n_components_)]
    
    X = df[feature_cols]
    
    # 預測機率
    pred_proba = model.predict_proba(X)[:, 1]
    
    # 應用閾值
    pred_labels = (pred_proba >= THRESHOLD).astype(int)
    
    # 組合結果
    predictions = [
        {
            'label': int(label),
            'probability': float(prob)
        }
        for label, prob in zip(pred_labels, pred_proba)
    ]
    
    return predictions
