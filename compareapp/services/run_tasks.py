from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Lock
from typing import Any

from django.db import close_old_connections, transaction
from django.utils import timezone

from ..models import ComparisonMatch, ComparisonRun
from .keywords import list_active_normalized_keywords
from .pipeline import PipelineOptions, build_comparison_report_from_records
from .schemas import ComparisonReport, MatchResult, MethodComparisonResult, NormalizedRecord, StandardRecord
from .serialization import build_unique_name_baseline_records, deserialize_standard_records


_EXECUTOR: ThreadPoolExecutor | None = None
_EXECUTOR_LOCK = Lock()


def enqueue_comparison_run(run_id: int) -> None:
    executor = _get_executor()
    executor.submit(_execute_comparison_run, run_id)


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is not None:
        return _EXECUTOR

    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix='compare-run')
    return _EXECUTOR


def _execute_comparison_run(run_id: int) -> None:
    close_old_connections()
    try:
        run = ComparisonRun.objects.select_related('project').get(pk=run_id)
    except ComparisonRun.DoesNotExist:
        return

    if run.status not in {ComparisonRun.Status.PENDING, ComparisonRun.Status.RUNNING}:
        return

    ComparisonRun.objects.filter(pk=run_id).update(
        status=ComparisonRun.Status.RUNNING,
        started_at=timezone.now(),
        finished_at=None,
        error_message='',
        baseline_meta={'stage': 'preparing'},
    )

    try:
        run = ComparisonRun.objects.select_related('project').get(pk=run_id)
        project = run.project

        left_records_raw = deserialize_standard_records(project.budget_records)
        right_records_raw = deserialize_standard_records(project.quantity_records)

        left_records = build_unique_name_baseline_records(left_records_raw, chinese_only=True)
        right_records = build_unique_name_baseline_records(right_records_raw, chinese_only=True)
        if not right_records:
            right_records = build_unique_name_baseline_records(right_records_raw, chinese_only=False)

        pair_count = len(left_records) * len(right_records)
        baseline_meta = {
            'left_raw_count': len(left_records_raw),
            'left_baseline_count': len(left_records),
            'right_raw_count': len(right_records_raw),
            'right_baseline_count': len(right_records),
            'pair_count': pair_count,
            'stage': 'matching',
        }
        ComparisonRun.objects.filter(pk=run_id).update(
            baseline_meta=baseline_meta,
            updated_at=timezone.now(),
        )

        report = build_comparison_report_from_records(
            left_records=left_records,
            right_records=right_records,
            options=PipelineOptions(
                quantity_tolerance=run.quantity_tolerance,
                fuzzy_threshold=run.fuzzy_threshold,
                weighted_threshold=run.weighted_threshold,
                cross_encoder_threshold=run.cross_encoder_threshold,
                cross_encoder_total_threshold=run.cross_encoder_total_threshold,
                sentence_model_name=run.sentence_model_name,
                cross_encoder_model_name=run.cross_encoder_model_name,
                keyword_terms=list_active_normalized_keywords(limit=3000),
                keyword_boost=0.08,
            ),
        )

        report_payload = comparison_report_to_payload(report)
        baseline_meta['stage'] = 'persisting'
        ComparisonRun.objects.filter(pk=run_id).update(
            baseline_meta=baseline_meta,
            updated_at=timezone.now(),
        )
        match_rows = _build_match_rows(run_id, report_payload)

        with transaction.atomic():
            locked_run = ComparisonRun.objects.select_for_update().get(pk=run_id)
            locked_run.status = ComparisonRun.Status.COMPLETED
            locked_run.finished_at = timezone.now()
            locked_run.error_message = ''
            baseline_meta['stage'] = 'completed'
            locked_run.baseline_meta = baseline_meta
            locked_run.report_payload = report_payload
            locked_run.save(
                update_fields=[
                    'status',
                    'finished_at',
                    'error_message',
                    'baseline_meta',
                    'report_payload',
                    'updated_at',
                ]
            )
            locked_run.matches.all().delete()
            if match_rows:
                ComparisonMatch.objects.bulk_create(match_rows, batch_size=400)

    except Exception as exc:  # pragma: no cover - defensive fallback
        ComparisonRun.objects.filter(pk=run_id).update(
            status=ComparisonRun.Status.FAILED,
            finished_at=timezone.now(),
            error_message=_short_error(exc),
        )
    finally:
        close_old_connections()


