"""
matching.py — 中介資料比對服務

提供 IntermediateItem 的匯入、正規化、精準比對與模糊比對功能。
複用 processing.py 的正規化與 token 化邏輯。
"""

import re
import unicodedata
from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import QuerySet

from .models import IntermediateItem, MatchResult, Project, ProjectFile

try:
    from rapidfuzz import fuzz as rf_fuzz
    from rapidfuzz import process as rf_process
except ImportError:  # pragma: no cover
    rf_fuzz = None
    rf_process = None

# ---------------------------------------------------------------------------
# 全半型轉換表（ASCII 可見字元範圍 0x21–0x7E → 全形 0xFF01–0xFF5E）
# ---------------------------------------------------------------------------
_FULLWIDTH_TO_HALFWIDTH = {}
for _i in range(0xFF01, 0xFF5F):
    _FULLWIDTH_TO_HALFWIDTH[chr(_i)] = chr(_i - 0xFEE0)
_FULLWIDTH_TO_HALFWIDTH["　"] = " "  # 全形空格
_FW_TABLE = str.maketrans(_FULLWIDTH_TO_HALFWIDTH)


# =========================================================================
# 正規化工具
# =========================================================================

def standardize_name(raw_name: str) -> str:
    """
    正規化名稱：
    1. NFKC Unicode 正規化
    2. 全形→半形轉換
    3. 去除前後空白 & 壓縮連續空格
    4. 移除零寬字元
    """
    if not raw_name:
        return ""
    text = unicodedata.normalize("NFKC", raw_name)
    text = text.translate(_FW_TABLE)
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)  # 零寬字元
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _tokenize(text: str) -> list[str]:
    """將正規化後名稱切成 token（中文 bigram + 英文字詞）。"""
    if not text:
        return []
    tokens: list[str] = []
    # 中文連續字元 (2+)
    tokens.extend(re.findall(r"[\u4e00-\u9fff]{2,}", text))
    # 英數字詞 (2+)
    tokens.extend(re.findall(r"[A-Za-z][A-Za-z0-9_/\\-]{1,}", text))
    normalized: list[str] = []
    for token in tokens:
        if token.isascii():
            token = token.lower()
        if len(token) < 2 or token.isdigit():
            continue
        normalized.append(token)
    return normalized


def generate_uid(reference: str, file_id: int | str, row_index: int | str) -> str:
    """產生 IntermediateItem 的唯一識別碼。"""
    return f"{reference}_{file_id}_{row_index}"


# =========================================================================
# 批次匯入
# =========================================================================

def bulk_import_from_budget(
    project: Project,
    budget_rows: list[dict[str, Any]],
    source_file: ProjectFile | None = None,
) -> list[IntermediateItem]:
    """從預算書解析結果批次建立 IntermediateItem。"""
    file_id = source_file.pk if source_file else 0
    items: list[IntermediateItem] = []
    for idx, row in enumerate(budget_rows):
        raw_name = row.get("description") or ""
        uid = generate_uid("budget", file_id, idx)
        quantity = row.get("quantity")
        price = row.get("price")
        std_name = standardize_name(raw_name)
        tokens = _tokenize(std_name)
        items.append(
            IntermediateItem(
                uid=uid,
                project=project,
                source_file=source_file,
                item_name=raw_name[:500],
                standard_name=std_name[:500],
                quantity=Decimal(str(quantity)) if quantity is not None else None,
                unit=(row.get("unit") or "")[:50],
                price=Decimal(str(price)) if price is not None else None,
                reference=IntermediateItem.REFERENCE_BUDGET,
                item_no=(row.get("item_no") or "")[:100],
                extra={
                    "ref_code": row.get("ref_code", ""),
                    "item_kind": row.get("item_kind", ""),
                    "amount": row.get("amount"),
                },
                name_tokens=tokens,
            )
        )
    with transaction.atomic():
        # 先清除同專案同來源同檔案的舊資料
        qs = IntermediateItem.objects.filter(
            project=project,
            reference=IntermediateItem.REFERENCE_BUDGET,
        )
        if source_file:
            qs = qs.filter(source_file=source_file)
        qs.delete()
        IntermediateItem.objects.bulk_create(items, batch_size=500)
    return items


