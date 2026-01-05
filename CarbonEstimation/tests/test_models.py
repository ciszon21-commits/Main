from django.test import TestCase
from django.contrib.auth.models import User
from CarbonEstimation.models import MainCategory, ComponentItem, Scenario, ScenarioData

class MainCategoryTests(TestCase):
    def setUp(self):
        self.category = MainCategory.objects.create(
            code="A01",
            name="Test Category",
            order=1
        )

    def test_string_representation(self):
        self.assertEqual(str(self.category), "A01 Test Category")

    def test_ordering(self):
        category2 = MainCategory.objects.create(
            code="A02",
            name="Test Category 2",
            order=2
        )
        categories = MainCategory.objects.all()
        self.assertEqual(categories[0], self.category)
        self.assertEqual(categories[1], category2)

class ComponentItemTests(TestCase):
    def setUp(self):
        self.category = MainCategory.objects.create(code="B01", name="Cat B", order=1)
        self.item = ComponentItem.objects.create(
            category=self.category,
            item_no="I1001",
            work_item="Concrete Work",
            unit="m3",
            default_quantity=100.00
        )

    def test_string_representation(self):
        self.assertEqual(str(self.item), "I1001 Concrete Work")

    def test_default_values(self):
        self.assertEqual(self.item.level, 3)
        self.assertEqual(self.item.order, 0)

class ScenarioTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.scenario = Scenario.objects.create(
            project_number="P-2023-001",
            project_name="Test Project",
            scenario_name="Base Scenario",
            creator=self.user
        )

    def test_string_representation(self):
        self.assertEqual(str(self.scenario), "P-2023-001 - Base Scenario")

    def test_can_edit_creator(self):
        self.assertTrue(self.scenario.can_edit(self.user))

    def test_can_edit_collaborator(self):
        other_user = User.objects.create_user(username='other', password='password')
        self.assertFalse(self.scenario.can_edit(other_user))
        self.scenario.collaborators.add(other_user)
        self.assertTrue(self.scenario.can_edit(other_user))

    def test_can_edit_anonymous_scenario(self):
        anon_scenario = Scenario.objects.create(
            project_number="P-Anon",
            project_name="Anon Project",
            scenario_name="Anon Scenario"
        )
        self.assertTrue(anon_scenario.can_edit(self.user))

    def test_can_delete(self):
        other_user = User.objects.create_user(username='other', password='password')
        self.assertTrue(self.scenario.can_delete(self.user))
        self.assertFalse(self.scenario.can_delete(other_user))

class ScenarioDataTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = MainCategory.objects.create(code="C01", name="Cat C")
        self.item = ComponentItem.objects.create(
            category=self.category,
            item_no="I2001",
            work_item="Steel Work"
        )
        self.scenario = Scenario.objects.create(
            project_number="P-2023-002",
            project_name="Test Project 2",
            scenario_name="Scenario 2",
            creator=self.user
        )

    def test_create_data(self):
        data = ScenarioData.objects.create(
            scenario=self.scenario,
            category=self.category,
            component_item=self.item,
            quantity=50.0
        )
        self.assertEqual(str(data), "Scenario 2 - I2001")
        self.assertEqual(data.quantity, 50.0)
