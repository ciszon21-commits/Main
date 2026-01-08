"""
SinoFile Models
================
用於管理分層儲存系統的資料模型。

ArchiveFolder: 管理封存卷冊（如光碟或磁帶卷）的狀態和內容清單。
"""

from django.db import models
from django.utils import timezone


class ArchiveFolder(models.Model):
    """
    封存資料夾模型
    
    用於管理儲存卷冊（Volume），每個卷冊有大小上限（預設 4GB）。
    支援追蹤 STAGING -> CLOSED -> ARCHIVED 的狀態流程。
    """
    
    class Status(models.TextChoices):
        STAGING = 'STAGING', '暫存中'    # 正在收集檔案
        CLOSED = 'CLOSED', '已封閉'      # 達到大小上限，等待轉移
        ARCHIVED = 'ARCHIVED', '已封存'  # 已完成轉移到冷儲存
    
    folder_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='資料夾名稱',
        help_text='例如: VOL_20260108'
    )
    
    total_size = models.BigIntegerField(
        default=0,
        verbose_name='目前大小(bytes)',
        help_text='此卷冊中所有檔案的總大小'
    )
    
    max_size = models.BigIntegerField(
        default=4 * 1024 * 1024 * 1024,  # 4GB
        verbose_name='大小上限(bytes)'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.STAGING,
        verbose_name='狀態'
    )
    
    manifest_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='清單資料',
        help_text='記錄原始路徑與 UUID 檔名的對應關係'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間'
    )
    
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='封閉時間'
    )
    
    archived_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='封存時間'
    )
    
    class Meta:
        verbose_name = '封存資料夾'
        verbose_name_plural = '封存資料夾'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.folder_name} ({self.get_status_display()})'
    
    def get_remaining_space(self):
        """取得剩餘可用空間"""
        return max(0, self.max_size - self.total_size)
    
    def can_add_file(self, file_size: int) -> bool:
        """檢查是否可加入指定大小的檔案"""
        return self.status == self.Status.STAGING and file_size <= self.get_remaining_space()
    
    def add_to_manifest(self, original_path: str, uuid_filename: str, file_size: int, 
                        model_label: str, field_name: str, instance_pk):
        """
        將檔案資訊加入清單
        
        Args:
            original_path: 原始檔案路徑 (相對於 MEDIA_ROOT)
            uuid_filename: 新的 UUID 檔名
            file_size: 檔案大小
            model_label: 模型標籤 (app_label.model_name)
            field_name: 欄位名稱
            instance_pk: 模型實例主鍵
        """
        if 'files' not in self.manifest_data:
            self.manifest_data['files'] = []
        
        self.manifest_data['files'].append({
            'original_path': original_path,
            'uuid_filename': uuid_filename,
            'file_size': file_size,
            'model_label': model_label,
            'field_name': field_name,
            'instance_pk': instance_pk,
        })
        self.total_size += file_size
    
    def close(self):
        """封閉資料夾，準備轉移"""
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save()
    
    def archive(self):
        """標記為已封存"""
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save()
    
    def get_file_count(self):
        """取得檔案數量"""
        return len(self.manifest_data.get('files', []))
    
    def get_human_size(self):
        """返回人類可讀的檔案大小"""
        size = self.total_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} TB'
