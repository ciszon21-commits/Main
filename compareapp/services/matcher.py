from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from difflib import SequenceMatcher
from functools import lru_cache
import math
from typing import TYPE_CHECKING

from .schemas import MatchResult, MethodComparisonResult, NormalizedRecord

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder
    from sentence_transformers import SentenceTransformer


@dataclass(frozen=True)
class MatchOptions:
    quantity_tolerance: Decimal
    fuzzy_threshold: float
    weighted_threshold: float
    semantic_threshold: float | None = None
    semantic_max_pairs: int = 120000
    semantic_prefilter_threshold: float | None = None
    semantic_top_k: int = 2
    semantic_candidate_max_pairs: int = 30000
    semantic_batch_size: int = 64
    sentence_model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'
    cross_encoder_threshold: float = 0.85
    cross_encoder_total_threshold: float | None = None
    cross_encoder_prefilter_threshold: float | None = None
    cross_encoder_top_k: int = 2
    cross_encoder_max_pairs: int = 4000
    cross_encoder_batch_size: int = 64
    cross_encoder_model_name: str = 'BAAI/bge-reranker-v2-m3'
    keyword_terms: tuple[str, ...] = ()
    keyword_boost: float = 0.08


@dataclass(frozen=True)
class KeywordFeatureContext:
    enabled: bool
    boost: float
    term_count: int
    left_hits: tuple[frozenset[str], ...]
    right_hits: tuple[frozenset[str], ...]


def compare_all_methods(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
) -> list[MethodComparisonResult]:
    keyword_context = _build_keyword_feature_context(left_records, right_records, options)
    return [
        _exact_match(left_records, right_records, options, keyword_context),
        _normalized_name_match(left_records, right_records, options, keyword_context),
        _fuzzy_name_match(left_records, right_records, options, keyword_context),
        _weighted_match(left_records, right_records, options, keyword_context),
        _sentence_transformer_match(left_records, right_records, options, keyword_context),
        _cross_encoder_match(left_records, right_records, options, keyword_context),
    ]


def _exact_match(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
    keyword_context: KeywordFeatureContext | None,
) -> MethodComparisonResult:
    used_right: set[int] = set()
    matches: list[MatchResult] = []
    unmatched_left: list[NormalizedRecord] = []

    for left in left_records:
        matched_index = None
        for idx, right in enumerate(right_records):
            if idx in used_right:
                continue
            if left.normalized_name != right.normalized_name:
                continue
            if left.normalized_unit != right.normalized_unit:
                continue
            quantity_score = _quantity_score(left, right, options.quantity_tolerance)
            if quantity_score < 1.0:
                continue
            matched_index = idx
            matches.append(
                MatchResult(
                    method='exact',
                    left=left,
                    right=right,
                    score=1.0,
                    name_score=1.0,
                    unit_score=1.0,
                    quantity_score=1.0,
                )
            )
            break

        if matched_index is None:
            unmatched_left.append(left)
        else:
            used_right.add(matched_index)

    unmatched_right = [record for idx, record in enumerate(right_records) if idx not in used_right]

    return MethodComparisonResult(
        method='exact',
        description='Exact match on normalized name, unit, and quantity.' + _keyword_description_suffix(keyword_context),
        matches=matches,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
    )


def _normalized_name_match(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
    keyword_context: KeywordFeatureContext | None,
) -> MethodComparisonResult:
    used_right: set[int] = set()
    matches: list[MatchResult] = []
    unmatched_left: list[NormalizedRecord] = []

    for left_idx, left in enumerate(left_records):
        matched_index = None
        for idx, right in enumerate(right_records):
            if idx in used_right:
                continue
            if left.normalized_name != right.normalized_name:
                continue
            name_score = 1.0
            unit_score = 1.0 if left.normalized_unit == right.normalized_unit else 0.5
            quantity_score = _quantity_score(left, right, options.quantity_tolerance)
            base_score = (0.6 * name_score) + (0.2 * unit_score) + (0.2 * quantity_score)
            total_score = min(1.0, base_score + _keyword_bonus(keyword_context, left_idx, idx))
            if total_score < options.weighted_threshold:
                continue

            matched_index = idx
            matches.append(
                MatchResult(
                    method='normalized',
                    left=left,
                    right=right,
                    score=round(total_score, 4),
                    name_score=name_score,
                    unit_score=unit_score,
                    quantity_score=quantity_score,
                )
            )
            break

        if matched_index is None:
            unmatched_left.append(left)
        else:
            used_right.add(matched_index)

    unmatched_right = [record for idx, record in enumerate(right_records) if idx not in used_right]

    return MethodComparisonResult(
        method='normalized',
        description='Match by normalized name first, then score unit and quantity.' + _keyword_description_suffix(keyword_context),
        matches=matches,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
    )


