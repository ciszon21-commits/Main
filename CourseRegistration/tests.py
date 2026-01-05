from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Course, Registration, PDFDownloadLog, CourseComment
from .forms import CourseForm, CommentForm
import tempfile
from django.test import override_settings

User = get_user_model()

class CourseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        now = timezone.now()
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            course_datetime=now + timedelta(days=5),
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=4),
            created_by=self.user,
            max_participants=2
        )

    def test_string_representation(self):
        self.assertEqual(str(self.course), 'Test Course')

    def test_get_absolute_url(self):
        self.assertEqual(self.course.get_absolute_url(), reverse('courses:course_detail', kwargs={'pk': self.course.pk}))

    def test_current_participants_count(self):
        self.assertEqual(self.course.current_participants_count, 0)
        Registration.objects.create(course=self.course, user=self.user)
        self.assertEqual(self.course.current_participants_count, 1)

    def test_is_registration_open(self):
        self.assertTrue(self.course.is_registration_open)
        # Test closed scenario
        self.course.registration_end = timezone.now() - timedelta(days=1)
        self.course.save()
        self.assertFalse(self.course.is_registration_open)

    def test_is_full(self):
        self.assertFalse(self.course.is_full)
        user2 = User.objects.create_user(username='testuser2', password='password')
        Registration.objects.create(course=self.course, user=self.user)
        Registration.objects.create(course=self.course, user=user2)
        self.assertTrue(self.course.is_full)

    def test_can_register(self):
        self.assertTrue(self.course.can_register)
        
        # Test full
        user2 = User.objects.create_user(username='testuser2', password='password')
        Registration.objects.create(course=self.course, user=self.user)
        Registration.objects.create(course=self.course, user=user2)
        self.assertFalse(self.course.can_register)

    def test_registration_status(self):
        self.assertEqual(self.course.registration_status, 'open')
        
        # Upcoming
        self.course.registration_start = timezone.now() + timedelta(days=1)
        self.course.registration_end = timezone.now() + timedelta(days=2)
        self.course.course_datetime = timezone.now() + timedelta(days=3)
        self.assertEqual(self.course.registration_status, 'upcoming')
        
        # Closed
        self.course.registration_start = timezone.now() - timedelta(days=5)
        self.course.registration_end = timezone.now() - timedelta(days=1)
        self.course.course_datetime = timezone.now() + timedelta(days=3)
        self.assertEqual(self.course.registration_status, 'closed')

    def test_clean_validation(self):
        # End before start
        self.course.registration_start = timezone.now()
        self.course.registration_end = timezone.now() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.course.clean()
            
        # Course date before registration start
        self.course.registration_end = timezone.now() + timedelta(days=1)
        self.course.course_datetime = timezone.now() - timedelta(days=1)
        self.course.registration_start = timezone.now()
        with self.assertRaises(ValidationError):
            self.course.clean()

class RegistrationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        now = timezone.now()
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            course_datetime=now + timedelta(days=5),
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=4),
            created_by=self.user,
        )

    def test_registration_creation(self):
        registration = Registration.objects.create(course=self.course, user=self.user)
        self.assertEqual(str(registration), f'{self.user.get_full_name()} - {self.course.title}')

    def test_unique_together(self):
        Registration.objects.create(course=self.course, user=self.user)
        with self.assertRaises(Exception): # Filter by generic exception as db integrity error might vary
            Registration.objects.create(course=self.course, user=self.user)

class CourseFormTest(TestCase):
    def test_valid_course_form(self):
        now = timezone.now()
        data = {
            'title': 'Test Course',
            'description': 'Description',
            'course_datetime': now + timedelta(days=10),
            'registration_start': now + timedelta(days=1),
            'registration_end': now + timedelta(days=5),
        }
        form = CourseForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_dates_course_form(self):
        now = timezone.now()
        data = {
            'title': 'Test Course',
            'description': 'Description',
            'course_datetime': now + timedelta(days=10),
            'registration_start': now + timedelta(days=5),
            'registration_end': now + timedelta(days=1), # End before start
        }
        form = CourseForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('報名截止時間必須晚於報名開始時間', form.non_field_errors())

@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class CourseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.other_user = User.objects.create_user(username='otheruser', password='password')
        
        now = timezone.now()
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            course_datetime=now + timedelta(days=5),
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=4),
            created_by=self.user,
            max_participants=2
        )
        self.pdf_course = Course.objects.create(
            title='PDF Course',
            description='PDF Description',
            course_datetime=now + timedelta(days=5),
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=4),
            created_by=self.user,
            pdf_file=SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        )

    def test_course_list_view(self):
        # self.client.force_login(self.user)
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('courses:course_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        
    def test_course_list_filter(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('courses:course_list'), {'filter': 'open'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Course')
        
        # Make course upcoming
        self.course.registration_start = timezone.now() + timedelta(days=1)
        self.course.save()
        response = self.client.get(reverse('courses:course_list'), {'filter': 'upcoming'})
        self.assertContains(response, 'Test Course')

    def test_course_detail_view(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('courses:course_detail', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['is_creator'], True)
        self.assertEqual(response.context['is_registered'], False)

    def test_course_create_view(self):
        self.client.login(username='testuser', password='password')
        now = timezone.now()
        data = {
            'title': 'New Course',
            'description': 'New Description',
            'course_datetime': (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M'),
            'registration_start': (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
            'registration_end': (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M'),
        }
        # Create view redirects on success
        response = self.client.post(reverse('courses:course_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(title='New Course').exists())

    def test_course_update_view(self):
        self.client.login(username='testuser', password='password')
        now = timezone.now()
        data = {
            'title': 'Updated Course',
            'description': self.course.description,
            'course_datetime': (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M'),
            'registration_start': (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
            'registration_end': (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M'),
        }
        response = self.client.post(reverse('courses:course_update', kwargs={'pk': self.course.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Updated Course')

    def test_course_delete_view(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('courses:course_delete', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())

    def test_register_course(self):
        self.client.login(username='otheruser', password='password')
        response = self.client.post(reverse('courses:register_course', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(Registration.objects.filter(course=self.course, user=self.other_user).exists())

        # Test double registration
        response = self.client.post(reverse('courses:register_course', kwargs={'pk': self.course.pk}))
        self.assertFalse(response.json()['success'])

    def test_cancel_registration(self):
        Registration.objects.create(course=self.course, user=self.other_user)
        self.client.login(username='otheruser', password='password')
        
        response = self.client.post(reverse('courses:cancel_registration', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(Registration.objects.filter(course=self.course, user=self.other_user).exists())

    def test_add_comment(self):
        self.client.login(username='otheruser', password='password')
        data = {'content': 'Nice course!'}
        response = self.client.post(reverse('courses:add_comment', kwargs={'pk': self.course.pk}), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(CourseComment.objects.filter(course=self.course, content='Nice course!').exists())

    def test_download_pdf(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('courses:download_pdf', kwargs={'pk': self.pdf_course.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PDFDownloadLog.objects.filter(course=self.pdf_course, user=self.user).exists())

        # Test no PDF
        response = self.client.get(reverse('courses:download_pdf', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 404)

    def test_registration_list_view(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('courses:registration_list', kwargs={'pk': self.course.pk}))
        self.assertEqual(response.status_code, 200)
