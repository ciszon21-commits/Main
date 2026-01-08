"""
EVCodeSigning Models - 簽章管理資料模型
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .validators import validate_signing_file
from SinoFile.fields import SinoFileField
import uuid
import os


def signing_file_upload_path(instance, filename):
    """產生上傳檔案路徑"""
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"ev_signing/original/{instance.request.id}/{unique_name}"


def signed_file_upload_path(instance, filename):
    """產生簽章後檔案路徑"""
    ext = os.path.splitext(filename)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return f"ev_signing/signed/{instance.request.id}/{unique_name}"


class SigningAdmin(models.Model):
    """
    簽章管理員
    由 superuser 設定，負責處理簽章申請
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='signing_admin_profile',
        verbose_name="使用者"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="是否啟用",
        help_text="停用後將不再收到新申請通知"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="建立時間"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_signing_admins',
        verbose_name="設定者"
    )

    class Meta:
        verbose_name = "簽章管理員"
        verbose_name_plural = "簽章管理員"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"


class SigningRequest(models.Model):
    """
    簽章申請
    使用者提交的簽章需求
    """
    STATUS_CHOICES = [
        ('pending', '待處理'),
        ('processing', '處理中'),
        ('completed', '已完成'),
        ('rejected', '已退回'),
    ]

    # 申請資訊
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='signing_requests',
        verbose_name="申請人"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="申請標題",
        help_text="簡述此次簽章申請的內容"
    )
    description = models.TextField(
        verbose_name="申請說明",
        help_text="請詳細說明簽章需求、用途及相關資訊"
    )

    # 狀態管理
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="狀態"
    )
    reject_reason = models.TextField(
        blank=True,
        verbose_name="退回原因",
        help_text="當申請被退回時，管理員需填寫此欄位"
    )

    # 處理資訊
    assigned_admin = models.ForeignKey(
        SigningAdmin,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_requests',
        verbose_name="處理管理員"
    )

    # 時間記錄
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="申請時間"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新時間"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="完成時間"
    )

    class Meta:
        verbose_name = "簽章申請"
        verbose_name_plural = "簽章申請"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title} - {self.applicant}"

    @property
    def file_count(self):
        """取得檔案數量"""
        return self.files.count()

    @property
    def signed_file_count(self):
        """取得已簽章檔案數量"""
        return self.files.filter(signed_file__isnull=False).exclude(signed_file='').count()

    @property
    def all_files_signed(self):
        """檢查是否所有檔案都已簽章"""
        if self.file_count == 0:
            return False
        return self.signed_file_count == self.file_count

    def mark_as_processing(self, admin):
        """標記為處理中"""
        self.status = 'processing'
        self.assigned_admin = admin
        self.save(update_fields=['status', 'assigned_admin', 'updated_at'])

    def mark_as_completed(self):
        """標記為已完成"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def mark_as_rejected(self, reason):
        """標記為已退回"""
        self.status = 'rejected'
        self.reject_reason = reason
        self.save(update_fields=['status', 'reject_reason', 'updated_at'])


class SigningFile(models.Model):
    """
    簽章檔案
    包含原始上傳檔案與簽章後檔案
    """
    request = models.ForeignKey(
        SigningRequest,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name="所屬申請"
    )
    original_file = SinoFileField(
        upload_to=signing_file_upload_path,
        validators=[validate_signing_file],
        verbose_name="原始檔案"
    )
    signed_file = SinoFileField(
        upload_to=signed_file_upload_path,
        blank=True,
        null=True,
        verbose_name="簽章後檔案"
    )
    original_filename = models.CharField(
        max_length=255,
        verbose_name="原始檔名"
    )
    file_size = models.BigIntegerField(
        default=0,
        verbose_name="檔案大小（bytes）"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="上傳時間"
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="簽章時間"
    )

    class Meta:
        verbose_name = "簽章檔案"
        verbose_name_plural = "簽章檔案"
        ordering = ['uploaded_at']

    def __str__(self):
        return self.original_filename

    @property
    def is_signed(self):
        """檢查是否已簽章"""
        return bool(self.signed_file)

    @property
    def file_extension(self):
        """取得檔案副檔名"""
        return os.path.splitext(self.original_filename)[1].lower()

    @property
    def file_size_display(self):
        """取得檔案大小（人類可讀格式）"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def save(self, *args, **kwargs):
        # 儲存原始檔名和檔案大小
        if self.original_file and not self.original_filename:
            self.original_filename = self.original_file.name
        if self.original_file and not self.file_size:
            try:
                self.file_size = self.original_file.size
            except Exception:
                pass
        super().save(*args, **kwargs)
