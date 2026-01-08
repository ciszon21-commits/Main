from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django_ckeditor_5.fields import CKEditor5Field
from SinoFile.fields import SinoFileField


class Category(models.Model):
    """分類模型"""
    name = models.CharField(max_length=100, verbose_name="分類名稱")
    description = models.TextField(blank=True, verbose_name="分類說明")
    order = models.IntegerField(default=0, verbose_name="排序", help_text="數字越小越靠前")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "分類"
        verbose_name_plural = "分類"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Achievement(models.Model):
    """開發成果模型"""
    name = models.CharField(max_length=200, verbose_name="成果名稱")
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='achievements',
        verbose_name="分類"
    )
    summary = models.CharField(max_length=200, verbose_name="簡介")
    video = SinoFileField(
        upload_to='achievements/videos/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])],
        verbose_name="展示影片",
        help_text="請上傳10分鐘以下的影片"
    )
    url = models.URLField(verbose_name="相關網址", blank=True)
    documentation = CKEditor5Field(verbose_name="說明文件", blank=True, config_name='extends')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_achievements',
        verbose_name="建立者"
    )
    developers = models.ManyToManyField(
        User,
        related_name='achievements',
        verbose_name="協同開發者",
        blank=True
    )
    
    view_count = models.IntegerField(default=0, verbose_name="瀏覽次數")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "開發成果"
        verbose_name_plural = "開發成果"
        ordering = ['-view_count', '-created_at']

    def __str__(self):
        return self.name

    def get_all_developers(self):
        """取得所有開發者（包含建立者）"""
        developers = list(self.developers.all())
        if self.created_by not in developers:
            developers.insert(0, self.created_by)
        return developers


class ViewLog(models.Model):
    """瀏覽記錄模型"""
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='view_logs',
        verbose_name="成果"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="使用者"
    )
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="瀏覽時間")

    class Meta:
        verbose_name = "瀏覽記錄"
        verbose_name_plural = "瀏覽記錄"
        unique_together = ['achievement', 'user']
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.get_full_name} - {self.achievement.name}"


class Comment(models.Model):
    """留言模型"""
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="成果"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="使用者"
    )
    content = models.TextField(verbose_name="留言內容")
    is_resolved = models.BooleanField(default=False, verbose_name="已解決")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="留言時間")

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name} - {self.achievement.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
