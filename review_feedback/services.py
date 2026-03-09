"""
JSON 比對結果解析服務

JSON 格式為三層巢狀 dict:
- 第一層 key: 減碳策略 (含策略名稱與定義)
- 第二層 key: 文字摘錄 (excerpt)
- 第三層 value: 比對結果欄位 (source_page, reasoning, is_match, ...)
"""
import json
from .models import ComparisonFile, ComparisonEntry


def parse_comparison_json(comparison_file: ComparisonFile) -> int:
    """
    解析上傳的 JSON 檔案並建立 ComparisonEntry records。
    回傳成功建立的 entry 數量。
    """
    comparison_file.file.open("rb")
    try:
        raw = comparison_file.file.read()
        data = json.loads(raw.decode("utf-8"))
    finally:
        comparison_file.file.close()

    entries_created = 0

    # 第一層: 減碳策略
    for strategy_key, excerpts in data.items():
        if not isinstance(excerpts, dict):
            continue

        strategy_name = strategy_key.strip()

        # 第二層: 文字摘錄
        for excerpt_text, fields in excerpts.items():
            if not isinstance(fields, dict):
                continue

            # 取得 char_interval
            char_interval = fields.get("char_interval", {})
            start_pos = char_interval.get("start_pos") if isinstance(char_interval, dict) else None
            end_pos = char_interval.get("end_pos") if isinstance(char_interval, dict) else None

            ComparisonEntry.objects.create(
                comparison_file=comparison_file,
                strategy_name=strategy_name,
                excerpt_text=excerpt_text.strip(),
                source_page=str(fields.get("source_page", "")),
                reasoning=fields.get("reasoning", ""),
                is_match=bool(fields.get("is_match", False)),
                arbitration_status=fields.get("arbitration_status", ""),
                arbitration_note=fields.get("arbitration_note"),
                final_decision_class=fields.get("final_decision_class", ""),
                char_start_pos=start_pos,
                char_end_pos=end_pos,
            )
            entries_created += 1

    return entries_created
