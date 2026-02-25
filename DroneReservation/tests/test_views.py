from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta
from DroneReservation.models import Announcement, DroneReviewer, DroneReservation

class BaseDroneTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.user = User.objects.create_user(username='user', password='password', email='user@example.com')
        self.reviewer_user = User.objects.create_user(username='reviewer', password='password', email='reviewer@example.com')
        self.other_user = User.objects.create_user(username='other', password='password')
        
        # Create reviewer profile
        self.reviewer_profile = DroneReviewer.objects.create(user=self.reviewer_user, is_active=True)
        
        # Create common reservation data
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=1, hours=10)
        self.end_time = self.now + timedelta(days=1, hours=12)

class DashboardViewTest(BaseDroneTest):
    def test_access_anonymous(self):
        url = reverse('drone:dashboard')
        response = self.client.get(url)
        self.assertRedirects(response, f'/accounts/login/?next={url}', fetch_redirect_response=False)

    def test_access_authenticated(self):
        self.client.login(username='user', password='password')
        response = self.client.get(reverse('drone:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'DroneReservation/dashboard.html')
        self.assertFalse(response.context['is_reviewer'])

    def test_access_reviewer(self):
        self.client.login(username='reviewer', password='password')
        response = self.client.get(reverse('drone:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_reviewer'])

class ReservationFlowTest(BaseDroneTest):
    def setUp(self):
        super().setUp()
        self.create_url = reverse('drone:reservation_create')
        self.success_url = reverse('drone:my_reservations')

    def test_create_reservation(self):
        self.client.login(username='user', password='password')
        
        data = {
            'phone_extension': '1234',
            'project_number': 'PROJ-001',
            'reason': 'Test reason',
            'usage_start_datetime': self.start_time.strftime('%Y-%m-%dT%H:%M'),
            'usage_end_datetime': self.end_time.strftime('%Y-%m-%dT%H:%M'),
            'location': 'Test Location',
            'notes': 'Notes'
        }
        
        with patch('DroneReservation.views.send_mail') as mock_mail:
            response = self.client.post(self.create_url, data)
            self.assertRedirects(response, self.success_url)
            
            # Check db
            self.assertEqual(DroneReservation.objects.count(), 1)
            reservation = DroneReservation.objects.first()
            self.assertEqual(reservation.applicant, self.user)
            self.assertEqual(reservation.status, 'pending')
            
            # Check email sent (notification to reviewers)
            self.assertTrue(mock_mail.called)
            # The recipient list is the 4th argument (index 3) or keyword argument
            # In current impl: recipient_list=reviewer_emails
            args, kwargs = mock_mail.call_args
            recipient_list = kwargs.get('recipient_list')
            self.assertIn(self.reviewer_user.email, recipient_list)

    def test_update_reservation(self):
        # Create initial reservation
        reservation = DroneReservation.objects.create(
            applicant=self.user,
            phone_extension='1234',
            project_number='PROJ-001',
            reason='Initial reason',
            usage_start_datetime=self.start_time,
            usage_end_datetime=self.end_time,
            location='Test Location',
            status='pending'
        )
        
        url = reverse('drone:reservation_update', args=[reservation.pk])
        self.client.login(username='user', password='password')
        
        # New data
        new_start = self.now + timedelta(days=2, hours=10)
        new_end = self.now + timedelta(days=2, hours=12)
        data = {
            'phone_extension': '5678',
            'project_number': 'PROJ-002',
            'reason': 'Updated reason',
            'usage_start_datetime': new_start.strftime('%Y-%m-%dT%H:%M'),
            'usage_end_datetime': new_end.strftime('%Y-%m-%dT%H:%M'),
            'location': 'Updated Location',
            'notes': 'Updated Notes'
        }
        
        response = self.client.post(url, data)
        self.assertRedirects(response, self.success_url)
        
        reservation.refresh_from_db()
        self.assertEqual(reservation.reason, 'Updated reason')
        self.assertEqual(reservation.phone_extension, '5678')

    def test_update_permission_denied(self):
        # Create reservation for user
        reservation = DroneReservation.objects.create(
            applicant=self.user,
            phone_extension='1234',
            project_number='PROJ-001',
            reason='Initial reason',
            usage_start_datetime=self.start_time,
            usage_end_datetime=self.end_time,
            location='Test Location',
            status='pending'
        )
        
        # Other user tries to update
        self.client.login(username='other', password='password')
        url = reverse('drone:reservation_update', args=[reservation.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404) # Or 403 depending on implementation, here queryset filter returns empty -> 404

    def test_cancel_reservation(self):
        reservation = DroneReservation.objects.create(
            applicant=self.user,
            phone_extension='1234',
            project_number='PROJ-001',
            reason='Reason',
            usage_start_datetime=self.start_time,
            usage_end_datetime=self.end_time,
            location='Location',
            status='pending'
        )
        
        url = reverse('drone:reservation_cancel', args=[reservation.pk])
        self.client.login(username='user', password='password')
        
        response = self.client.post(url)
        self.assertRedirects(response, self.success_url)
        
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, 'cancelled')

class ReviewerFlowTest(BaseDroneTest):
    def setUp(self):
        super().setUp()
        self.reservation = DroneReservation.objects.create(
            applicant=self.user,
            phone_extension='1234',
            project_number='PROJ-001',
            reason='Reason',
            usage_start_datetime=self.start_time,
            usage_end_datetime=self.end_time,
            location='Location',
            status='pending'
        )
        self.review_url = reverse('drone:review_reservation', args=[self.reservation.pk])
        self.pending_url = reverse('drone:pending_approvals')

    def test_reviewer_list(self):
        self.client.login(username='reviewer', password='password')
        response = self.client.get(self.pending_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.reservation.project_number)

    def test_approve_reservation(self):
        self.client.login(username='reviewer', password='password')
        
        data = {
            'action': 'approve',
            'rejection_reason': ''
        }
        
        with patch('DroneReservation.views.send_mail') as mock_mail:
            response = self.client.post(self.review_url, data)
            self.assertRedirects(response, self.pending_url)
            
            self.reservation.refresh_from_db()
            self.assertEqual(self.reservation.status, 'approved')
            self.assertEqual(self.reservation.reviewer, self.reviewer_user)
            
            # Check applicant notified
            self.assertTrue(mock_mail.called)
            args, kwargs = mock_mail.call_args
            recipient_list = kwargs.get('recipient_list')
            self.assertIn(self.user.email, recipient_list)

    def test_reject_reservation(self):
        self.client.login(username='reviewer', password='password')
        
        data = {
            'action': 'reject',
            'rejection_reason': 'Bad plan'
        }
        
        with patch('DroneReservation.views.send_mail') as mock_mail:
            response = self.client.post(self.review_url, data)
            self.assertRedirects(response, self.pending_url)
            
            self.reservation.refresh_from_db()
            self.assertEqual(self.reservation.status, 'rejected')
            self.assertEqual(self.reservation.rejection_reason, 'Bad plan')
            
            # Check applicant notified
            self.assertTrue(mock_mail.called)

    def test_non_reviewer_access_denied(self):
        self.client.login(username='user', password='password')
        response = self.client.get(self.pending_url)
        # Should redirect to dashboard with error message
        self.assertRedirects(response, reverse('drone:dashboard')) 
        # You might also check messages here if needed

    def test_approve_with_date_modification(self):
        """審核人核准時修改預約日期"""
        self.client.login(username='reviewer', password='password')
        
        new_start = (self.now + timedelta(days=5)).strftime('%Y-%m-%d')
        new_end = (self.now + timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = {
            'action': 'approve',
            'rejection_reason': '',
            'usage_start_datetime': new_start,
            'usage_end_datetime': new_end,
        }
        
        with patch('DroneReservation.views.send_mail') as mock_mail:
            response = self.client.post(self.review_url, data)
            self.assertRedirects(response, self.pending_url)
            
            self.reservation.refresh_from_db()
            self.assertEqual(self.reservation.status, 'approved')
            # 驗證日期已更新
            self.assertEqual(
                self.reservation.usage_start_datetime.strftime('%Y-%m-%d'),
                new_start
            )
            self.assertEqual(
                self.reservation.usage_end_datetime.strftime('%Y-%m-%d'),
                new_end
            )

    def test_approve_without_date_modification(self):
        """審核人核准時不修改日期"""
        self.client.login(username='reviewer', password='password')
        
        original_start = self.reservation.usage_start_datetime
        original_end = self.reservation.usage_end_datetime
        
        data = {
            'action': 'approve',
            'rejection_reason': '',
            'usage_start_datetime': original_start.strftime('%Y-%m-%d'),
            'usage_end_datetime': original_end.strftime('%Y-%m-%d'),
        }
        
        with patch('DroneReservation.views.send_mail') as mock_mail:
            response = self.client.post(self.review_url, data)
            self.assertRedirects(response, self.pending_url)
            
            self.reservation.refresh_from_db()
            self.assertEqual(self.reservation.status, 'approved')

    def test_approve_with_invalid_dates(self):
        """審核人核准時，結束日期早於開始日期應重導"""
        self.client.login(username='reviewer', password='password')
        
        data = {
            'action': 'approve',
            'rejection_reason': '',
            'usage_start_datetime': (self.now + timedelta(days=7)).strftime('%Y-%m-%d'),
            'usage_end_datetime': (self.now + timedelta(days=5)).strftime('%Y-%m-%d'),  # 結束 < 開始
        }
        
        response = self.client.post(self.review_url, data)
        detail_url = reverse('drone:reservation_detail', args=[self.reservation.pk])
        self.assertRedirects(response, detail_url)
        
        # 預約不應被核准
        self.reservation.refresh_from_db()
        self.assertEqual(self.reservation.status, 'pending')


class ReviewerUpdateFlowTest(BaseDroneTest):
    """測試審核人修改已核准預約時間（獨立頁面）"""
    
    def setUp(self):
        super().setUp()
        self.reservation = DroneReservation.objects.create(
            applicant=self.user,
            phone_extension='1234',
            project_number='PROJ-001',
            reason='Reason',
            usage_start_datetime=self.start_time,
            usage_end_datetime=self.end_time,
            location='Location',
            status='approved',
            reviewer=self.reviewer_user,
            review_datetime=timezone.now()
        )
        self.update_url = reverse('drone:reviewer_update', args=[self.reservation.pk])

    def test_reviewer_can_edit_approved(self):
        """審核人可編輯已核准預約的時間"""
        self.client.login(username='reviewer', password='password')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 200)

    def test_reviewer_cannot_edit_pending(self):
        """審核人不能透過修改時間頁面編輯申請中預約"""
        self.reservation.status = 'pending'
        self.reservation.save()
        
        self.client.login(username='reviewer', password='password')
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 404)

    def test_non_reviewer_cannot_edit(self):
        """非審核人不能編輯已核准預約"""
        self.client.login(username='user', password='password')
        response = self.client.get(self.update_url)
        # Should redirect (ReviewerRequiredMixin)
        self.assertRedirects(response, reverse('drone:dashboard'))

class AnnouncementFlowTest(BaseDroneTest):
    def setUp(self):
        super().setUp()
        self.list_url = reverse('drone:announcement_list')
        self.create_url = reverse('drone:announcement_create')

    def test_reviewer_can_create_announcement(self):
        self.client.login(username='reviewer', password='password')
        
        data = {
            'title': 'New Announcement',
            'content': 'Content',
            'is_pinned': False,
            'is_active': True
        }
        
        response = self.client.post(self.create_url, data)
        self.assertRedirects(response, self.list_url)
        self.assertEqual(Announcement.objects.count(), 1)
        
    def test_user_cannot_access_management(self):
        self.client.login(username='user', password='password')
        response = self.client.get(self.list_url)
        self.assertRedirects(response, reverse('drone:dashboard')) # ReviewerRequiredMixin redirects to dashboard
