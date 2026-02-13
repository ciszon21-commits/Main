from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .matcher import MatchOptions, compare_all_methods
from .normalization import normalize_record
from .parsers import parse_budget_xml, parse_quantity_workbook
from .schemas import ComparisonReport, StandardRecord


@dataclass(frozen=True)
class PipelineOptions:
    quantity_tolerance: Decimal
    fuzzy_threshold: float
    weighted_threshold: float
    semantic_threshold: float | None = None
    sentence_model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
    cross_encoder_threshold: float = 0.85
    cross_encoder_total_threshold: float | None = None
    cross_encoder_model_name: str = 'BAAI/bge-reranker-v2-m3'
    keyword_terms: tuple[str, ...] = ()
    keyword_boost: float = 0.08


def build_comparison_report(
    budget_file_name: str,
    budget_payload: bytes,
    quantity_file_name: str,
    quantity_payload: bytes,
    options: PipelineOptions,
) -> ComparisonReport:
    left_records = parse_budget_xml(budget_file_name, budget_payload)
    right_records = parse_quantity_workbook(quantity_file_name, quantity_payload)
    return build_comparison_report_from_records(left_records, right_records, options)


def build_comparison_report_from_records(
    left_records: list[StandardRecord],
    right_records: list[StandardRecord],
    options: PipelineOptions,
) -> ComparisonReport:

    normalized_left = [normalize_record(record) for record in left_records]
    normalized_right = [normalize_record(record) for record in right_records]

    methods = compare_all_methods(
        normalized_left,
        normalized_right,
        MatchOptions(
            quantity_tolerance=options.quantity_tolerance,
            fuzzy_threshold=options.fuzzy_threshold,
            weighted_threshold=options.weighted_threshold,
            semantic_threshold=options.semantic_threshold,
            sentence_model_name=options.sentence_model_name,
            cross_encoder_threshold=options.cross_encoder_threshold,
            cross_encoder_total_threshold=options.cross_encoder_total_threshold,
            cross_encoder_model_name=options.cross_encoder_model_name,
            keyword_terms=options.keyword_terms,
            keyword_boost=options.keyword_boost,
        ),
    )

    return ComparisonReport(
        left_records=left_records,
        right_records=right_records,
        normalized_left=normalized_left,
        normalized_right=normalized_right,
        methods=methods,
    )
