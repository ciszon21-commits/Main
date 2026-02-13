from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.matcher import MatchOptions, compare_all_methods
from .services.normalization import normalize_record
from .services.schemas import StandardRecord


class _FakeSentenceModel:
    def encode(self, texts, normalize_embeddings=True, convert_to_numpy=True):
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if 'steel' in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif 'concrete' in lowered:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])

        return vectors


class _FakeCrossEncoder:
    def predict(self, pairs, convert_to_numpy=True):
        scores: list[float] = []
        for left_text, right_text in pairs:
            left_lower = left_text.lower()
            right_lower = right_text.lower()
            if 'steel' in left_lower and 'steel' in right_lower:
                scores.append(0.96)
            elif 'concrete' in left_lower and 'concrete' in right_lower:
                scores.append(0.93)
            else:
                scores.append(0.08)
        return scores


class SentenceTransformerMatcherTests(SimpleTestCase):
    def test_method_order_places_complex_methods_last(self):
        left = normalize_record(
            StandardRecord(
                source_type='budget_xml',
                source_id='xml-1',
                name='Steel Bar',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )
        right = normalize_record(
            StandardRecord(
                source_type='quantity_sheet',
                source_id='sheet-1',
                name='Steel Reinforcement',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )

        with patch(
            'compareapp.services.matcher._get_sentence_model',
            side_effect=ImportError(),
        ), patch(
            'compareapp.services.matcher._get_cross_encoder_model',
            side_effect=ImportError(),
        ):
            method_results = compare_all_methods(
                [left],
                [right],
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.7,
                    weighted_threshold=0.7,
                ),
            )

        method_names = [item.method for item in method_results]
        self.assertEqual(
            method_names,
            [
                'exact',
                'normalized',
                'fuzzy',
                'weighted',
                'sentence_transformer',
                'cross_encoder',
            ],
        )

    def test_sentence_transformer_method_gracefully_handles_missing_dependency(self):
        left = normalize_record(
            StandardRecord(
                source_type='budget_xml',
                source_id='xml-1',
                name='Steel Bar',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )
        right = normalize_record(
            StandardRecord(
                source_type='quantity_sheet',
                source_id='sheet-1',
                name='Steel Reinforcement',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )

        with patch(
            'compareapp.services.matcher._get_sentence_model',
            side_effect=ImportError(),
        ), patch(
            'compareapp.services.matcher._get_cross_encoder_model',
            side_effect=ImportError(),
        ):
            method_results = compare_all_methods(
                [left],
                [right],
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.7,
                    weighted_threshold=0.7,
                    semantic_threshold=0.7,
                ),
            )

        result_map = {item.method: item for item in method_results}
        semantic_result = result_map['sentence_transformer']
        self.assertEqual(len(semantic_result.matches), 0)
        self.assertEqual(len(semantic_result.unmatched_left), 1)
        self.assertEqual(len(semantic_result.unmatched_right), 1)

    def test_sentence_transformer_method_matches_by_semantic_similarity(self):
        left = normalize_record(
            StandardRecord(
                source_type='budget_xml',
                source_id='xml-1',
                name='Steel Bar',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )
        right = normalize_record(
            StandardRecord(
                source_type='quantity_sheet',
                source_id='sheet-1',
                name='Steel Reinforcement',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )

        with patch(
            'compareapp.services.matcher._get_sentence_model',
            return_value=_FakeSentenceModel(),
        ), patch(
            'compareapp.services.matcher._get_cross_encoder_model',
            side_effect=ImportError(),
        ):
            method_results = compare_all_methods(
                [left],
                [right],
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.7,
                    weighted_threshold=0.7,
                    semantic_threshold=0.7,
                ),
            )

        result_map = {item.method: item for item in method_results}
        semantic_result = result_map['sentence_transformer']
        self.assertEqual(len(semantic_result.matches), 1)
        self.assertEqual(semantic_result.matches[0].left.original.source_id, 'xml-1')
        self.assertEqual(semantic_result.matches[0].right.original.source_id, 'sheet-1')
        self.assertGreaterEqual(semantic_result.matches[0].name_score, 0.99)

    def test_cross_encoder_method_gracefully_handles_missing_dependency(self):
        left = normalize_record(
            StandardRecord(
                source_type='budget_xml',
                source_id='xml-1',
                name='Steel Bar',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )
        right = normalize_record(
            StandardRecord(
                source_type='quantity_sheet',
                source_id='sheet-1',
                name='Steel Reinforcement',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )

        with patch(
            'compareapp.services.matcher._get_sentence_model',
            side_effect=ImportError(),
        ), patch(
            'compareapp.services.matcher._get_cross_encoder_model',
            side_effect=ImportError(),
        ):
            method_results = compare_all_methods(
                [left],
                [right],
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.7,
                    weighted_threshold=0.7,
                    semantic_threshold=0.7,
                ),
            )

        result_map = {item.method: item for item in method_results}
        cross_result = result_map['cross_encoder']
        self.assertEqual(len(cross_result.matches), 0)
        self.assertEqual(len(cross_result.unmatched_left), 1)
        self.assertEqual(len(cross_result.unmatched_right), 1)

    def test_cross_encoder_method_is_stricter_and_rejects_low_scores(self):
        left_records = [
            normalize_record(
                StandardRecord(
                    source_type='budget_xml',
                    source_id='xml-1',
                    name='Steel Bar',
                    quantity=Decimal('10'),
                    unit='kg',
                    raw_payload={},
                )
            ),
            normalize_record(
                StandardRecord(
                    source_type='budget_xml',
                    source_id='xml-2',
                    name='Concrete Casting',
                    quantity=Decimal('3'),
                    unit='m3',
                    raw_payload={},
                )
            ),
        ]
        right_records = [
            normalize_record(
                StandardRecord(
                    source_type='quantity_sheet',
                    source_id='sheet-1',
                    name='Steel Reinforcement',
                    quantity=Decimal('10'),
                    unit='kg',
                    raw_payload={},
                )
            ),
            normalize_record(
                StandardRecord(
                    source_type='quantity_sheet',
                    source_id='sheet-2',
                    name='Cable Tray',
                    quantity=Decimal('3'),
                    unit='m3',
                    raw_payload={},
                )
            ),
        ]

        with patch(
            'compareapp.services.matcher._get_sentence_model',
            side_effect=ImportError(),
        ), patch(
            'compareapp.services.matcher._get_cross_encoder_model',
            return_value=_FakeCrossEncoder(),
        ):
            method_results = compare_all_methods(
                left_records,
                right_records,
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.7,
                    weighted_threshold=0.7,
                    semantic_threshold=0.7,
                    cross_encoder_threshold=0.85,
                ),
            )

        result_map = {item.method: item for item in method_results}
        cross_result = result_map['cross_encoder']
        self.assertEqual(len(cross_result.matches), 1)
        self.assertEqual(cross_result.matches[0].left.original.source_id, 'xml-1')
        self.assertEqual(cross_result.matches[0].right.original.source_id, 'sheet-1')
        self.assertEqual(len(cross_result.unmatched_left), 1)
        self.assertEqual(len(cross_result.unmatched_right), 1)
