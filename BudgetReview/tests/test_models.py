from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from BudgetReview.models import (
    Project, Discipline, Stage, QuantityFile, PriceInquiryFile, 
    BudgetFile, FinalBudgetFile, PriceAdjustment, AuditLog
)
from datetime import timedelta
import datetime

class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.project = Project.objects.create(
            name='Test Project',
            code='TP001',
            description='Test Description',
            created_by=self.user
        )

    def test_project_creation(self):
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.code, 'TP001')
        self.assertEqual(self.project.status, 'PREPARING')
        self.assertFalse(self.project.is_deleted)

    def test_project_str(self):
        self.assertEqual(str(self.project), 'TP001 - Test Project')

    def test_soft_delete(self):
        self.project.deleted_at = timezone.now()
        self.project.save()
        self.assertTrue(self.project.is_deleted)

class DisciplineModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project', code='TP001')
        self.discipline = Discipline.objects.create(
            project=self.project,
            code='01',
            name='Civil Engineering'
        )

    def test_discipline_creation(self):
        self.assertEqual(self.discipline.name, 'Civil Engineering')
        self.assertEqual(self.discipline.code, '01')
        self.assertFalse(self.discipline.is_overall)

    def test_discipline_str(self):
        self.assertEqual(str(self.discipline), f'Test Project - [01] Civil Engineering')

    def test_prevent_overall_delete(self):
        overall = self.project.disciplines.get(is_overall=True)
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            overall.delete()

class StageModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Test Project', code='TP001')
        self.stage = Stage.objects.create(
            project=self.project,
            name='Stage 1',
            order=1,
            deadline=timezone.now() + timedelta(days=1)
        )

    def test_stage_creation(self):
        self.assertEqual(self.stage.name, 'Stage 1')
        self.assertEqual(self.stage.order, 1)

    def test_time_remaining(self):
        # Future
        self.assertIn('剩餘', self.stage.time_remaining)
        
        # Past
        self.stage.deadline = timezone.now() - timedelta(days=1)
        self.stage.save()
        self.assertEqual(self.stage.time_remaining, '已截止')

class FileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.project = Project.objects.create(name='Test Project', code='TP001')
        self.discipline = Discipline.objects.create(project=self.project, code='01', name='Civil')
        
    def test_quantity_file_creation(self):
        f = QuantityFile.objects.create(
            project=self.project,
            discipline=self.discipline,
            file_name='test.xlsx',
            uploaded_by=self.user
        )
        self.assertEqual(f.version, 1)
        self.assertTrue(f.is_latest)

    def test_version_logic_manual(self):
        # Note: Model doesn't auto-increment version in save(), view does it.
        # But we can test default values.
        f1 = QuantityFile.objects.create(
            project=self.project,
            discipline=self.discipline,
            file_name='test.xlsx'
        )
        self.assertEqual(f1.version, 1)

class PriceAdjustmentTest(TestCase):
    def test_create(self):
        project = Project.objects.create(name='P', code='P')
        pa = PriceAdjustment.objects.create(
            project=project,
            item_code='I001',
            item_name='Item 1',
            original_price=100,
            adjusted_price=120,
            reason='Inflation'
        )
        self.assertEqual(pa.adjusted_price, 120)

class AuditLogTest(TestCase):
    def test_create(self):
        log = AuditLog.objects.create(
            action='CREATE',
            model_name='Project',
            object_id=1,
            detail={'a': 1}
        )
        self.assertEqual(log.action, 'CREATE')