def bulk_import_from_quantity(
    project: Project,
    quantity_rows: list[dict[str, Any]],
    source_file: ProjectFile | None = None,
) -> list[IntermediateItem]:
    """從數量計算書解析結果批次建立 IntermediateItem。"""
    file_id = source_file.pk if source_file else 0
    items: list[IntermediateItem] = []
    for idx, row in enumerate(quantity_rows):
        raw_name = row.get("description") or ""
        uid = generate_uid("quantity", file_id, idx)
        quantity = row.get("quantity")
        std_name = standardize_name(raw_name)
        tokens = _tokenize(std_name)
        items.append(
            IntermediateItem(
                uid=uid,
                project=project,
                source_file=source_file,
                item_name=raw_name[:500],
                standard_name=std_name[:500],
                quantity=Decimal(str(quantity)) if quantity is not None else None,
                unit=(row.get("unit") or "")[:50],
                price=None,
                reference=IntermediateItem.REFERENCE_QUANTITY,
                item_no=(row.get("item_no") or "")[:100],
                extra={
                    "sheet": row.get("sheet", ""),
                    "row": row.get("row"),
                    "category": row.get("category", ""),
                },
                name_tokens=tokens,
            )
        )
    with transaction.atomic():
        qs = IntermediateItem.objects.filter(
            project=project,
            reference=IntermediateItem.REFERENCE_QUANTITY,
        )
        if source_file:
            qs = qs.filter(source_file=source_file)
        qs.delete()
        IntermediateItem.objects.bulk_create(items, batch_size=500)
    return items


# =========================================================================
# 逐欄比對
# =========================================================================

def compare_items(item_a: IntermediateItem, item_b: IntermediateItem) -> dict[str, Any]:
    """
    比較兩個 IntermediateItem 的名稱、單位、數量。
    回傳一致性報告 dict。
    """
    # 名稱比對
    name_consistent = item_a.standard_name == item_b.standard_name
    name_score = 100 if name_consistent else _compute_name_score(item_a, item_b)

    # 單位比對
    unit_a = standardize_name(item_a.unit)
    unit_b = standardize_name(item_b.unit)
    unit_consistent = unit_a == unit_b if (unit_a and unit_b) else (unit_a == unit_b)

    # 數量比對
    qty_consistent = False
    qty_delta = None
    if item_a.quantity is not None and item_b.quantity is not None:
        qty_delta = float(item_a.quantity - item_b.quantity)
        qty_consistent = abs(qty_delta) < 0.0001
    elif item_a.quantity is None and item_b.quantity is None:
        qty_consistent = True

    return {
        "is_name_consistent": name_consistent,
        "is_unit_consistent": unit_consistent,
        "is_qty_consistent": qty_consistent,
        "name_score": name_score,
        "qty_delta": qty_delta,
        "unit_a": unit_a,
        "unit_b": unit_b,
    }


def _compute_name_score(item_a: IntermediateItem, item_b: IntermediateItem) -> int:
    """計算兩個 item 名稱的相似度分數 (0-100)。"""
    if rf_fuzz:
        return int(rf_fuzz.token_set_ratio(item_a.standard_name, item_b.standard_name))
    # fallback: token overlap
    tokens_a = set(item_a.name_tokens or [])
    tokens_b = set(item_b.name_tokens or [])
    if not tokens_a or not tokens_b:
        return 0
    common = tokens_a & tokens_b
    overlap = len(common) / max(1, min(len(tokens_a), len(tokens_b)))
    return int(round(overlap * 100))


# =========================================================================
# 精準比對
# =========================================================================

