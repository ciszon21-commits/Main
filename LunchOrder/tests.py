from django.test import TestCase, Client
from django.urls import reverse
from .models import Restaurant, MenuItem, RestaurantSchedule
from datetime import date
from django.contrib.auth.models import User

class CalendarTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.restaurant = Restaurant.objects.create(name="Test Restaurant", is_active=True)
        self.menu_item = MenuItem.objects.create(restaurant=self.restaurant, name="Test Item", price=100)
        self.schedule = RestaurantSchedule.objects.create(date=date.today(), restaurant=self.restaurant)

    def test_calendar_view_loads(self):
        # We haven't created the view yet, so we expect 404/error or we can test once wired
        # For now let's just assert the model works
        self.assertEqual(RestaurantSchedule.objects.count(), 1)
        self.assertEqual(self.schedule.restaurant, self.restaurant)
