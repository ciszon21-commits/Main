from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from .matching import (
    _tokenize,
    compare_items,
    exact_match,
    fuzzy_match,
    generate_uid,
    run_full_match,
    standardize_name,
)
from .models import IntermediateItem, MatchResult, Project

User = get_user_model()


class StandardizeNameTests(TestCase):
    """standardize_name 正規化測試"""

    def test_fullwidth_to_halfwidth(self):
        result = standardize_name("ＡＢＣ１２３")
        self.assertEqual(result, "ABC123")

    def test_strips_whitespace(self):
        result = standardize_name("  預力鋼筋　混凝土  ")
        self.assertEqual(result, "預力鋼筋 混凝土")

    def test_empty_string(self):
        self.assertEqual(standardize_name(""), "")
        self.assertEqual(standardize_name(None), "")

    def test_mixed_fullwidth_halfwidth(self):
        result = standardize_name("ＰＣ鋼棒 φ32mm")
        self.assertEqual(result, "PC鋼棒 φ32mm")


class GenerateUIDTests(TestCase):
    """generate_uid 測試"""

    def test_format(self):
        uid = generate_uid("budget", 42, 7)
        self.assertEqual(uid, "budget_42_7")

    def test_uniqueness(self):
        uid1 = generate_uid("budget", 1, 1)
        uid2 = generate_uid("quantity", 1, 1)
        self.assertNotEqual(uid1, uid2)


class TokenizeTests(TestCase):
    """_tokenize 測試"""

    def test_chinese_tokens(self):
        tokens = _tokenize("鋼筋混凝土 PC鋼棒")
        self.assertIn("鋼筋混凝土", tokens)

    def test_english_tokens(self):
        tokens = _tokenize("HDPE pipe 200mm")
        self.assertIn("hdpe", tokens)
        self.assertIn("pipe", tokens)

    def test_empty(self):
        self.assertEqual(_tokenize(""), [])


class CompareItemsTests(TestCase):
    """compare_items 逐欄比對測試"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="tester", password="test1234")
        cls.project = Project.objects.create(name="Test Project", owner=cls.user)

    def _make_item(self, **kwargs):
        defaults = {
            "project": self.project,
            "uid": generate_uid("budget", 0, id(kwargs)),
            "item_name": "test",
            "standard_name": "test",
            "reference": IntermediateItem.REFERENCE_BUDGET,
        }
        defaults.update(kwargs)
        return IntermediateItem.objects.create(**defaults)

    def test_identical_items(self):
        a = self._make_item(
            uid="test_a_1",
            item_name="鋼筋混凝土",
            standard_name="鋼筋混凝土",
            quantity=Decimal("100.0000"),
            unit="m3",
        )
        b = self._make_item(
            uid="test_b_1",
            item_name="鋼筋混凝土",
            standard_name="鋼筋混凝土",
            quantity=Decimal("100.0000"),
            unit="m3",
            reference=IntermediateItem.REFERENCE_QUANTITY,
        )
        result = compare_items(a, b)
        self.assertTrue(result["is_name_consistent"])
        self.assertTrue(result["is_unit_consistent"])
        self.assertTrue(result["is_qty_consistent"])

    def test_quantity_mismatch(self):
        a = self._make_item(
            uid="test_a_2",
            standard_name="鋼筋",
            quantity=Decimal("100.0000"),
            unit="kg",
        )
        b = self._make_item(
            uid="test_b_2",
            standard_name="鋼筋",
            quantity=Decimal("200.0000"),
            unit="kg",
            reference=IntermediateItem.REFERENCE_QUANTITY,
        )
        result = compare_items(a, b)
        self.assertTrue(result["is_name_consistent"])
        self.assertFalse(result["is_qty_consistent"])
        self.assertAlmostEqual(result["qty_delta"], -100.0)

    def test_unit_mismatch(self):
        a = self._make_item(uid="test_a_3", standard_name="混凝土", unit="m3")
        b = self._make_item(
            uid="test_b_3",
            standard_name="混凝土",
            unit="m2",
            reference=IntermediateItem.REFERENCE_QUANTITY,
        )
        result = compare_items(a, b)
        self.assertFalse(result["is_unit_consistent"])


class ExactMatchTests(TestCase):
    """exact_match 精準比對測試"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="exact_tester", password="test1234")
        cls.project = Project.objects.create(name="Exact Match Project", owner=cls.user)

        IntermediateItem.objects.create(
            uid="budget_1_0",
            project=cls.project,
            item_name="鋼筋混凝土 fc280",
            standard_name="鋼筋混凝土 fc280",
            quantity=Decimal("50.0000"),
            unit="m3",
            reference=IntermediateItem.REFERENCE_BUDGET,
            name_tokens=["鋼筋混凝土"],
        )
        IntermediateItem.objects.create(
            uid="quantity_1_0",
            project=cls.project,
            item_name="鋼筋混凝土 fc280",
            standard_name="鋼筋混凝土 fc280",
            quantity=Decimal("50.0000"),
            unit="m3",
            reference=IntermediateItem.REFERENCE_QUANTITY,
            name_tokens=["鋼筋混凝土"],
        )
        IntermediateItem.objects.create(
            uid="budget_1_1",
            project=cls.project,
            item_name="模板",
            standard_name="模板",
            quantity=Decimal("200.0000"),
            unit="m2",
            reference=IntermediateItem.REFERENCE_BUDGET,
            name_tokens=["模板"],
        )

    def test_exact_match_finds_pair(self):
        results = exact_match(self.project)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, 100)
        self.assertEqual(results[0].match_method, MatchResult.METHOD_EXACT)
        self.assertTrue(results[0].is_name_consistent)


class FuzzyMatchTests(TestCase):
    """fuzzy_match 模糊比對測試"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="fuzzy_tester", password="test1234")
        cls.project = Project.objects.create(name="Fuzzy Match Project", owner=cls.user)

        IntermediateItem.objects.create(
            uid="budget_2_0",
            project=cls.project,
            item_name="鋼筋混凝土構造物 fc280 kg/cm2",
            standard_name="鋼筋混凝土構造物 fc280 kg/cm2",
            quantity=Decimal("100.0000"),
            unit="m3",
            reference=IntermediateItem.REFERENCE_BUDGET,
            name_tokens=["鋼筋混凝土構造物", "fc280", "kg"],
        )
        IntermediateItem.objects.create(
            uid="quantity_2_0",
            project=cls.project,
            item_name="鋼筋混凝土構造物fc280kg/cm2",
            standard_name="鋼筋混凝土構造物fc280kg/cm2",
            quantity=Decimal("100.0000"),
            unit="m3",
            reference=IntermediateItem.REFERENCE_QUANTITY,
            name_tokens=["鋼筋混凝土構造物", "fc280kg"],
        )

    def test_fuzzy_match_finds_similar(self):
        results = fuzzy_match(self.project, threshold=70, exclude_exact=False)
        self.assertGreaterEqual(len(results), 1)
        self.assertGreaterEqual(results[0].score, 70)
