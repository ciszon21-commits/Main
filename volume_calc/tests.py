from django.test import TestCase
from django.urls import reverse
from .models import ProjectCase

class ProjectCaseModelTest(TestCase):
    def setUp(self):
        self.case = ProjectCase.objects.create(
            name="Test Case A",
            base_area=1029,
            original_volume=2000,
            zone_type="第三種住宅區",
            volume_ratio=2.25,
            reward_parameters={"rule5": 10, "rule6": 8}
        )

    def test_model_creation(self):
        self.assertEqual(self.case.name, "Test Case A")
        self.assertEqual(self.case.base_area, 1029)
        self.assertEqual(self.case.reward_parameters["rule5"], 10)
        self.assertEqual(str(self.case), "Test Case A - 第三種住宅區")


