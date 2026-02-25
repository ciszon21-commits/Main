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


class EmailTemplate(models.Model):
    """郵件模板設定"""
    EMAIL_TYPE_CHOICES = [
        ('new_application', '新申請待審核通知'),
        ('approved', '核准通知'),
        ('rejected', '拒絕通知'),
        ('cancelled', '取消通知'),
        ('time_changed', '時間變更通知'),
    ]
    
    # 預設模板內容
    DEFAULT_TEMPLATES = {
        'new_application': {
            'subject': '[無人機預約] 新申請待審核 - {applicant_name}',
            'body': '''您好，

有一筆新的無人機預約申請待審核：

申請人：{applicant_name}
使用時間：{start_time} ~ {end_time}
地點：{location}
計畫編號：{project_number}
申請理由：{reason}

請登入系統進行審核。

此為系統自動發送郵件，請勿直接回覆。'''
        },
        'approved': {
            'subject': '[無人機預約] 您的申請已核准',
            'body': '''您好，

您的無人機預約申請已核准：

使用時間：{start_time} ~ {end_time}
地點：{location}
簽核人：{reviewer_name}

請依照流程，聯繫簽核人(#07130)，確認行程安排。

此為系統自動發送郵件，請勿直接回覆。'''
        },
        'rejected': {
            'subject': '[無人機預約] 您的申請已被拒絕',
            'body': '''您好，

您的無人機預約申請已被拒絕：

使用時間：{start_time} ~ {end_time}
地點：{location}
簽核人：{reviewer_name}
拒絕理由：{rejection_reason}

如有疑問，請聯繫簽核人(#07130)。

此為系統自動發送郵件，請勿直接回覆。'''
        },
        'cancelled': {
            'subject': '[無人機預約] 預約已取消 - {applicant_name}',
            'body': '''您好，

以下無人機預約已被取消：

申請人：{applicant_name}
使用時間：{start_time} ~ {end_time}
地點：{location}

此為系統自動發送郵件，請勿直接回覆。'''
        },
        'time_changed': {
            'subject': '[無人機預約] 已核准預約時間變更 - {applicant_name}',
            'body': '''您好，

以下已核准的無人機預約時間已被修改：

申請人：{applicant_name}
地點：{location}
計畫編號：{project_number}

【時間變更】
原時間：{old_start_time} ~ {old_end_time}
新時間：{start_time} ~ {end_time}

如有疑問，請聯繫相關人員。

此為系統自動發送郵件，請勿直接回覆。'''
        },
    }

    email_type = models.CharField(
        max_length=30,
        choices=EMAIL_TYPE_CHOICES,
        unique=True,
        verbose_name="郵件類型"
    )
    subject_template = models.CharField(
        max_length=200,
        verbose_name="郵件主旨模板"
    )
    body_template = models.TextField(
        verbose_name="郵件內容模板"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "郵件模板"
        verbose_name_plural = "郵件模板"

    def __str__(self):
        return self.get_email_type_display()

    @classmethod
    def get_template(cls, email_type):
        """取得郵件模板，若不存在則使用預設值"""
        try:
            return cls.objects.get(email_type=email_type)
        except cls.DoesNotExist:
            # 使用預設模板
            defaults = cls.DEFAULT_TEMPLATES.get(email_type, {})
            return cls(
                email_type=email_type,
                subject_template=defaults.get('subject', ''),
                body_template=defaults.get('body', '')
            )

    @classmethod
    def ensure_all_templates(cls):
        """確保所有模板都存在於資料庫中"""
        for email_type, defaults in cls.DEFAULT_TEMPLATES.items():
            cls.objects.get_or_create(
                email_type=email_type,
                defaults={
                    'subject_template': defaults['subject'],
                    'body_template': defaults['body']
                }
            )

    def render(self, context):
        """渲染模板，替換變數"""
        subject = self.subject_template
        body = self.body_template
        for key, value in context.items():
            placeholder = '{' + key + '}'
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
        return subject, body


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
        return f"{self.applicant.get_full_name() or self.applicant.username} - {self.usage_start_datetime.strftime('%Y/%m/%d')}"

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


class MissionRecord(models.Model):
    """飛行任務紀錄 - 記錄已完成的無人機飛行任務"""
    
    # 關聯預約單（可選，用於自動帶入欄位）
    reservation = models.ForeignKey(
        DroneReservation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mission_records',
        verbose_name="關聯預約單"
    )
    
    # 基本資訊
    mission_start_date = models.DateField(verbose_name="任務開始日期")
    mission_end_date = models.DateField(verbose_name="任務結束日期")
    project_number = models.CharField(max_length=100, verbose_name="計畫編號")
    project_short_name = models.CharField(max_length=100, verbose_name="計畫簡稱")
    
    # 地點資訊（用於地圖顯示）
    location_name = models.CharField(max_length=200, verbose_name="任務地點")
    latitude = models.FloatField(verbose_name="緯度", help_text="例如：25.0478")
    longitude = models.FloatField(verbose_name="經度", help_text="例如：121.5319")
    
    # 任務詳情
    mission_description = models.TextField(verbose_name="任務說明")
    drone_payload = models.CharField(max_length=200, verbose_name="無人機/酬載")
    pilot = models.CharField(
        max_length=100,
        verbose_name="任務飛手",
        help_text="輸入飛手姓名",
        default=''
    )
    result_location = models.CharField(
        max_length=500,
        verbose_name="成果存放位置",
        help_text="檔案路徑或雲端連結"
    )
    
    # 管理欄位
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_mission_records',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "飛行任務紀錄"
        verbose_name_plural = "飛行任務紀錄"
        ordering = ['-mission_start_date', '-created_at']

    def __str__(self):
        start = self.mission_start_date.strftime('%Y/%m/%d')
        end = self.mission_end_date.strftime('%Y/%m/%d')
        if start == end:
            return f"{start} - {self.project_short_name}"
        return f"{start}~{end} - {self.project_short_name}"
