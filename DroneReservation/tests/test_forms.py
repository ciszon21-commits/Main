from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from DroneReservation.forms import ReservationForm, ReviewForm, ReviewerTimeEditForm

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


class ReviewerTimeEditFormTest(TestCase):
    """測試審核人時間編輯表單"""

    def test_valid_dates(self):
        """有效的日期範圍"""
        now = timezone.now()
        data = {
            'usage_start_datetime': (now + timedelta(days=1)).strftime('%Y-%m-%d'),
            'usage_end_datetime': (now + timedelta(days=3)).strftime('%Y-%m-%d'),
        }
        form = ReviewerTimeEditForm(data=data)
        self.assertTrue(form.is_valid())

    def test_same_day(self):
        """開始與結束同一天也是有效的"""
        now = timezone.now()
        same_day = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        data = {
            'usage_start_datetime': same_day,
            'usage_end_datetime': same_day,
        }
        form = ReviewerTimeEditForm(data=data)
        self.assertTrue(form.is_valid())

    def test_end_before_start(self):
        """結束日期早於開始日期應無效"""
        now = timezone.now()
        data = {
            'usage_start_datetime': (now + timedelta(days=5)).strftime('%Y-%m-%d'),
            'usage_end_datetime': (now + timedelta(days=2)).strftime('%Y-%m-%d'),
        }
        form = ReviewerTimeEditForm(data=data)
        self.assertFalse(form.is_valid())