def _fuzzy_name_match(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
    keyword_context: KeywordFeatureContext | None,
) -> MethodComparisonResult:
    used_right: set[int] = set()
    matches: list[MatchResult] = []
    unmatched_left: list[NormalizedRecord] = []

    for left_idx, left in enumerate(left_records):
        best_index = None
        best_result: MatchResult | None = None

        for idx, right in enumerate(right_records):
            if idx in used_right:
                continue
            name_score = _name_similarity(left.normalized_name, right.normalized_name)
            if name_score < options.fuzzy_threshold:
                continue
            unit_score = 1.0 if left.normalized_unit == right.normalized_unit else 0.5
            quantity_score = _quantity_score(left, right, options.quantity_tolerance)
            base_score = (0.7 * name_score) + (0.15 * unit_score) + (0.15 * quantity_score)
            total_score = min(1.0, base_score + _keyword_bonus(keyword_context, left_idx, idx))

            candidate = MatchResult(
                method='fuzzy',
                left=left,
                right=right,
                score=round(total_score, 4),
                name_score=round(name_score, 4),
                unit_score=unit_score,
                quantity_score=quantity_score,
            )
            if best_result is None or candidate.score > best_result.score:
                best_result = candidate
                best_index = idx

        if best_result is None or best_index is None:
            unmatched_left.append(left)
            continue

        used_right.add(best_index)
        matches.append(best_result)

    unmatched_right = [record for idx, record in enumerate(right_records) if idx not in used_right]

    return MethodComparisonResult(
        method='fuzzy',
        description='Character-level similarity with difflib SequenceMatcher.' + _keyword_description_suffix(keyword_context),
        matches=matches,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
    )


