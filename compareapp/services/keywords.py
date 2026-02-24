from __future__ import annotations

import re
from collections import Counter

from django.db import transaction

from ..models import CompareProject, GlobalKeyword
from .normalization import normalize_name
from .serialization import deserialize_standard_records

TOKEN_PATTERN = re.compile(r'[\u3400-\u9fff]{2,}|[A-Za-z][A-Za-z0-9#\-\+]{1,}')
STOPWORDS = {
    '工程',
    '施工',
    '工作',
    '項目',
    '項次',
    '數量',
    '單位',
    '費用',
    '材料',
    '安裝',
    '製作',
}


def normalize_keyword_term(term: str) -> tuple[str, str] | None:
    clean_term = str(term or '').strip()
    if not clean_term:
        return None

    normalized = normalize_name(clean_term)
    if not normalized or len(normalized) < 2 or normalized.isdigit():
        return None

    return clean_term[:120], normalized[:120]


def upsert_global_keyword(
    term: str,
    source: str = GlobalKeyword.Source.MANUAL,
) -> tuple[GlobalKeyword | None, bool]:
    normalized_pair = normalize_keyword_term(term)
    if normalized_pair is None:
        return None, False

    display_term, normalized_term = normalized_pair
    source_value = source if source in GlobalKeyword.Source.values else GlobalKeyword.Source.MANUAL

    with transaction.atomic():
        keyword = (
            GlobalKeyword.objects.select_for_update()
            .filter(normalized_term=normalized_term)
            .first()
        )
        if keyword is None:
            created = GlobalKeyword.objects.create(
                term=display_term,
                normalized_term=normalized_term,
                source=source_value,
                selected_count=1,
                is_active=True,
            )
            return created, True

        update_fields: list[str] = ['selected_count', 'is_active', 'updated_at']
        keyword.selected_count += 1
        keyword.is_active = True

        if not keyword.term.strip() or len(display_term) < len(keyword.term):
            keyword.term = display_term
            update_fields.append('term')

        keyword.save(update_fields=update_fields)
        return keyword, False


def build_keyword_panel_context(
    project: CompareProject,
    stage: str = 'all',
    suggestion_limit: int = 24,
    library_limit: int = 60,
) -> dict[str, object]:
    global_keywords = list_global_keywords(limit=library_limit)
    existing_terms = set(
        GlobalKeyword.objects.filter(is_active=True).values_list('normalized_term', flat=True)
    )
    recommendations = extract_keyword_candidates_for_project(
        project=project,
        stage=stage,
        existing_terms=existing_terms,
        limit=suggestion_limit,
    )
    return {
        'keyword_global_list': global_keywords,
        'keyword_recommendations': recommendations,
        'keyword_recommendation_count': len(recommendations),
    }


def list_global_keywords(limit: int = 60) -> list[dict[str, object]]:
    safe_limit = max(1, int(limit))
    queryset = GlobalKeyword.objects.filter(is_active=True).order_by('-selected_count', 'term')[:safe_limit]
    return [
        {
            'id': item.id,
            'term': item.term,
            'normalized_term': item.normalized_term,
            'selected_count': item.selected_count,
            'source': item.source,
        }
        for item in queryset
    ]


def list_active_normalized_keywords(limit: int = 2000) -> tuple[str, ...]:
    safe_limit = max(1, int(limit))
    values = (
        GlobalKeyword.objects.filter(is_active=True)
        .order_by('-selected_count', 'normalized_term')
        .values_list('normalized_term', flat=True)[:safe_limit]
    )
    return tuple(values)


def extract_keyword_candidates_for_project(
    project: CompareProject,
    stage: str = 'all',
    existing_terms: set[str] | None = None,
    limit: int = 24,
) -> list[dict[str, object]]:
    records = _records_for_stage(project, stage)
    return extract_keyword_candidates_from_records(records, existing_terms=existing_terms, limit=limit)


def extract_keyword_candidates_from_records(
    records,
    existing_terms: set[str] | None = None,
    limit: int = 24,
) -> list[dict[str, object]]:
    if not records:
        return []

    existing = existing_terms if existing_terms is not None else set()
    token_counter: Counter[str] = Counter()
    display_tokens: dict[str, str] = {}

    for record in records:
        seen_in_record: set[str] = set()
        raw_name = str(getattr(record, 'name', '') or '')
        for token in _tokenize_name(raw_name):
            normalized_pair = normalize_keyword_term(token)
            if normalized_pair is None:
                continue
            display_term, normalized_term = normalized_pair
            if normalized_term in STOPWORDS:
                continue
            if len(normalized_term) > 32:
                continue
            if normalized_term in seen_in_record:
                continue

            seen_in_record.add(normalized_term)
            token_counter[normalized_term] += 1

            previous = display_tokens.get(normalized_term, '')
            if not previous or len(display_term) < len(previous):
                display_tokens[normalized_term] = display_term

    ranked = sorted(
        token_counter.items(),
        key=lambda item: (-item[1], len(item[0]), item[0]),
    )

    recommendations: list[dict[str, object]] = []
    for normalized_term, occurrences in ranked:
        recommendations.append(
            {
                'term': display_tokens.get(normalized_term, normalized_term),
                'normalized_term': normalized_term,
                'occurrences': occurrences,
                'exists': normalized_term in existing,
            }
        )
        if len(recommendations) >= max(1, int(limit)):
            break

    return recommendations


def _records_for_stage(project: CompareProject, stage: str):
    stage_value = (stage or 'all').strip().lower()
    records = []
    if stage_value in {'all', 'budget'}:
        records.extend(deserialize_standard_records(project.budget_records))
    if stage_value in {'all', 'quantity'}:
        records.extend(deserialize_standard_records(project.quantity_records))
    return records


def _tokenize_name(raw_name: str) -> list[str]:
    if not raw_name:
        return []
    return [item.strip() for item in TOKEN_PATTERN.findall(raw_name) if item.strip()]
