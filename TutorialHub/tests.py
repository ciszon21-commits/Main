from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Tutorial, TutorialStep, StepSnippet, TutorialMaintainer, Question, Answer
from .forms import TutorialForm
import json

class TutorialModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.tutorial = Tutorial.objects.create(
            title='Test Tutorial',
            description='Test Description',
            is_published=True
        )

    def test_slug_generation(self):
        self.assertEqual(self.tutorial.slug, 'test-tutorial')
        
    def test_tutorial_maintainer_creation(self):
        maintainer = TutorialMaintainer.objects.create(
            tutorial=self.tutorial,
            user=self.user,
            role='creator'
        )
        self.assertEqual(str(maintainer), f'testuser - Test Tutorial (創建者)')

    def test_answer_maintainer_detection(self):
        # Create steps and question
        step = TutorialStep.objects.create(tutorial=self.tutorial, title="Step 1")
        question = Question.objects.create(step=step, user=self.user, content="Help?")
        
        # Non-maintainer answer
        answer1 = Answer.objects.create(question=question, user=self.user, content="No")
        self.assertFalse(answer1.is_from_maintainer)
        
        # Add as maintainer
        TutorialMaintainer.objects.create(tutorial=self.tutorial, user=self.user, role='maintainer')
        
        # Maintainer answer
        answer2 = Answer.objects.create(question=question, user=self.user, content="Yes")
        self.assertTrue(answer2.is_from_maintainer)

class TutorialViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='creator', password='password')
        self.user2 = User.objects.create_user(username='other', password='password')
        self.client.login(username='creator', password='password')
        
        self.tutorial = Tutorial.objects.create(
            title='My Tutorial',
            description='Desc',
            is_published=True
        )
        TutorialMaintainer.objects.create(
            tutorial=self.tutorial,
            user=self.user,
            role='creator'
        )

    def test_tutorial_list_view(self):
        response = self.client.get(reverse('tutorialhub:tutorial_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Tutorial')

    def test_tutorial_create_view(self):
        response = self.client.post(reverse('tutorialhub:tutorial_create'), {
            'title': 'New Tutorial',
            'description': 'New Desc',
            'is_published': 'on'
        })
        self.assertEqual(response.status_code, 302) # Redirects to edit steps
        self.assertTrue(Tutorial.objects.filter(title='New Tutorial').exists())
        # Check if creator is added
        new_tutorial = Tutorial.objects.get(title='New Tutorial')
        self.assertTrue(new_tutorial.maintainers.filter(user=self.user, role='creator').exists())

    def test_permission_enforcement(self):
        # Login as non-maintainer
        self.client.login(username='other', password='password')
        
        # Try to edit steps
        response = self.client.get(reverse('tutorialhub:tutorial_edit_steps', kwargs={'slug': self.tutorial.slug}))
        self.assertEqual(response.status_code, 302) # Redirects to detail page with error message
        
    def test_ajax_add_step(self):
        url = reverse('tutorialhub:add_step', kwargs={'slug': self.tutorial.slug})
        response = self.client.post(url, {'title': 'New Step'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(TutorialStep.objects.filter(title='New Step').exists())

    def test_contributors_management(self):
        # Test add contributor
        url = reverse('tutorialhub:add_contributor', kwargs={'slug': self.tutorial.slug})
        response = self.client.post(url, {'username': 'other'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.tutorial.maintainers.filter(user=self.user2).exists())
        
        # Test remove contributor
        url_remove = reverse('tutorialhub:remove_contributor', kwargs={'slug': self.tutorial.slug, 'user_id': self.user2.id})
        response = self.client.post(url_remove)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.tutorial.maintainers.filter(user=self.user2).exists())

class TutorialFormTest(TestCase):
    def test_tutorial_form_valid(self):
        form = TutorialForm(data={
            'title': 'Test Title',
            'description': 'Test Desc',
            'is_published': True
        })
        self.assertTrue(form.is_valid())

    def test_tutorial_form_invalid(self):
        form = TutorialForm(data={})
        self.assertFalse(form.is_valid())
