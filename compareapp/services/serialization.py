from __future__ import annotations

import re
from decimal import Decimal

from .normalization import normalize_name, normalize_unit, parse_decimal
from .schemas import StandardRecord

CJK_PATTERN = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')


def contains_cjk_text(value: str) -> bool:
    if not value:
        return False
    return CJK_PATTERN.search(value) is not None


def standard_record_to_dict(record: StandardRecord) -> dict[str, object]:
    return {
        'source_type': record.source_type,
        'source_id': record.source_id,
        'name': record.name,
        'quantity': str(record.quantity) if record.quantity is not None else None,
        'unit': record.unit,
        'raw_payload': record.raw_payload,
    }


def standard_record_from_dict(data: dict[str, object]) -> StandardRecord:
    raw_quantity = data.get('quantity')
    quantity = parse_decimal(raw_quantity)
    if isinstance(raw_quantity, Decimal):
        quantity = raw_quantity

    return StandardRecord(
        source_type=str(data.get('source_type', '')),
        source_id=str(data.get('source_id', '')),
        name=str(data.get('name', '')).strip(),
        quantity=quantity,
        unit=str(data.get('unit', '')).strip(),
        raw_payload=data.get('raw_payload', {}) if isinstance(data.get('raw_payload'), dict) else {},
    )


def serialize_standard_records(records: list[StandardRecord]) -> list[dict[str, object]]:
    return [standard_record_to_dict(record) for record in records]


def deserialize_standard_records(payload: list[dict[str, object]]) -> list[StandardRecord]:
    return [standard_record_from_dict(item) for item in payload]


def extract_budget_terms(
    records: list[StandardRecord],
    chinese_only: bool = False,
) -> list[dict[str, str]]:
    seen: set[str] = set()
    terms: list[dict[str, str]] = []
    for record in records:
        if chinese_only and not contains_cjk_text(record.name):
            continue
        compact = normalize_name(record.name)
        if not compact or compact in seen:
            continue
        seen.add(compact)
        terms.append(
            {
                'name': record.name,
                'normalized_name': compact,
            }
        )
    return terms


def build_unique_name_baseline_records(
    records: list[StandardRecord],
    chinese_only: bool = True,
) -> list[StandardRecord]:
    grouped: dict[str, dict[str, object]] = {}

    for record in records:
        if chinese_only and not contains_cjk_text(record.name):
            continue

        normalized_name = normalize_name(record.name)
        if not normalized_name:
            continue

        quantity = parse_decimal(record.quantity)
        normalized_unit = normalize_unit(record.unit)
        existing = grouped.get(normalized_name)

        if existing is None:
            grouped[normalized_name] = {
                'record': record,
                'source_ids': [record.source_id],
                'quantity': quantity,
                'unit': record.unit,
                'unit_normalized': normalized_unit,
                'mixed_unit': False,
            }
            continue

        existing['source_ids'].append(record.source_id)
        existing_qty = existing['quantity']
        if quantity is not None:
            if existing_qty is None:
                existing['quantity'] = quantity
            else:
                existing['quantity'] = existing_qty + quantity

        existing_unit_norm = existing['unit_normalized']
        if not existing['unit'] and record.unit:
            existing['unit'] = record.unit
            existing['unit_normalized'] = normalized_unit
        elif normalized_unit and existing_unit_norm and normalized_unit != existing_unit_norm:
            existing['mixed_unit'] = True

    baseline: list[StandardRecord] = []
    for normalized_name, item in grouped.items():
        seed = item['record']
        source_ids = item['source_ids']
        source_id = source_ids[0] if len(source_ids) == 1 else f"{source_ids[0]}(+{len(source_ids)-1})"
        baseline.append(
            StandardRecord(
                source_type=seed.source_type,
                source_id=source_id,
                name=seed.name,
                quantity=item['quantity'],
                unit=item['unit'] or '',
                raw_payload={
                    'normalized_name': normalized_name,
                    'source_ids': source_ids,
                    'aggregated_count': len(source_ids),
                    'quantity_strategy': 'sum',
                    'mixed_unit': bool(item['mixed_unit']),
                },
            )
        )

    return baseline
