from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Project(models.Model):
    name = models.CharField(_("專案名稱"), max_length=200)
    description = models.TextField(_("專案描述"), blank=True)
    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)
    cover_image = models.ImageField(_("封面圖片"), upload_to='site360/projects/', blank=True, null=True)

    # Address Fields
    city = models.CharField(_("縣市"), max_length=50, blank=True)
    district = models.CharField(_("區域"), max_length=50, blank=True)
    address_detail = models.CharField(_("詳細地址"), max_length=200, blank=True)

    # Geo Fields
    latitude = models.FloatField(_("緯度"), blank=True, null=True)
    longitude = models.FloatField(_("經度"), blank=True, null=True)

    class Meta:
        verbose_name = _("專案")
        verbose_name_plural = _("專案")
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Scene(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scenes', verbose_name=_("所屬專案"))
    title = models.CharField(_("場景標題"), max_length=200)
    image = models.ImageField(_("360全景圖"), upload_to='site360/scenes/')
    order = models.PositiveIntegerField(_("排序"), default=0)
    
    # Initial view settings
    pitch = models.FloatField(_("初始俯仰角 (Pitch)"), default=0, help_text="Starting pitch in degrees")
    yaw = models.FloatField(_("初始偏航角 (Yaw)"), default=0, help_text="Starting yaw in degrees")
    hfov = models.FloatField(_("視場角 (HFOV)"), default=110, help_text="Horizontal field of view in degrees")

    # Navigation Hotspot Positions (Customizable)
    next_pitch = models.FloatField(_("下一張熱點 Pitch"), default=-5)
    next_yaw = models.FloatField(_("下一張熱點 Yaw"), default=0)
    prev_pitch = models.FloatField(_("上一張熱點 Pitch"), default=-5)
    prev_yaw = models.FloatField(_("上一張熱點 Yaw"), default=180)

    class Meta:
        verbose_name = _("場景")
        verbose_name_plural = _("場景")
        ordering = ['order', 'title']

    def __str__(self):
        return f"{self.project.name} - {self.title}"

class Hotspot(models.Model):
    TYPE_CHOICES = (
        ('text', '文字'),
        ('text_hover', '懸浮文字'),
        ('image', '圖片'),
        ('image_hover', '懸浮圖片'),
        ('video', '影片'),
        ('video_hover', '懸浮影片'),
    )

    scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True, blank=True, related_name='hotspots', verbose_name=_("所屬場景"))
    hotspot_type = models.CharField(_("類型"), max_length=20, choices=TYPE_CHOICES, default='text')
    pitch = models.FloatField(_("俯仰角 (Pitch)"))
    yaw = models.FloatField(_("偏航角 (Yaw)"))
    title = models.CharField(_("標題"), max_length=200)
    description = models.TextField(_("詳細說明"), blank=True)
    image = models.ImageField(_("圖片內容"), upload_to='site360/hotspots/images/', blank=True, null=True)
    video = models.FileField(_("影片內容"), upload_to='site360/hotspots/videos/', blank=True, null=True)
    icon = models.CharField(_("圖示"), max_length=50, default='fas fa-info-circle')
    icon_color = models.CharField(_("圖示顏色"), max_length=20, default='#ffffff')
    
    # Data Provenance
    source_hotspot = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='copied_by', help_text="The original hotspot this was imported from")

    # Version Control
    version_number = models.PositiveIntegerField(_("版本號"), default=1, help_text="Version number of this resource")
    is_latest_version = models.BooleanField(_("是否為最新版本"), default=True, help_text="Indicates if this is the latest version")
    original_resource = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='versions', help_text="Points to the original resource in the version chain")

    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新時間"), auto_now=True)

    class Meta:
        verbose_name = _("熱點內容")
        verbose_name_plural = _("熱點內容")

    def __str__(self):
        return f"{self.get_hotspot_type_display()} - {self.title}"


class HazardType(models.Model):
    """危害類型資料表"""
    serial_number = models.PositiveIntegerField(_("項次"), unique=True, help_text="危害類型的項次編號")
    name = models.CharField(_("危害類型名稱"), max_length=200)
    description = models.TextField(_("危害類型說明"), blank=True)

    class Meta:
        verbose_name = _("危害類型")
        verbose_name_plural = _("危害類型")
        ordering = ['serial_number']

    def __str__(self):
        return f"{self.serial_number}. {self.name}"


class UserActionLog(models.Model):
    """
    記錄所有使用者操作的詳細資訊
    """
    ACTION_TYPE_CHOICES = (
        ('CREATE', '建立'),
        ('UPDATE', '更新'),
        ('DELETE', '刪除'),
        ('VIEW', '查看'),
        ('LOGIN', '登入'),
        ('LOGOUT', '登出'),
        ('UPLOAD', '上傳'),
        ('DOWNLOAD', '下載'),
        ('REFERENCE', '引用'),
        ('REORDER', '重新排序'),
        ('MOVE', '移動'),
        ('SET_COVER', '設為封面'),
        ('OTHER', '其他'),
    )

    # 使用者資訊
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("使用者"),
        help_text="執行操作的使用者，null 表示匿名用戶"
    )
    
    # 操作資訊
    action_type = models.CharField(
        _("操作類型"), 
        max_length=20, 
        choices=ACTION_TYPE_CHOICES,
        db_index=True
    )
    
    # 操作對象 (使用 Generic Foreign Key)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("對象類型"),
        db_index=True
    )
    object_id = models.PositiveIntegerField(
        _("對象ID"), 
        null=True, 
        blank=True,
        db_index=True
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 對象字串表示（冗餘存儲，避免對象被刪除後無法查看）
    object_repr = models.CharField(
        _("對象描述"), 
        max_length=500, 
        blank=True,
        help_text="操作對象的字串表示"
    )
    
    # 操作詳情 (JSON格式存儲具體變更內容)
    action_detail = models.JSONField(
        _("操作詳情"), 
        default=dict, 
        blank=True,
        help_text="包含請求參數、變更內容等詳細資訊"
    )
    
    # 請求資訊
    ip_address = models.GenericIPAddressField(
        _("IP地址"), 
        null=True, 
        blank=True,
        help_text="客戶端IP地址"
    )
    user_agent = models.CharField(
        _("用戶代理"), 
        max_length=500, 
        blank=True,
        help_text="瀏覽器和操作系統資訊"
    )
    request_path = models.CharField(
        _("請求路徑"), 
        max_length=500, 
        blank=True,
        db_index=True
    )
    request_method = models.CharField(
        _("請求方法"), 
        max_length=10, 
        blank=True,
        help_text="GET, POST, PUT, DELETE 等"
    )
    
    # 會話資訊
    session_key = models.CharField(
        _("會話KEY"), 
        max_length=100, 
        blank=True,
        db_index=True,
        help_text="用於追蹤同一會話的操作"
    )
    
    # 時間戳記
    created_at = models.DateTimeField(
        _("操作時間"), 
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = _("使用者操作記錄")
        verbose_name_plural = _("使用者操作記錄")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['session_key']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "匿名用戶"
        action = self.get_action_type_display()
        obj_str = self.object_repr or f"{self.content_type} #{self.object_id}" if self.content_type else "系統"
        return f"{user_str} {action} {obj_str}"
