from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase

from .services.matcher import MatchOptions, compare_all_methods
from .services.normalization import normalize_name, normalize_record, normalize_unit
from .services.parsers import _parse_sheet_rows, parse_budget_xml
from .services.schemas import StandardRecord
from .services.serialization import (
    build_unique_name_baseline_records,
    contains_cjk_text,
    extract_budget_terms,
    serialize_standard_records,
)


class NormalizationTests(SimpleTestCase):
    def test_name_normalization_removes_symbols(self):
        self.assertEqual(normalize_name('鋼筋-#4 (SD420W)'), '鋼筋4sd420w')

    def test_unit_normalization_maps_synonyms(self):
        self.assertEqual(normalize_unit(' 公斤 '), 'kg')
        self.assertEqual(normalize_unit('M^2'), 'm2')


class MatcherTests(SimpleTestCase):
    def test_exact_and_weighted_match_can_find_pair(self):
        left = normalize_record(
            StandardRecord(
                source_type='budget_xml',
                source_id='xml-1',
                name='鋼筋 SD420W',
                quantity=Decimal('10'),
                unit='公斤',
                raw_payload={},
            )
        )
        right = normalize_record(
            StandardRecord(
                source_type='quantity_sheet',
                source_id='Sheet1:2',
                name='鋼筋SD420W',
                quantity=Decimal('10.00'),
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
        result_map = {item.method: item for item in method_results}
        self.assertEqual(len(result_map['exact'].matches), 1)
        self.assertEqual(len(result_map['weighted'].matches), 1)

    def test_weighted_match_can_use_global_keyword_feature_bonus(self):
        left = normalize_record(
            StandardRecord(
                source_type='budget_xml',
                source_id='xml-k-1',
                name='steel bar install',
                quantity=Decimal('10'),
                unit='kg',
                raw_payload={},
            )
        )
        right = normalize_record(
            StandardRecord(
                source_type='quantity_sheet',
                source_id='sheet-k-1',
                name='steel reinforce bar',
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
            without_keyword = compare_all_methods(
                [left],
                [right],
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.95,
                    weighted_threshold=0.74,
                ),
            )
            with_keyword = compare_all_methods(
                [left],
                [right],
                MatchOptions(
                    quantity_tolerance=Decimal('0.01'),
                    fuzzy_threshold=0.95,
                    weighted_threshold=0.74,
                    keyword_terms=('steel',),
                    keyword_boost=0.08,
                ),
            )

        no_keyword_map = {item.method: item for item in without_keyword}
        with_keyword_map = {item.method: item for item in with_keyword}
        self.assertEqual(len(no_keyword_map['weighted'].matches), 0)
        self.assertEqual(len(with_keyword_map['weighted'].matches), 1)


class SerializationTests(SimpleTestCase):
    def test_extract_budget_terms_is_unique_by_normalized_name(self):
        records = [
            StandardRecord('budget_xml', '1', 'Rebar SD420W', Decimal('10'), 'kg', {}),
            StandardRecord('budget_xml', '2', 'Rebar-SD420W', Decimal('12'), 'kg', {}),
        ]
        terms = extract_budget_terms(records)
        self.assertEqual(len(terms), 1)

    def test_extract_budget_terms_chinese_only_filters_english(self):
        records = [
            StandardRecord('budget_xml', '1', 'GENERAL REQUIREMENTS', Decimal('1'), '式', {}),
            StandardRecord('budget_xml', '2', '施工管理與協調', Decimal('1'), '式', {}),
            StandardRecord('budget_xml', '3', 'SD420W', Decimal('10'), 't', {}),
        ]
        terms = extract_budget_terms(records, chinese_only=True)
        self.assertEqual(len(terms), 1)
        self.assertEqual(terms[0]['name'], '施工管理與協調')

    def test_contains_cjk_text(self):
        self.assertTrue(contains_cjk_text('施工管理與協調'))
        self.assertFalse(contains_cjk_text('GENERAL REQUIREMENTS'))

    def test_serialize_standard_records_contains_expected_keys(self):
        records = [
            StandardRecord('budget_xml', '1', 'Formwork', Decimal('5'), 'm2', {'a': 1}),
        ]
        payload = serialize_standard_records(records)
        self.assertEqual(payload[0]['source_id'], '1')
        self.assertEqual(payload[0]['quantity'], '5')

    def test_build_unique_name_baseline_records_deduplicates_and_sums_quantity(self):
        records = [
            StandardRecord('budget_xml', '1', '施工管理', Decimal('1'), '式', {}),
            StandardRecord('budget_xml', '2', '施工 管理', Decimal('2'), '式', {}),
            StandardRecord('budget_xml', '3', 'GENERAL REQUIREMENTS', Decimal('3'), '式', {}),
        ]
        baseline = build_unique_name_baseline_records(records, chinese_only=True)
        self.assertEqual(len(baseline), 1)
        self.assertEqual(baseline[0].name, '施工管理')
        self.assertEqual(baseline[0].quantity, Decimal('3'))
        self.assertIn('(+1)', baseline[0].source_id)


class ParserTests(SimpleTestCase):
    def test_parse_sheet_rows_supports_item_description_header(self):
        rows = [
            ['', '', '', ''],
            ['項次', '項目及說明', '單位', '數量'],
            ['1.0', 'Type S1', 'm2', '6713.55'],
            ['1.1', '鋼筋籠', '', ''],
        ]
        records = _parse_sheet_rows(rows, 'SheetA')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, 'Type S1')
        self.assertEqual(str(records[0].quantity), '6713.55')
        self.assertEqual(records[0].unit, 'm2')

    def test_parse_budget_xml_prefers_zh_tw_language_value(self):
        xml = (
            '<Root>'
            '<WorkItem itemCode="A001">'
            '<Description language="zh-TW">工程管理</Description>'
            '<Description language="en">PROJECT MANAGEMENT</Description>'
            '<Unit language="zh-TW">式</Unit>'
            '<Unit language="en">LS</Unit>'
            '<Quantity>1</Quantity>'
            '</WorkItem>'
            '</Root>'
        ).encode('utf-8')
        records = parse_budget_xml('sample.xml', xml)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, '工程管理')
        self.assertEqual(records[0].unit, '式')
