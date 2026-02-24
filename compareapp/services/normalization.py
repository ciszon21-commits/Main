from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

from .schemas import NormalizedRecord, StandardRecord


NON_ALNUM_PATTERN = re.compile(r'[\W_]+', re.UNICODE)
NUMBER_PATTERN = re.compile(r'[-+]?\d+(?:\.\d+)?')

UNIT_SYNONYMS = {
    'm': 'm',
    'meter': 'm',
    'metre': 'm',
    '公尺': 'm',
    '米': 'm',
    'm2': 'm2',
    '㎡': 'm2',
    'm^2': 'm2',
    '平方公尺': 'm2',
    '平方公尺m2': 'm2',
    'm3': 'm3',
    'm^3': 'm3',
    '立方公尺': 'm3',
    'kg': 'kg',
    '公斤': 'kg',
    't': 't',
    'ton': 't',
    '噸': 't',
    'pc': 'pc',
    'pcs': 'pc',
    'ea': 'pc',
    '個': 'pc',
    '支': 'pc',
    '式': 'set',
    'set': 'set',
}


def normalize_text(value: str) -> str:
    if value is None:
        return ''
    normalized = unicodedata.normalize('NFKC', str(value)).strip().lower()
    return normalized


def normalize_name(value: str) -> str:
    normalized = normalize_text(value)
    return NON_ALNUM_PATTERN.sub('', normalized)


def normalize_unit(value: str) -> str:
    normalized = normalize_text(value)
    compact = normalized.replace(' ', '')
    return UNIT_SYNONYMS.get(compact, compact)


def parse_decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = normalize_text(str(value)).replace(',', '')
    if not text:
        return None

    match = NUMBER_PATTERN.search(text)
    if not match:
        return None

    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def normalize_record(record: StandardRecord) -> NormalizedRecord:
    return NormalizedRecord(
        original=record,
        normalized_name=normalize_name(record.name),
        normalized_unit=normalize_unit(record.unit),
        normalized_quantity=parse_decimal(record.quantity),
    )
