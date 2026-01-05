from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from BudgetReview.models import Project, Discipline, Stage, QuantityFile, BudgetFile, FinalBudgetFile

class WorkspaceViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin', password='password')
        self.user = User.objects.create_user(username='user', password='password')
        
        self.project = Project.objects.create(name='P', code='P', created_by=self.admin)
        self.project.admins.add(self.admin)
        
        self.discipline = Discipline.objects.create(project=self.project, name='D1', code='01', responsible_user=self.user)
        self.stage = Stage.objects.create(project=self.project, name='S1', order=1)

    def test_workspace_access_permission(self):
        url = reverse('budget_review:project_workspace', kwargs={'project_id': self.project.id, 'stage_id': self.stage.id})
        
        # Admin can access
        self.client.login(username='admin', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Member (responsible_user) can access
        self.client.login(username='user', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Stranger cannot access
        stranger = User.objects.create_user(username='stranger', password='password')
        self.client.login(username='stranger', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_file_upload(self):
        self.client.login(username='user', password='password')
        url = reverse('budget_review:workspace_file_upload', kwargs={
            'project_id': self.project.id, 
            'stage_id': self.stage.id,
            'file_type': 'quantity'
        })
        
        f = SimpleUploadedFile("test_q.xlsx", b"content")
        data = {
            'discipline': self.discipline.id,
            'file': f,
            'description': 'desc'
        }
        response = self.client.post(url, data)
        self.assertTrue(response.json()['success'])
        self.assertTrue(QuantityFile.objects.filter(file_name='test_q.xlsx').exists())

    def test_file_submit(self):
        # Create a file
        f = QuantityFile.objects.create(
            project=self.project,
            discipline=self.discipline,
            stage=self.stage,
            file_name='test.xlsx',
            version=1,
            is_latest=True,
            is_submitted=False
        )
        
        self.client.login(username='user', password='password')
        url = reverse('budget_review:file_submit', kwargs={'file_type': 'quantity', 'file_id': f.id})
        
        response = self.client.post(url)
        self.assertTrue(response.json()['success'])
        f.refresh_from_db()
        self.assertTrue(f.is_submitted)

    def test_integration_area_access(self):
        url = reverse('budget_review:project_integration', kwargs={'project_id': self.project.id, 'stage_id': self.stage.id})
        
        # Admin can access
        self.client.login(username='admin', password='password')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
