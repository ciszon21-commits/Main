from django.test import TestCase
from django.contrib.auth.models import User
from BudgetReview.forms import ProjectForm, DisciplineForm, OverallDisciplineForm, FileUploadForm, PriceAdjustmentForm
from BudgetReview.stage_forms import StageForm
from BudgetReview.models import Project, Discipline, Stage
from django.utils import timezone
import datetime

class ProjectFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_valid_form(self):
        data = {
            'name': 'Test Project',
            'code': 'TP001',
            'description': 'Desc',
            'status': 'PREPARING',
            'admins': [self.user.id]
        }
        form = ProjectForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        data = {
            'name': '', # Required
            'code': 'TP001'
        }
        form = ProjectForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

class DisciplineFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='p1')
        self.project = Project.objects.create(name='P', code='P')

    def test_valid_form(self):
        data = {
            'name': 'Disc 1',
            'code': '01',
            'responsible_user': self.user.id,
            'members': [self.user.id],
            'budget_members': []
        }
        form = DisciplineForm(data=data)
        self.assertTrue(form.is_valid())

class OverallDisciplineFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='p1')

    def test_fields(self):
        # OverallDisciplineForm only has 'budget_manager', 'budget_members'
        form = OverallDisciplineForm()
        self.assertEqual(list(form.fields.keys()), ['budget_manager', 'budget_members'])

class StageFormTest(TestCase):
    def test_datetime_formatting(self):
        # Create a stage with a deadline
        project = Project.objects.create(name='P', code='P')
        deadline = timezone.now()
        stage = Stage.objects.create(
            project=project, name='S1', order=1, deadline=deadline
        )
        
        # Init form with instance
        form = StageForm(instance=stage)
        # Check if initial deadline is string formatted
        self.assertTrue(isinstance(form.initial.get('deadline'), str))

class FileUploadFormTest(TestCase):
    def test_valid(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile("file.txt", b"content")
        data = {'description': 'desc'}
        files = {'file': f}
        form = FileUploadForm(data=data, files=files)
        self.assertTrue(form.is_valid())

class PriceAdjustmentFormTest(TestCase):
    def test_valid(self):
        data = {
            'item_code': 'I1',
            'item_name': 'Iname',
            'original_price': 100,
            'adjusted_price': 120,
            'reason': 'Because'
        }
        form = PriceAdjustmentForm(data=data)
        # Discipline is optional in model (null=True) but let's check if form requires it?
        # Model: discipline = models.ForeignKey(..., null=True, blank=True)
        # Form fields includes 'discipline'. If not provided, should be valid as it's blank=True
        self.assertTrue(form.is_valid())