def comparison_report_to_payload(report: ComparisonReport) -> dict[str, Any]:
    return {
        'left_records': [_standard_record_to_payload(item) for item in report.left_records],
        'right_records': [_standard_record_to_payload(item) for item in report.right_records],
        'normalized_left': [_normalized_record_to_payload(item) for item in report.normalized_left],
        'normalized_right': [_normalized_record_to_payload(item) for item in report.normalized_right],
        'methods': [_method_result_to_payload(item) for item in report.methods],
    }


def _method_result_to_payload(result: MethodComparisonResult) -> dict[str, Any]:
    return {
        'method': result.method,
        'description': result.description,
        'matches': [_match_to_payload(match) for match in result.matches],
        'unmatched_left': [_normalized_record_to_payload(item) for item in result.unmatched_left],
        'unmatched_right': [_normalized_record_to_payload(item) for item in result.unmatched_right],
    }


def _match_to_payload(match: MatchResult) -> dict[str, Any]:
    return {
        'method': match.method,
        'left': _normalized_record_to_payload(match.left),
        'right': _normalized_record_to_payload(match.right),
        'score': float(match.score),
        'name_score': float(match.name_score),
        'unit_score': float(match.unit_score),
        'quantity_score': float(match.quantity_score),
    }


def _normalized_record_to_payload(record: NormalizedRecord) -> dict[str, Any]:
    return {
        'original': _standard_record_to_payload(record.original),
        'normalized_name': record.normalized_name,
        'normalized_unit': record.normalized_unit,
        'normalized_quantity': _decimal_to_string(record.normalized_quantity),
    }


def _standard_record_to_payload(record: StandardRecord) -> dict[str, Any]:
    return {
        'source_type': record.source_type,
        'source_id': record.source_id,
        'name': record.name,
        'quantity': _decimal_to_string(record.quantity),
        'unit': record.unit,
        'raw_payload': _json_safe(record.raw_payload),
    }


def _decimal_to_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def _build_match_rows(run_id: int, report_payload: dict[str, Any]) -> list[ComparisonMatch]:
    methods = report_payload.get('methods')
    if not isinstance(methods, list):
        return []

    rows: list[ComparisonMatch] = []
    for method_payload in methods:
        if not isinstance(method_payload, dict):
            continue

        method = str(method_payload.get('method', '')).strip()
        matches = method_payload.get('matches')
        if not method or not isinstance(matches, list):
            continue

        for rank, match in enumerate(matches, start=1):
            if not isinstance(match, dict):
                continue

            left = match.get('left') if isinstance(match.get('left'), dict) else {}
            right = match.get('right') if isinstance(match.get('right'), dict) else {}
            left_original = (
                left.get('original') if isinstance(left.get('original'), dict) else {}
            )
            right_original = (
                right.get('original') if isinstance(right.get('original'), dict) else {}
            )

            rows.append(
                ComparisonMatch(
                    run_id=run_id,
                    method=method,
                    rank=rank,
                    left_source_id=str(left_original.get('source_id', '')).strip(),
                    right_source_id=str(right_original.get('source_id', '')).strip(),
                    left_name=str(left_original.get('name', '')).strip(),
                    right_name=str(right_original.get('name', '')).strip(),
                    score=_to_float(match.get('score')),
                    name_score=_to_float(match.get('name_score')),
                    unit_score=_to_float(match.get('unit_score')),
                    quantity_score=_to_float(match.get('quantity_score')),
                )
            )

    return rows


def _to_float(value: object) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _short_error(exc: Exception, max_length: int = 2000) -> str:
    message = str(exc).replace('\n', ' ').strip()
    if not message:
        return f'{exc.__class__.__name__}'
    if len(message) <= max_length:
        return message
    return message[: max_length - 3] + '...'
