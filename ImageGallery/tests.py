from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Image, ImageCategory, ImageRating
from .forms import ImageUploadForm, CategoryForm
import datetime
import tempfile
import shutil

class ImageCategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = ImageCategory.objects.create(name='Test Category', created_by=self.user)

    def test_category_string_representation(self):
        self.assertEqual(str(self.category), 'Test Category')

    def test_category_creation(self):
        self.assertTrue(isinstance(self.category, ImageCategory))
        self.assertEqual(self.category.name, 'Test Category')

class ImageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = ImageCategory.objects.create(name='Test Category', created_by=self.user)
        
        # Create a dummy image file
        self.image_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        self.image = Image.objects.create(
            title='Test Image',
            image=self.image_file,
            uploaded_by=self.user,
            category=self.category
        )

    def tearDown(self):
        # Clean up uploaded files
        try:
            self.image.image.delete()
        except:
            pass

    def test_image_string_representation(self):
        self.assertEqual(str(self.image), 'Test Image')

    def test_increment_view_count(self):
        initial_count = self.image.view_count
        self.image.increment_view_count()
        self.image.refresh_from_db()
        self.assertEqual(self.image.view_count, initial_count + 1)

    def test_rating_properties_and_methods(self):
        # Create ratings
        user2 = User.objects.create_user(username='user2', password='password')
        ImageRating.objects.create(image=self.image, user=self.user, rating=4)
        ImageRating.objects.create(image=self.image, user=user2, rating=5)

        # Test average_rating
        self.assertEqual(self.image.average_rating, 4.5)

        # Test total_ratings
        self.assertEqual(self.image.total_ratings, 2)

        # Test get_rating_distribution
        dist = self.image.get_rating_distribution()
        self.assertEqual(dist[4]['count'], 1)
        self.assertEqual(dist[5]['count'], 1)
        self.assertEqual(dist[1]['count'], 0)
        self.assertEqual(dist[4]['percentage'], 50.0)

class ImageRatingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = ImageCategory.objects.create(name='Test Category')
        self.image = Image.objects.create(
            title='Test Image',
            image=SimpleUploadedFile('test.jpg', b'content'),
            uploaded_by=self.user,
            category=self.category
        )

    def test_rating_creation(self):
        rating = ImageRating.objects.create(image=self.image, user=self.user, rating=5)
        self.assertEqual(str(rating), f'{self.user.get_full_name} - {self.image.title} - 5星')

    def test_rating_validators(self):
        # Validating constraints usually requires full_clean()
        rating_high = ImageRating(image=self.image, user=self.user, rating=6)
        with self.assertRaises(ValidationError):
            rating_high.full_clean()
        
        rating_low = ImageRating(image=self.image, user=self.user, rating=0)
        with self.assertRaises(ValidationError):
            rating_low.full_clean()

class FormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = ImageCategory.objects.create(name='Test Category')

    def test_category_form_valid(self):
        form = CategoryForm(data={'name': 'New Category'})
        self.assertTrue(form.is_valid())

    def test_category_form_duplicate(self):
        form = CategoryForm(data={'name': 'Test Category'})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_image_upload_form_valid(self):
        image_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        data = {
            'title': 'Test Image',
            'category': self.category.id,
        }
        files = {'image': image_file}
        form = ImageUploadForm(data=data, files=files)
        self.assertTrue(form.is_valid())

class ViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = ImageCategory.objects.create(name='Cat1')
        
        self.image_file = SimpleUploadedFile(
            name='test.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        self.image = Image.objects.create(
            title='Test Image', 
            description='Desc', 
            image=self.image_file, 
            uploaded_by=self.user,
            category=self.category,
            view_count=5
        )
        self.url_list = reverse('gallery:list')
        self.url_detail = reverse('gallery:detail', args=[self.image.pk])
        self.url_upload = reverse('gallery:upload')
        self.url_rate = reverse('gallery:rate', args=[self.image.pk])

    def tearDown(self):
        try:
            self.image.image.delete()
        except:
            pass

    def test_gallery_list_view(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Image')
        
        # Test filters
        response = self.client.get(self.url_list, {'category': self.category.id})
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(self.url_list, {'search': 'Desc'})
        self.assertEqual(response.status_code, 200)
        
        # Test sort
        response = self.client.get(self.url_list, {'sort': 'popular'})
        self.assertEqual(response.status_code, 200)

    def test_gallery_detail_view(self):
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Image')
        
        # Verify view count increment
        self.image.refresh_from_db()
        self.assertEqual(self.image.view_count, 6)

    def test_gallery_upload_view(self):
        # Redirect if not logged in
        response = self.client.get(self.url_upload)
        self.assertEqual(response.status_code, 302)
        
        # self.client.force_login(self.user)
        self.client.login(username='testuser', password='password')
        response = self.client.get(self.url_upload)
        self.assertEqual(response.status_code, 200)
        
        # Test upload
        img_file = SimpleUploadedFile(
            name='new.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
            content_type='image/jpeg'
        )
        data = {
            'title': 'New Upload',
            'category': self.category.id
        }
        files = {'image': img_file}
        response = self.client.post(self.url_upload, data, format='multipart') # files arg is not directly for post, mix in data
        
        # Correct way to send files in test client
        response = self.client.post(self.url_upload, {'title': 'New', 'category': self.category.id, 'image': img_file})
        self.assertEqual(response.status_code, 302) # Redirects to detail
        self.assertTrue(Image.objects.filter(title='New').exists())

    def test_rate_api(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(self.url_rate, {'rating': 5})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertEqual(response.json()['user_rating'], 5)
        
        # Invalid rating
        response = self.client.post(self.url_rate, {'rating': 10})
        self.assertEqual(response.status_code, 400)

    def test_leaderboard_view(self):
        url = reverse('gallery:leaderboard_all')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url_week = reverse('gallery:leaderboard', args=['week'])
        response = self.client.get(url_week)
        self.assertEqual(response.status_code, 200)

    def test_category_manage(self):
        self.client.login(username='testuser', password='password')
        url = reverse('gallery:category_manage')
        
        # Get
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Post
        response = self.client.post(url, {'name': 'New Cat'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ImageCategory.objects.filter(name='New Cat').exists())

    def test_gallery_edit(self):
        self.client.login(username='testuser', password='password')
        url = reverse('gallery:edit', args=[self.image.pk])
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(url, {
            'title': 'Updated Title',
            'category': self.category.id,
            'description': 'Updated Desc'
        })
        self.assertEqual(response.status_code, 302)
        self.image.refresh_from_db()
        self.assertEqual(self.image.title, 'Updated Title')
        
        # Test permission (other user)
        other_user = User.objects.create_user(username='other', password='pw')
        self.client.force_login(other_user)
        response = self.client.get(url)
        # Should redirect back to detail with error message (implementation details vary but likely 302)
        self.assertEqual(response.status_code, 302)
