from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from DroneReservation.forms import ReservationForm, ReviewForm

class ReservationFormTest(TestCase):
    def test_valid_form(self):
        now = timezone.now()
        start = now + timedelta(days=1, hours=10)
        end = now + timedelta(days=1, hours=12)
        
        data = {
            'phone_extension': '1234',
            'project_number': 'PROJ-001',
            'reason': 'Test reason',
            'usage_start_datetime': start,
            'usage_end_datetime': end,
            'location': 'Test Location',
            'notes': 'Some notes'
        }
        form = ReservationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_end_time_before_start_time(self):
        now = timezone.now()
        start = now + timedelta(days=1, hours=12)
        end = now + timedelta(days=1, hours=10)  # End before start
        
        data = {
            'phone_extension': '1234',
            'project_number': 'PROJ-001',
            'reason': 'Test reason',
            'usage_start_datetime': start,
            'usage_end_datetime': end,
            'location': 'Test Location'
        }
        form = ReservationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('結束時間必須在開始時間之後', form.errors['__all__'])

    def test_start_time_in_past(self):
        now = timezone.now()
        start = now - timedelta(hours=1)  # Past time
        end = now + timedelta(hours=1)
        
        data = {
            'phone_extension': '1234',
            'project_number': 'PROJ-001',
            'reason': 'Test reason',
            'usage_start_datetime': start,
            'usage_end_datetime': end,
            'location': 'Test Location'
        }
        form = ReservationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('開始時間不能是過去的時間', form.errors['__all__'])

class ReviewFormTest(TestCase):
    def test_approve_valid(self):
        data = {
            'action': 'approve',
            'rejection_reason': ''
        }
        form = ReviewForm(data=data)
        self.assertTrue(form.is_valid())

    def test_reject_valid(self):
        data = {
            'action': 'reject',
            'rejection_reason': 'Some reason'
        }
        form = ReviewForm(data=data)
        self.assertTrue(form.is_valid())

    def test_reject_missing_reason(self):
        data = {
            'action': 'reject',
            'rejection_reason': ''  # Missing reason
        }
        form = ReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rejection_reason', form.errors)
