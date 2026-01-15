"""
OpenSearch Logging Models
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SearchLog(models.Model):
    """Records search queries for analytics"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opensearch_searches',
        verbose_name='使用者'
    )
    query = models.CharField(max_length=500, verbose_name='搜尋關鍵字')
    indices = models.CharField(max_length=200, default='*', verbose_name='搜尋範圍')
    results_count = models.IntegerField(default=0, verbose_name='結果數量')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='搜尋時間')

    class Meta:
        verbose_name = '搜尋記錄'
        verbose_name_plural = '搜尋記錄'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['query']),
        ]

    def __str__(self):
        return f'{self.user} - "{self.query}" ({self.results_count} results)'


class ClickLog(models.Model):
    """Records click actions on search results"""
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opensearch_clicks',
        verbose_name='使用者'
    )
    query = models.CharField(max_length=500, blank=True, verbose_name='搜尋關鍵字')
    index_name = models.CharField(max_length=200, verbose_name='索引名稱')
    doc_id = models.CharField(max_length=200, verbose_name='文件ID')
    title = models.CharField(max_length=500, blank=True, verbose_name='標題')
    path = models.TextField(blank=True, verbose_name='檔案路徑')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='點擊時間')

    class Meta:
        verbose_name = '點擊記錄'
        verbose_name_plural = '點擊記錄'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['index_name']),
        ]

    def __str__(self):
        return f'{self.user} - {self.title[:30]}... ({self.index_name})'