def exact_match(
    project: Project,
    ref_a: str = IntermediateItem.REFERENCE_BUDGET,
    ref_b: str = IntermediateItem.REFERENCE_QUANTITY,
    run=None,
) -> list[MatchResult]:
    """
    以 standard_name 完全匹配進行精準比對。
    回傳建立的 MatchResult 清單。
    """
    items_a = list(
        IntermediateItem.objects.filter(project=project, reference=ref_a)
        .values_list("id", "standard_name", named=True)
    )
    items_b = list(
        IntermediateItem.objects.filter(project=project, reference=ref_b)
        .values_list("id", "standard_name", named=True)
    )

    # 建立 B 端的 standard_name → id 索引
    b_index: dict[str, list[int]] = defaultdict(list)
    for item in items_b:
        if item.standard_name:
            b_index[item.standard_name].append(item.id)

    used_b: set[int] = set()
    matched_pairs: list[tuple[int, int]] = []

    for item in items_a:
        if not item.standard_name or item.standard_name not in b_index:
            continue
        candidates = b_index[item.standard_name]
        # 優先選未使用的
        chosen = None
        for b_id in candidates:
            if b_id not in used_b:
                chosen = b_id
                break
        if chosen is None:
            continue
        used_b.add(chosen)
        matched_pairs.append((item.id, chosen))

    # 批次載入完整 item 進行逐欄比對
    all_ids = {a for a, _ in matched_pairs} | {b for _, b in matched_pairs}
    items_map = {
        item.id: item
        for item in IntermediateItem.objects.filter(id__in=all_ids)
    }

    results: list[MatchResult] = []
    for a_id, b_id in matched_pairs:
        ia, ib = items_map[a_id], items_map[b_id]
        comparison = compare_items(ia, ib)
        results.append(
            MatchResult(
                project=project,
                run=run,
                item_a=ia,
                item_b=ib,
                match_method=MatchResult.METHOD_EXACT,
                score=100,
                is_name_consistent=comparison["is_name_consistent"],
                is_unit_consistent=comparison["is_unit_consistent"],
                is_qty_consistent=comparison["is_qty_consistent"],
                detail=comparison,
            )
        )

    if results:
        with transaction.atomic():
            MatchResult.objects.bulk_create(results, batch_size=500)
    return results


# =========================================================================
# 模糊比對
# =========================================================================

def fuzzy_match(
    project: Project,
    ref_a: str = IntermediateItem.REFERENCE_BUDGET,
    ref_b: str = IntermediateItem.REFERENCE_QUANTITY,
    threshold: int = 85,
    run=None,
    exclude_exact: bool = True,
) -> list[MatchResult]:
    """
    對未精準匹配的項目執行模糊比對。
    使用 token overlap + rapidfuzz 計算相似度。

    Args:
        project: 目標專案
        ref_a / ref_b: 比對的兩個來源
        threshold: 匹配門檻 (0-100)
        run: 對應的 ComparisonRun
        exclude_exact: 是否排除已有精準匹配的項目
    """
    items_a = list(
        IntermediateItem.objects.filter(project=project, reference=ref_a)
    )
    items_b = list(
        IntermediateItem.objects.filter(project=project, reference=ref_b)
    )

    # 收集已精準匹配的 ID
    already_matched_a: set[int] = set()
    already_matched_b: set[int] = set()
    if exclude_exact:
        existing = MatchResult.objects.filter(
            project=project,
            match_method=MatchResult.METHOD_EXACT,
        ).values_list("item_a_id", "item_b_id")
        for a_id, b_id in existing:
            already_matched_a.add(a_id)
            already_matched_b.add(b_id)

    unmatched_a = [i for i in items_a if i.id not in already_matched_a]
    unmatched_b = [i for i in items_b if i.id not in already_matched_b]

    if not unmatched_a or not unmatched_b:
        return []

    # 建立 B 端的搜尋索引
    b_norms = [item.standard_name for item in unmatched_b]
    b_token_index: dict[str, set[int]] = defaultdict(set)
    for idx, item in enumerate(unmatched_b):
        for token in (item.name_tokens or []):
            b_token_index[token].add(idx)

    used_b: set[int] = set()
    results: list[MatchResult] = []

    for item_a in unmatched_a:
        best_idx, best_score, best_method = _find_best_fuzzy(
            item_a, unmatched_b, b_norms, b_token_index, used_b, threshold
        )
        if best_idx is None:
            continue

        used_b.add(best_idx)
        item_b = unmatched_b[best_idx]
        comparison = compare_items(item_a, item_b)
        comparison["name_score"] = best_score

        results.append(
            MatchResult(
                project=project,
                run=run,
                item_a=item_a,
                item_b=item_b,
                match_method=best_method,
                score=best_score,
                is_name_consistent=comparison["is_name_consistent"],
                is_unit_consistent=comparison["is_unit_consistent"],
                is_qty_consistent=comparison["is_qty_consistent"],
                detail=comparison,
            )
        )

    if results:
        with transaction.atomic():
            MatchResult.objects.bulk_create(results, batch_size=500)
    return results


