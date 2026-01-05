from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from BudgetReview.models import Project, Stage, AuditLog

class StageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='password')
        self.project = Project.objects.create(name='P', code='P', created_by=self.admin)
        self.project.admins.add(self.admin)
        self.stage = Stage.objects.create(project=self.project, name='S1', order=1)

    def test_create_stage(self):
        self.client.login(username='admin', password='password')
        url = reverse('budget_review:stage_create', kwargs={'project_id': self.project.id})
        
        # Test GET (Ajax form)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('html', response.json())
        
        # Test POST
        data = {
            'name': 'Stage 2',
            'order': 2,
            'description': 'Desc'
        }
        response = self.client.post(url, data)
        self.assertTrue(response.json()['success'])
        self.assertTrue(Stage.objects.filter(name='Stage 2', project=self.project).exists())

    def test_update_stage(self):
        self.client.login(username='admin', password='password')
        url = reverse('budget_review:stage_update', kwargs={'project_id': self.project.id, 'pk': self.stage.pk})
        
        data = {
            'name': 'Stage Updated',
            'order': 1,
            'description': 'Updated'
        }
        response = self.client.post(url, data)
        self.assertTrue(response.json()['success'])
        self.stage.refresh_from_db()
        self.assertEqual(self.stage.name, 'Stage Updated')

    def test_delete_stage(self):
        self.client.login(username='admin', password='password')
        url = reverse('budget_review:stage_delete', kwargs={'project_id': self.project.id, 'pk': self.stage.pk})
        response = self.client.post(url)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Stage.objects.filter(pk=self.stage.pk).exists())
