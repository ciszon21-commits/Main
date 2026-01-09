from django.db import models
from django.utils.translation import gettext_lazy as _

class Project(models.Model):
    name = models.CharField(_("專案名稱"), max_length=200)
    description = models.TextField(_("專案描述"), blank=True)
    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)
    cover_image = models.ImageField(_("封面圖片"), upload_to='site360/projects/', blank=True, null=True)

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

    class Meta:
        verbose_name = _("場景")
        verbose_name_plural = _("場景")
        ordering = ['order', 'title']

    def __str__(self):
        return f"{self.project.name} - {self.title}"

class Hotspot(models.Model):
    TYPE_CHOICES = (
        ('text', '文字公告 (Text)'),
        ('text_hover', '懸浮文字 (Hover Text)'),
        ('image', '照片 (Image)'),
        ('image_hover', '懸浮照片 (Hover Image)'),
        ('video', '影片 (Video)'),
    )

    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='hotspots', verbose_name=_("所屬場景"))
    hotspot_type = models.CharField(_("類型"), max_length=20, choices=TYPE_CHOICES, default='text')
    pitch = models.FloatField(_("俯仰角 (Pitch)"))
    yaw = models.FloatField(_("偏航角 (Yaw)"))
    title = models.CharField(_("標題"), max_length=200)
    description = models.TextField(_("詳細說明"), blank=True)
    image = models.ImageField(_("圖片內容"), upload_to='site360/hotspots/images/', blank=True, null=True)
    video = models.FileField(_("影片內容"), upload_to='site360/hotspots/videos/', blank=True, null=True)
    icon = models.CharField(_("圖示"), max_length=50, default='fas fa-info-circle')
    icon_color = models.CharField(_("圖示顏色"), max_length=20, default='#ffffff')
    created_at = models.DateTimeField(_("建立時間"), auto_now_add=True)

    class Meta:
        verbose_name = _("熱點內容")
        verbose_name_plural = _("熱點內容")

    def __str__(self):
        return f"{self.get_hotspot_type_display()} - {self.title}"