def _find_best_fuzzy(
    item_a: IntermediateItem,
    candidates_b: list[IntermediateItem],
    b_norms: list[str],
    b_token_index: dict[str, set[int]],
    used_b: set[int],
    threshold: int,
) -> tuple[int | None, int, str]:
    """
    為 item_a 在 candidates_b 中找到最佳模糊匹配。
    回傳 (最佳 index, 分數, 匹配方式)。
    """
    tokens_a = set(item_a.name_tokens or [])
    if not tokens_a:
        return None, 0, ""

    # 第一步：用 item_no 匹配
    if item_a.item_no:
        for idx, item_b in enumerate(candidates_b):
            if idx in used_b:
                continue
            if item_b.item_no and item_a.item_no == item_b.item_no:
                score = _score_pair(item_a.standard_name, item_b.standard_name)
                return idx, max(score, 95), MatchResult.METHOD_ITEM_NO

    # 第二步：用 token overlap 篩選候選
    candidate_indices: set[int] = set()
    for token in tokens_a:
        candidate_indices.update(b_token_index.get(token, set()))
    candidate_indices -= used_b

    if not candidate_indices:
        # 第三步：全域 rapidfuzz fallback
        if rf_process and rf_fuzz:
            available = [(idx, n) for idx, n in enumerate(b_norms) if idx not in used_b]
            if available:
                avail_norms = [n for _, n in available]
                avail_indices = [idx for idx, _ in available]
                best = rf_process.extractOne(
                    item_a.standard_name, avail_norms, scorer=rf_fuzz.token_set_ratio
                )
                if best and int(best[1]) >= threshold:
                    return avail_indices[best[2]], int(best[1]), MatchResult.METHOD_FUZZY
        return None, 0, ""

    # 對候選進行評分
    best_idx = None
    best_score = -1
    for idx in candidate_indices:
        score = _score_pair(item_a.standard_name, candidates_b[idx].standard_name)
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is not None and best_score >= threshold:
        return best_idx, best_score, MatchResult.METHOD_TOKEN

    return None, 0, ""


def _score_pair(name_a: str, name_b: str) -> int:
    """計算兩個名稱的相似度分數。"""
    if rf_fuzz:
        return int(rf_fuzz.token_set_ratio(name_a, name_b))
    # fallback: simple token overlap
    tokens_a = set(_tokenize(name_a))
    tokens_b = set(_tokenize(name_b))
    if not tokens_a or not tokens_b:
        return 0
    common = tokens_a & tokens_b
    overlap = len(common) / max(1, min(len(tokens_a), len(tokens_b)))
    return int(round(overlap * 100))


# =========================================================================
# 整合比對入口
# =========================================================================

def run_full_match(
    project: Project,
    run=None,
    fuzzy_threshold: int = 85,
) -> dict[str, Any]:
    """
    執行完整比對流程：精準比對 → 模糊比對。
    回傳統計摘要。
    """
    # 清除舊比對結果
    MatchResult.objects.filter(project=project, run=run).delete()

    exact_results = exact_match(project, run=run)
    fuzzy_results = fuzzy_match(
        project, threshold=fuzzy_threshold, run=run, exclude_exact=True
    )

    total_a = IntermediateItem.objects.filter(
        project=project, reference=IntermediateItem.REFERENCE_BUDGET
    ).count()
    total_b = IntermediateItem.objects.filter(
        project=project, reference=IntermediateItem.REFERENCE_QUANTITY
    ).count()

    return {
        "total_budget": total_a,
        "total_quantity": total_b,
        "exact_matched": len(exact_results),
        "fuzzy_matched": len(fuzzy_results),
        "total_matched": len(exact_results) + len(fuzzy_results),
        "unmatched_budget": total_a - len(exact_results) - len(fuzzy_results),
        "unmatched_quantity": total_b - len(exact_results) - len(fuzzy_results),
    }
