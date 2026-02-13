from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class StandardRecord:
    source_type: str
    source_id: str
    name: str
    quantity: Decimal | None
    unit: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class NormalizedRecord:
    original: StandardRecord
    normalized_name: str
    normalized_unit: str
    normalized_quantity: Decimal | None


@dataclass(frozen=True)
class MatchResult:
    method: str
    left: NormalizedRecord
    right: NormalizedRecord
    score: float
    name_score: float
    unit_score: float
    quantity_score: float


@dataclass(frozen=True)
class MethodComparisonResult:
    method: str
    description: str
    matches: list[MatchResult]
    unmatched_left: list[NormalizedRecord]
    unmatched_right: list[NormalizedRecord]


@dataclass(frozen=True)
class ComparisonReport:
    left_records: list[StandardRecord]
    right_records: list[StandardRecord]
    normalized_left: list[NormalizedRecord]
    normalized_right: list[NormalizedRecord]
    methods: list[MethodComparisonResult]
