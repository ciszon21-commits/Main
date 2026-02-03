from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field


class Announcement(models.Model):
    """公告模型"""
    title = models.CharField(max_length=200, verbose_name="標題")
    content = CKEditor5Field(verbose_name="內容", config_name='extends', blank=True)
    is_pinned = models.BooleanField(default=False, verbose_name="置頂")
    is_active = models.BooleanField(default=True, verbose_name="啟用")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drone_announcements',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "公告"
        verbose_name_plural = "公告"
        ordering = ['-is_pinned', '-updated_at']

    def __str__(self):
        return self.title


class SiteSettings(models.Model):
    """網站設定（單例模式）"""
    banner_subtitle = models.CharField(
        max_length=200, 
        default="園區無人機使用預約系統",
        verbose_name="Banner 副標題"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="最後更新者"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "網站設定"
        verbose_name_plural = "網站設定"

    def __str__(self):
        return "網站設定"

    @classmethod
    def get_settings(cls):
        """取得或建立設定（單例）"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class DroneReviewer(models.Model):
    """無人機簽核人（飛手）設定"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='drone_reviewer_profile',
        verbose_name="使用者"
    )
    is_active = models.BooleanField(default=True, verbose_name="啟用")
    receive_email = models.BooleanField(default=True, verbose_name="接收郵件通知")
    can_manage_reviewers = models.BooleanField(default=False, verbose_name="可管理簽核人")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "簽核人（飛手）"
        verbose_name_plural = "簽核人（飛手）"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class DroneReservation(models.Model):
    """無人機預約申請模型"""
    STATUS_CHOICES = [
        ('pending', '申請中'),
        ('approved', '已核准'),
        ('rejected', '已拒絕'),
        ('cancelled', '已取消'),
    ]

    # 申請人資訊
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='drone_reservations',
        verbose_name="申請人"
    )
    phone_extension = models.CharField(max_length=20, verbose_name="分機")
    project_number = models.CharField(max_length=100, verbose_name="計畫編號")

    # 申請內容
    reason = models.TextField(verbose_name="申請理由")
    usage_start_datetime = models.DateTimeField(verbose_name="使用開始時間")
    usage_end_datetime = models.DateTimeField(verbose_name="使用結束時間")
    location = models.CharField(max_length=200, verbose_name="地點")
    notes = models.TextField(blank=True, verbose_name="其他說明")

    # 簽核資訊
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="狀態"
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_drone_reservations',
        verbose_name="簽核人"
    )
    review_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="簽核時間"
    )
    rejection_reason = models.TextField(blank=True, verbose_name="拒絕理由")
    cancellation_reason = models.TextField(blank=True, verbose_name="取消理由")

    # 時間戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "無人機預約"
        verbose_name_plural = "無人機預約"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.applicant.get_full_name() or self.applicant.username} - {self.usage_start_datetime.strftime('%Y/%m/%d %H:%M')}"

    def get_status_display_class(self):
        """取得狀態對應的 CSS class"""
        status_classes = {
            'pending': 'status-pending',
            'approved': 'status-approved',
            'rejected': 'status-rejected',
            'cancelled': 'status-cancelled',
        }
        return status_classes.get(self.status, '')

    def can_edit(self, user):
        """檢查使用者是否可以編輯此預約"""
        # 申請人只能在申請中狀態下編輯（已核准後只有審核人可修改時間）
        return user == self.applicant and self.status == 'pending'

    def can_cancel(self, user):
        """檢查使用者是否可以取消此預約"""
        # 只有申請人且狀態為申請中或已核准時可以取消
        return user == self.applicant and self.status in ['pending', 'approved']

    def can_reviewer_cancel(self, user):
        """檢查簽核人是否可以取消已核准的預約"""
        if self.status != 'approved':
            return False
        try:
            reviewer_profile = user.drone_reviewer_profile
            return reviewer_profile.is_active
        except DroneReviewer.DoesNotExist:
            return False

    def can_reviewer_edit(self, user):
        """檢查審核人是否可以編輯已核准預約的時間"""
        if self.status != 'approved':
            return False
        try:
            reviewer_profile = user.drone_reviewer_profile
            return reviewer_profile.is_active
        except DroneReviewer.DoesNotExist:
            return False

    def can_review(self, user):
        """檢查使用者是否可以簽核此預約"""
        # 只有簽核人且狀態為申請中時可以簽核
        if self.status != 'pending':
            return False
        try:
            reviewer_profile = user.drone_reviewer_profile
            return reviewer_profile.is_active
        except DroneReviewer.DoesNotExist:
            return False
