from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from DroneReservation.models import Announcement, DroneReviewer, DroneReservation
from datetime import timedelta

class AnnouncementModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.announcement = Announcement.objects.create(
            title="Test Announcement",
            content="Test Content",
            created_by=self.user,
            is_pinned=False
        )
        self.pinned_announcement = Announcement.objects.create(
            title="Pinned Announcement",
            content="Pinned Content",
            created_by=self.user,
            is_pinned=True
        )

    def test_string_representation(self):
        self.assertEqual(str(self.announcement), "Test Announcement")

    def test_ordering(self):
        """Test that pinned announcements come first"""
        announcements = Announcement.objects.all()
        self.assertEqual(announcements[0], self.pinned_announcement)
        self.assertEqual(announcements[1], self.announcement)

class DroneReviewerModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reviewer', password='password')
        self.reviewer = DroneReviewer.objects.create(user=self.user)

    def test_string_representation(self):
        # Should return username if full name is empty
        self.assertEqual(str(self.reviewer), 'reviewer')
        
        # Should return full name if set
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()
        self.assertEqual(str(self.reviewer), 'John Doe')

class DroneReservationModelTest(TestCase):
    def setUp(self):
        self.applicant = User.objects.create_user(username='applicant', password='password')
        self.reviewer_user = User.objects.create_user(username='reviewer', password='password')
        self.reviewer_profile = DroneReviewer.objects.create(user=self.reviewer_user, is_active=True)
        
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=1, hours=10)
        self.end_time = self.now + timedelta(days=1, hours=12)
        
        self.reservation = DroneReservation.objects.create(
            applicant=self.applicant,
            phone_extension='1234',
            project_number='PROJ-001',
            reason='Test reason',
            usage_start_datetime=self.start_time,
            usage_end_datetime=self.end_time,
            location='Test Location'
        )

    def test_string_representation(self):
        expected_str = f"{self.applicant.username} - {self.start_time.strftime('%Y/%m/%d %H:%M')}"
        self.assertEqual(str(self.reservation), expected_str)

    def test_get_status_display_class(self):
        self.reservation.status = 'pending'
        self.assertEqual(self.reservation.get_status_display_class(), 'status-pending')
        
        self.reservation.status = 'approved'
        self.assertEqual(self.reservation.get_status_display_class(), 'status-approved')
        
        self.reservation.status = 'rejected'
        self.assertEqual(self.reservation.get_status_display_class(), 'status-rejected')
        
        self.reservation.status = 'cancelled'
        self.assertEqual(self.reservation.get_status_display_class(), 'status-cancelled')

    def test_can_edit(self):
        # Applicant can edit pending reservation
        self.assertTrue(self.reservation.can_edit(self.applicant))
        
        # Cannot edit if status is not pending
        self.reservation.status = 'approved'
        self.assertFalse(self.reservation.can_edit(self.applicant))
        
        # Others cannot edit
        self.reservation.status = 'pending'
        other_user = User.objects.create_user(username='other', password='password')
        self.assertFalse(self.reservation.can_edit(other_user))

    def test_can_cancel(self):
        # Applicant can cancel pending reservation
        self.assertTrue(self.reservation.can_cancel(self.applicant))
        
        # Applicant can cancel approved reservation
        self.reservation.status = 'approved'
        self.assertTrue(self.reservation.can_cancel(self.applicant))
        
        # Cannot cancel rejected/cancelled reservation
        self.reservation.status = 'rejected'
        self.assertFalse(self.reservation.can_cancel(self.applicant))
        
        # Others cannot cancel
        self.reservation.status = 'pending'
        other_user = User.objects.create_user(username='other', password='password')
        self.assertFalse(self.reservation.can_cancel(other_user))

    def test_can_review(self):
        # Reviewer can review pending reservation
        self.assertTrue(self.reservation.can_review(self.reviewer_user))
        
        # Cannot review if not pending
        self.reservation.status = 'approved'
        self.assertFalse(self.reservation.can_review(self.reviewer_user))
        
        # Inactive reviewer cannot review
        self.reservation.status = 'pending'
        self.reviewer_profile.is_active = False
        self.reviewer_profile.save()
        self.assertFalse(self.reservation.can_review(self.reviewer_user))
        
        # Non-reviewer cannot review
        self.assertFalse(self.reservation.can_review(self.applicant))

    def test_can_reviewer_edit(self):
        """審核人只能編輯已核准預約的時間"""
        # 申請中預約 - 不能透過修改時間編輯
        self.reservation.status = 'pending'
        self.assertFalse(self.reservation.can_reviewer_edit(self.reviewer_user))
        
        # 已核准預約 - 審核人可以編輯時間
        self.reservation.status = 'approved'
        self.assertTrue(self.reservation.can_reviewer_edit(self.reviewer_user))
        
        # 已拒絕預約 - 不能編輯
        self.reservation.status = 'rejected'
        self.assertFalse(self.reservation.can_reviewer_edit(self.reviewer_user))
        
        # 已取消預約 - 不能編輯
        self.reservation.status = 'cancelled'
        self.assertFalse(self.reservation.can_reviewer_edit(self.reviewer_user))
        
        # 非審核人不能編輯
        self.reservation.status = 'approved'
        self.assertFalse(self.reservation.can_reviewer_edit(self.applicant))
        
        # 停用的審核人不能編輯
        self.reviewer_profile.is_active = False
        self.reviewer_profile.save()
        self.assertFalse(self.reservation.can_reviewer_edit(self.reviewer_user))
