"""
業務邏輯服務模組
整合 HTML 解析、CSV 轉換和分類模型預測
"""
import csv
import re
import os
from collections import Counter
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from io import StringIO
from .models import ClassificationResult


SYSTEM_CODES = ["DR", "SW", "WW", "PW", "RW", "IE", "UT"]


def extract_system_code(filename: str) -> str:
    """
    從檔案名稱提取系統代碼
    例如: DN-D3-DR-00000-0A.rvt -> DR
    """
    for code in SYSTEM_CODES:
        if f"-{code}-" in filename:
            return code
    return ""


def clean_text(cell):
    """清理 HTML cell 中的文字"""
    return " ".join(cell.get_text(strip=True).split())


def parse_html_to_records(html_file):
    """
    解析 HTML 檔案為 records
    參考 html_to_csv.py 的邏輯
    """
    # 讀取 HTML 內容
    html_content = html_file.read()
    if isinstance(html_content, bytes):
        html_content = html_content.decode('utf-8')
    
    soup = BeautifulSoup(html_content, "lxml")
    
    records = []
    item_id_counter = Counter()
    
    # 只處理 mainTable
    for table in soup.select("table.mainTable"):
        rows = table.select("tr.contentRow")
        
        for row in rows:
            tds = row.find_all("td")
            
            if len(tds) < 25:
                continue
            
            distance = float(clean_text(tds[3]))
            
            status_text = clean_text(tds[2])
            status = {
                "已解決": 0,
                "作用中": 1,
                "新": 2,
            }.get(status_text, 1)
            
            # --- 項目 1 ---
            item1_id_match = re.search(r"\d+", clean_text(tds[7]))
            if not item1_id_match:
                continue
            item1_id = item1_id_match.group()
            item1_file = clean_text(tds[10])
            item1_category = clean_text(tds[13])
            item1_family = clean_text(tds[15])
            item1_type_name = item1_category + "-" + item1_family
            item1_system = extract_system_code(item1_file)
            
            # --- 項目 2 ---
            item2_id_match = re.search(r"\d+", clean_text(tds[16]))
            if not item2_id_match:
                continue
            item2_id = item2_id_match.group()
            item2_file = clean_text(tds[19])
            item2_category = clean_text(tds[22])
            item2_family = clean_text(tds[24])
            item2_type_name = item2_category + "-" + item2_family
            item2_system = extract_system_code(item2_file)
            
            item_id_counter[item1_id] += 1
            item_id_counter[item2_id] += 1
            
            records.append({
                "distance": distance,
                "item1_id": item1_id,
                "item1_system": item1_system,
                "item1_type": item1_type_name,
                "item2_id": item2_id,
                "item2_system": item2_system,
                "item2_type": item2_type_name,
                "status": status,
            })
    
    # 補出現次數
    for r in records:
        r["item1_count"] = item_id_counter[r["item1_id"]]
        r["item2_count"] = item_id_counter[r["item2_id"]]
    
    return records


def records_to_csv_content(records):
    """
    將 records 轉換為 CSV 內容
    """
    output = StringIO()
    headers = [
        "衝突距離",
        "項目1出現次數",
        "項目1系統",
        "項目1Revit類型名稱",
        "項目2出現次數",
        "項目2系統",
        "項目2Revit類型名稱",
        "標註",
    ]
    
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for r in records:
        writer.writerow([
            r["distance"],
            r["item1_count"],
            r["item1_system"],
            r["item1_type"],
            r["item2_count"],
            r["item2_system"],
            r["item2_type"],
            r["status"],
        ])
    
    return output.getvalue()


def process_clash_report(clash_report):
    """
    處理碰撞報告的完整流程：
    1. 解析 HTML
    2. 生成 CSV
    3. 進行分類預測
    4. 儲存結果
    
    返回: (records, predictions) tuple
    """
    from .ml_utils import predict_clash_classification
    
    # 1. 解析 HTML
    clash_report.html_file.seek(0)
    records = parse_html_to_records(clash_report.html_file)
    
    if not records:
        raise ValueError("無法從 HTML 中解析出碰撞記錄")
    
    # 2. 生成並儲存 CSV
    csv_content = records_to_csv_content(records)
    csv_filename = f"{clash_report.title}.csv"
    clash_report.csv_file.save(
        csv_filename,
        ContentFile(csv_content.encode('utf-8-sig')),
        save=True
    )
    
    # 3. 進行分類預測
    predictions = predict_clash_classification(records)
    
    # 4. 儲存分類結果到資料庫
    save_classification_results(clash_report, records, predictions)
    
    return records, predictions


def save_classification_results(clash_report, records, predictions):
    """
    儲存分類結果到資料庫
    """
    classification_objects = []
    
    for idx, (record, pred) in enumerate(zip(records, predictions)):
        classification_objects.append(
            ClassificationResult(
                report=clash_report,
                row_index=idx,
                distance=record['distance'],
                item1_id=record['item1_id'],
                item1_system=record['item1_system'],
                item1_type=record['item1_type'],
                item1_count=record['item1_count'],
                item2_id=record['item2_id'],
                item2_system=record['item2_system'],
                item2_type=record['item2_type'],
                item2_count=record['item2_count'],
                status=record['status'],
                predicted_class=pred['label'],
                confidence=pred['probability']
            )
        )
    
    # 批量創建
    ClassificationResult.objects.bulk_create(classification_objects)