def _sentence_transformer_match(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
    keyword_context: KeywordFeatureContext | None,
) -> MethodComparisonResult:
    if not left_records or not right_records:
        return MethodComparisonResult(
            method='sentence_transformer',
            description='Semantic matching skipped: no records to compare.',
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    total_pairs = len(left_records) * len(right_records)
    pair_meta = _build_sentence_transformer_pair_meta(left_records, right_records, options)
    if not pair_meta:
        return MethodComparisonResult(
            method='sentence_transformer',
            description='Semantic matching skipped: no candidate pairs after pre-filtering.',
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    model, status_description = _load_sentence_model(options.sentence_model_name)
    if model is None:
        return MethodComparisonResult(
            method='sentence_transformer',
            description=status_description,
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    if not left_records or not right_records:
        return MethodComparisonResult(
            method='sentence_transformer',
            description=status_description,
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    candidate_left_indices = sorted({left_idx for left_idx, _, _, _ in pair_meta})
    candidate_right_indices = sorted({right_idx for _, right_idx, _, _ in pair_meta})
    candidate_left_records = [left_records[index] for index in candidate_left_indices]
    candidate_right_records = [right_records[index] for index in candidate_right_indices]

    try:
        left_embeddings = _encode_texts(
            model,
            [_semantic_text(item) for item in candidate_left_records],
            batch_size=options.semantic_batch_size,
        )
        right_embeddings = _encode_texts(
            model,
            [_semantic_text(item) for item in candidate_right_records],
            batch_size=options.semantic_batch_size,
        )
        if len(left_embeddings) != len(candidate_left_records):
            raise ValueError('left embedding size mismatch')
        if len(right_embeddings) != len(candidate_right_records):
            raise ValueError('right embedding size mismatch')
    except Exception as exc:  # pragma: no cover - defensive fallback
        return MethodComparisonResult(
            method='sentence_transformer',
            description=(
                'Semantic matching skipped: encoding failed '
                f'({exc.__class__.__name__}).'
            ),
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    semantic_threshold = (
        options.semantic_threshold
        if options.semantic_threshold is not None
        else options.weighted_threshold
    )

    left_embedding_map = {
        record_index: left_embeddings[offset]
        for offset, record_index in enumerate(candidate_left_indices)
    }
    right_embedding_map = {
        record_index: right_embeddings[offset]
        for offset, record_index in enumerate(candidate_right_indices)
    }

    candidates: list[tuple[float, int, int, MatchResult]] = []
    for left_idx, right_idx, left, right in pair_meta:
        left_vector = left_embedding_map.get(left_idx)
        right_vector = right_embedding_map.get(right_idx)
        if left_vector is None or right_vector is None:
            continue

        cosine_score = _dot_product(left_vector, right_vector)
        name_score = _cosine_to_similarity(cosine_score)
        if name_score < semantic_threshold:
            continue

        unit_score = _unit_score(left, right)
        quantity_score = _quantity_score(left, right, options.quantity_tolerance)
        base_score = (0.7 * name_score) + (0.15 * unit_score) + (0.15 * quantity_score)
        total_score = min(1.0, base_score + _keyword_bonus(keyword_context, left_idx, right_idx))

        candidates.append(
            (
                total_score,
                left_idx,
                right_idx,
                MatchResult(
                    method='sentence_transformer',
                    left=left,
                    right=right,
                    score=round(total_score, 4),
                    name_score=round(name_score, 4),
                    unit_score=round(unit_score, 4),
                    quantity_score=round(quantity_score, 4),
                ),
            )
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    used_left: set[int] = set()
    used_right: set[int] = set()
    matches: list[MatchResult] = []

    for _, left_idx, right_idx, match in candidates:
        if left_idx in used_left or right_idx in used_right:
            continue
        used_left.add(left_idx)
        used_right.add(right_idx)
        matches.append(match)

    unmatched_left = [record for idx, record in enumerate(left_records) if idx not in used_left]
    unmatched_right = [record for idx, record in enumerate(right_records) if idx not in used_right]

    return MethodComparisonResult(
        method='sentence_transformer',
        description=(
            f'{status_description} '
            f'candidate_pairs={len(pair_meta)}/{total_pairs}, threshold={semantic_threshold:.2f}.'
            f'{_keyword_description_suffix(keyword_context)}'
        ),
        matches=matches,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
    )


def _weighted_match(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
    keyword_context: KeywordFeatureContext | None,
) -> MethodComparisonResult:
    candidates: list[tuple[float, int, int, MatchResult]] = []
    for left_idx, left in enumerate(left_records):
        for right_idx, right in enumerate(right_records):
            name_score = _name_similarity(left.normalized_name, right.normalized_name)
            unit_score = _unit_score(left, right)
            quantity_score = _quantity_score(left, right, options.quantity_tolerance)
            base_score = (0.6 * name_score) + (0.2 * unit_score) + (0.2 * quantity_score)
            total_score = min(1.0, base_score + _keyword_bonus(keyword_context, left_idx, right_idx))
            if total_score < options.weighted_threshold:
                continue
            candidates.append(
                (
                    total_score,
                    left_idx,
                    right_idx,
                    MatchResult(
                        method='weighted',
                        left=left,
                        right=right,
                        score=round(total_score, 4),
                        name_score=round(name_score, 4),
                        unit_score=round(unit_score, 4),
                        quantity_score=round(quantity_score, 4),
                    ),
                )
            )

    candidates.sort(key=lambda item: item[0], reverse=True)
    used_left: set[int] = set()
    used_right: set[int] = set()
    matches: list[MatchResult] = []

    for _, left_idx, right_idx, match in candidates:
        if left_idx in used_left or right_idx in used_right:
            continue
        used_left.add(left_idx)
        used_right.add(right_idx)
        matches.append(match)

    unmatched_left = [record for idx, record in enumerate(left_records) if idx not in used_left]
    unmatched_right = [record for idx, record in enumerate(right_records) if idx not in used_right]

    return MethodComparisonResult(
        method='weighted',
        description='Weighted score of name, unit, and quantity.' + _keyword_description_suffix(keyword_context),
        matches=matches,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
    )


def _cross_encoder_match(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
    keyword_context: KeywordFeatureContext | None,
) -> MethodComparisonResult:
    model, status_description = _load_cross_encoder_model(options.cross_encoder_model_name)
    if model is None:
        return MethodComparisonResult(
            method='cross_encoder',
            description=status_description,
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    if not left_records or not right_records:
        return MethodComparisonResult(
            method='cross_encoder',
            description=status_description,
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    pair_meta = _build_cross_encoder_pair_meta(left_records, right_records, options)
    if not pair_meta:
        return MethodComparisonResult(
            method='cross_encoder',
            description='Cross-encoder matching skipped: no candidate pairs after pre-filtering.',
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    pairs = [(_cross_text(left), _cross_text(right)) for _, _, left, right in pair_meta]

    try:
        raw_scores = _predict_cross_scores(model, pairs, batch_size=options.cross_encoder_batch_size)
        if len(raw_scores) != len(pair_meta):
            raise ValueError('cross encoder score size mismatch')
    except Exception as exc:  # pragma: no cover - defensive fallback
        return MethodComparisonResult(
            method='cross_encoder',
            description=(
                'Cross-encoder matching skipped: scoring failed '
                f'({exc.__class__.__name__}).'
            ),
            matches=[],
            unmatched_left=list(left_records),
            unmatched_right=list(right_records),
        )

    cross_threshold = _clamp01(options.cross_encoder_threshold)
    total_threshold = options.cross_encoder_total_threshold
    if total_threshold is None:
        total_threshold = max(cross_threshold, options.weighted_threshold)
    total_threshold = _clamp01(total_threshold)

    candidates: list[tuple[float, int, int, MatchResult]] = []
    for raw_score, meta in zip(raw_scores, pair_meta):
        left_idx, right_idx, left, right = meta
        name_score = _cross_score_to_similarity(raw_score)
        if name_score < cross_threshold:
            continue

        unit_score = _unit_score(left, right)
        quantity_score = _quantity_score(left, right, options.quantity_tolerance)
        base_score = (0.8 * name_score) + (0.1 * unit_score) + (0.1 * quantity_score)
        total_score = min(1.0, base_score + _keyword_bonus(keyword_context, left_idx, right_idx))
        if total_score < total_threshold:
            continue

        candidates.append(
            (
                total_score,
                left_idx,
                right_idx,
                MatchResult(
                    method='cross_encoder',
                    left=left,
                    right=right,
                    score=round(total_score, 4),
                    name_score=round(name_score, 4),
                    unit_score=round(unit_score, 4),
                    quantity_score=round(quantity_score, 4),
                ),
            )
        )

    candidates.sort(key=lambda item: item[0], reverse=True)
    used_left: set[int] = set()
    used_right: set[int] = set()
    matches: list[MatchResult] = []

    for _, left_idx, right_idx, match in candidates:
        if left_idx in used_left or right_idx in used_right:
            continue
        used_left.add(left_idx)
        used_right.add(right_idx)
        matches.append(match)

    unmatched_left = [record for idx, record in enumerate(left_records) if idx not in used_left]
    unmatched_right = [record for idx, record in enumerate(right_records) if idx not in used_right]

    return MethodComparisonResult(
        method='cross_encoder',
        description=(
            f'{status_description} '
            f'name_threshold={cross_threshold:.2f}, total_threshold={total_threshold:.2f}, '
            f'candidate_pairs={len(pair_meta)}.'
            f'{_keyword_description_suffix(keyword_context)}'
        ),
        matches=matches,
        unmatched_left=unmatched_left,
        unmatched_right=unmatched_right,
    )


def _build_keyword_feature_context(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
) -> KeywordFeatureContext | None:
    boost = max(0.0, float(options.keyword_boost))
    if boost <= 0.0:
        return None

    unique_terms = tuple(
        sorted(
            {
                term.strip()
                for term in options.keyword_terms
                if isinstance(term, str) and len(term.strip()) >= 2
            }
        )
    )
    if not unique_terms:
        return None

    left_hits = tuple(
        frozenset(_keyword_hits_for_name(record.normalized_name, unique_terms))
        for record in left_records
    )
    right_hits = tuple(
        frozenset(_keyword_hits_for_name(record.normalized_name, unique_terms))
        for record in right_records
    )

    return KeywordFeatureContext(
        enabled=True,
        boost=boost,
        term_count=len(unique_terms),
        left_hits=left_hits,
        right_hits=right_hits,
    )


def _keyword_hits_for_name(name: str, keyword_terms: tuple[str, ...]) -> set[str]:
    if not name:
        return set()
    return {term for term in keyword_terms if term in name}


def _keyword_bonus(
    keyword_context: KeywordFeatureContext | None,
    left_idx: int,
    right_idx: int,
) -> float:
    if keyword_context is None or not keyword_context.enabled:
        return 0.0

    if left_idx >= len(keyword_context.left_hits) or right_idx >= len(keyword_context.right_hits):
        return 0.0

    left_hits = keyword_context.left_hits[left_idx]
    right_hits = keyword_context.right_hits[right_idx]
    if not left_hits or not right_hits:
        return 0.0

    overlap = left_hits.intersection(right_hits)
    if not overlap:
        return 0.0

    denominator = max(1, min(len(left_hits), len(right_hits)))
    overlap_ratio = len(overlap) / denominator
    return keyword_context.boost * overlap_ratio


def _keyword_description_suffix(keyword_context: KeywordFeatureContext | None) -> str:
    if keyword_context is None or not keyword_context.enabled:
        return ''
    return f' Keyword feature enabled ({keyword_context.term_count} global terms).'


def _name_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return SequenceMatcher(a=left, b=right).ratio()


def _unit_score(left: NormalizedRecord, right: NormalizedRecord) -> float:
    if not left.normalized_unit and not right.normalized_unit:
        return 1.0
    if not left.normalized_unit or not right.normalized_unit:
        return 0.5
    return 1.0 if left.normalized_unit == right.normalized_unit else 0.0


def _quantity_score(
    left: NormalizedRecord, right: NormalizedRecord, tolerance: Decimal
) -> float:
    left_qty = left.normalized_quantity
    right_qty = right.normalized_quantity
    if left_qty is None and right_qty is None:
        return 1.0
    if left_qty is None or right_qty is None:
        return 0.3

    diff = abs(left_qty - right_qty)
    if diff <= tolerance:
        return 1.0

    scale = max(abs(left_qty), abs(right_qty), Decimal('1'))
    ratio = float(diff / scale)
    return max(0.0, 1.0 - ratio)


def _semantic_text(record: NormalizedRecord) -> str:
    return record.normalized_name or record.original.name


def _cross_text(record: NormalizedRecord) -> str:
    text = record.original.name.strip()
    if text:
        return text
    return record.normalized_name


def _cosine_to_similarity(cosine_score: float) -> float:
    bounded = max(-1.0, min(1.0, cosine_score))
    return (bounded + 1.0) / 2.0


def _cross_score_to_similarity(raw_score: float) -> float:
    if not math.isfinite(raw_score):
        return 0.0

    if 0.0 <= raw_score <= 1.0:
        return raw_score

    if -1.0 <= raw_score <= 1.0:
        return (raw_score + 1.0) / 2.0

    return _sigmoid(raw_score)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        exponent = math.exp(-value)
        return 1.0 / (1.0 + exponent)

    exponent = math.exp(value)
    return exponent / (1.0 + exponent)


def _short_error(exc: Exception, max_length: int = 140) -> str:
    message = str(exc).replace('\n', ' ').strip()
    if not message:
        return 'no details'
    if len(message) <= max_length:
        return message
    return message[: max_length - 3] + '...'


def _load_sentence_model(model_name: str) -> tuple['SentenceTransformer | None', str]:
    try:
        model = _get_sentence_model(model_name)
    except ImportError:
        return None, 'Semantic matching skipped: sentence-transformers is not installed.'
    except Exception as exc:
        return (
            None,
            'Semantic matching skipped: unable to load '
            f'"{model_name}" ({exc.__class__.__name__}: {_short_error(exc)}).',
        )

    return model, 'Semantic name matching with sentence-transformers cosine similarity.'


def _load_cross_encoder_model(model_name: str) -> tuple['CrossEncoder | None', str]:
    try:
        model = _get_cross_encoder_model(model_name)
    except ImportError:
        return None, 'Cross-encoder matching skipped: sentence-transformers is not installed.'
    except Exception as exc:
        return (
            None,
            'Cross-encoder matching skipped: unable to load '
            f'"{model_name}" ({exc.__class__.__name__}: {_short_error(exc)}).',
        )

    return model, f'Cross-encoder semantic verification with "{model_name}".'


@lru_cache(maxsize=4)
def _get_sentence_model(model_name: str) -> 'SentenceTransformer':
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


@lru_cache(maxsize=4)
def _get_cross_encoder_model(model_name: str) -> 'CrossEncoder':
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)


def _encode_texts(
    model: 'SentenceTransformer',
    texts: list[str],
    batch_size: int = 64,
):
    safe_batch_size = max(1, int(batch_size))
    encode_attempts = [
        {
            'normalize_embeddings': True,
            'convert_to_numpy': True,
            'show_progress_bar': False,
            'batch_size': safe_batch_size,
        },
        {
            'convert_to_numpy': True,
            'show_progress_bar': False,
            'batch_size': safe_batch_size,
        },
        {
            'convert_to_numpy': True,
            'batch_size': safe_batch_size,
        },
        {
            'convert_to_numpy': True,
        },
        {},
    ]

    vectors = None
    last_error: Exception | None = None
    for kwargs in encode_attempts:
        try:
            vectors = model.encode(texts, **kwargs)
            break
        except TypeError as exc:
            last_error = exc

    if vectors is None:
        if last_error is not None:
            raise last_error
        raise ValueError('unable to encode texts')

    return [_normalize_vector(row) for row in _to_matrix(vectors)]


def _predict_cross_scores(
    model: 'CrossEncoder',
    pairs: list[tuple[str, str]],
    batch_size: int = 64,
) -> list[float]:
    if not pairs:
        return []

    safe_batch_size = max(1, int(batch_size))
    output: list[float] = []
    for index in range(0, len(pairs), safe_batch_size):
        chunk = pairs[index : index + safe_batch_size]
        try:
            raw_scores = model.predict(chunk, convert_to_numpy=True)
        except TypeError:
            raw_scores = model.predict(chunk)
        output.extend(_to_score_list(raw_scores))
    return output


def _build_cross_encoder_pair_meta(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
) -> list[tuple[int, int, NormalizedRecord, NormalizedRecord]]:
    total_pairs = len(left_records) * len(right_records)
    max_pairs = max(1, int(options.cross_encoder_max_pairs))
    top_k = max(1, min(int(options.cross_encoder_top_k), len(right_records)))

    if total_pairs <= max_pairs:
        return [
            (left_idx, right_idx, left, right)
            for left_idx, left in enumerate(left_records)
            for right_idx, right in enumerate(right_records)
        ]

    prefilter_threshold = options.cross_encoder_prefilter_threshold
    if prefilter_threshold is None:
        prefilter_threshold = options.fuzzy_threshold
    prefilter_threshold = _clamp01(prefilter_threshold)

    candidate_scores: dict[tuple[int, int], float] = {}
    for left_idx, left in enumerate(left_records):
        ranked: list[tuple[float, int]] = []
        for right_idx, right in enumerate(right_records):
            pre_score = _name_similarity(left.normalized_name, right.normalized_name)
            if pre_score < prefilter_threshold:
                continue
            ranked.append((pre_score, right_idx))
        if not ranked:
            continue
        ranked.sort(key=lambda item: item[0], reverse=True)

        for pre_score, right_idx in ranked[:top_k]:
            key = (left_idx, right_idx)
            existing = candidate_scores.get(key)
            if existing is None or pre_score > existing:
                candidate_scores[key] = pre_score

    ranked_pairs = sorted(
        candidate_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:max_pairs]

    return [
        (
            left_idx,
            right_idx,
            left_records[left_idx],
            right_records[right_idx],
        )
        for (left_idx, right_idx), _ in ranked_pairs
    ]


def _build_sentence_transformer_pair_meta(
    left_records: list[NormalizedRecord],
    right_records: list[NormalizedRecord],
    options: MatchOptions,
) -> list[tuple[int, int, NormalizedRecord, NormalizedRecord]]:
    total_pairs = len(left_records) * len(right_records)
    if total_pairs <= options.semantic_max_pairs:
        return [
            (left_idx, right_idx, left, right)
            for left_idx, left in enumerate(left_records)
            for right_idx, right in enumerate(right_records)
        ]

    max_pairs = max(1, int(options.semantic_candidate_max_pairs))
    top_k = max(1, min(int(options.semantic_top_k), len(right_records)))
    prefilter_threshold = options.semantic_prefilter_threshold
    if prefilter_threshold is None:
        prefilter_threshold = min(0.75, max(0.4, options.fuzzy_threshold - 0.1))
    prefilter_threshold = _clamp01(prefilter_threshold)

    candidate_scores: dict[tuple[int, int], float] = {}
    for left_idx, left in enumerate(left_records):
        ranked: list[tuple[float, int]] = []
        for right_idx, right in enumerate(right_records):
            pre_score = _name_similarity(left.normalized_name, right.normalized_name)
            if pre_score < prefilter_threshold:
                continue
            ranked.append((pre_score, right_idx))

        if not ranked:
            continue

        ranked.sort(key=lambda item: item[0], reverse=True)
        for pre_score, right_idx in ranked[:top_k]:
            key = (left_idx, right_idx)
            existing = candidate_scores.get(key)
            if existing is None or pre_score > existing:
                candidate_scores[key] = pre_score

    ranked_pairs = sorted(
        candidate_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:max_pairs]

    return [
        (
            left_idx,
            right_idx,
            left_records[left_idx],
            right_records[right_idx],
        )
        for (left_idx, right_idx), _ in ranked_pairs
    ]


def _to_matrix(vectors: object) -> list[list[float]]:
    if vectors is None:
        return []

    if hasattr(vectors, 'tolist'):
        vectors = vectors.tolist()

    rows = list(vectors)
    if not rows:
        return []

    first = rows[0]
    if isinstance(first, (int, float)):
        return [[float(value) for value in rows]]

    matrix: list[list[float]] = []
    for row in rows:
        if hasattr(row, 'tolist'):
            row = row.tolist()
        matrix.append([float(value) for value in row])
    return matrix


def _to_score_list(scores: object) -> list[float]:
    if scores is None:
        return []

    if hasattr(scores, 'tolist'):
        scores = scores.tolist()

    rows = list(scores)
    output: list[float] = []
    for row in rows:
        if hasattr(row, 'tolist'):
            row = row.tolist()

        if isinstance(row, (list, tuple)):
            if not row:
                output.append(0.0)
            elif len(row) == 1:
                output.append(float(row[0]))
            else:
                output.append(float(row[-1]))
            continue

        output.append(float(row))
    return output


def _normalize_vector(vector: list[float]) -> list[float]:
    if not vector:
        return []

    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0.0:
        return [0.0 for _ in vector]

    return [value / norm for value in vector]


def _dot_product(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0

    shared_size = min(len(left), len(right))
    return sum(left[index] * right[index] for index in range(shared_size))
