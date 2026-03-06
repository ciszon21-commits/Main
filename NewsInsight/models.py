from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SearchRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="使用者")
    keywords = models.CharField(max_length=255, verbose_name="搜尋關鍵字")
    start_date = models.DateField(null=True, blank=True, verbose_name="起始日期")
    end_date = models.DateField(null=True, blank=True, verbose_name="結束日期")
    topic_words = models.TextField(blank=True, verbose_name="主題詞")
    stop_words = models.TextField(blank=True, verbose_name="停用詞")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="查詢時間")

    class Meta:
        verbose_name = "搜尋紀錄"
        verbose_name_plural = "搜尋紀錄"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.keywords} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
