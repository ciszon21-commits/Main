"""
SinoFile Admin
===============
ArchiveFolder 的 Django Admin 管理介面。
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import ArchiveFolder


@admin.register(ArchiveFolder)
class ArchiveFolderAdmin(admin.ModelAdmin):
    """封存資料夾管理"""
    
    list_display = [
        'folder_name',
        'status_badge',
        'display_size',
        'file_count',
        'created_at',
        'closed_at',
        'archived_at',
    ]
    
    list_filter = ['status', 'created_at']
    search_fields = ['folder_name']
    readonly_fields = [
        'folder_name',
        'total_size',
        'status',
        'created_at',
        'closed_at',
        'archived_at',
        'display_manifest',
    ]
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('folder_name', 'status', 'total_size', 'max_size')
        }),
        ('時間紀錄', {
            'fields': ('created_at', 'closed_at', 'archived_at')
        }),
        ('清單內容', {
            'fields': ('display_manifest',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """顯示狀態標籤"""
        colors = {
            'STAGING': '#f0ad4e',   # 橘色
            'CLOSED': '#5bc0de',    # 藍色
            'ARCHIVED': '#5cb85c',  # 綠色
        }
        color = colors.get(obj.status, '#777')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = '狀態'
    
    def display_size(self, obj):
        """顯示可讀大小"""
        return obj.get_human_size()
    display_size.short_description = '目前大小'
    
    def file_count(self, obj):
        """顯示檔案數量"""
        return obj.get_file_count()
    file_count.short_description = '檔案數'
    
    def display_manifest(self, obj):
        """顯示清單內容（格式化）"""
        files = obj.manifest_data.get('files', [])
        if not files:
            return '（無檔案）'
        
        rows = []
        for f in files[:50]:  # 最多顯示 50 筆
            rows.append(
                f"<tr>"
                f"<td style='padding: 4px; border: 1px solid #ddd;'>{f.get('uuid_filename', '-')}</td>"
                f"<td style='padding: 4px; border: 1px solid #ddd;'>{f.get('original_path', '-')}</td>"
                f"<td style='padding: 4px; border: 1px solid #ddd;'>{f.get('model_label', '-')}</td>"
                f"</tr>"
            )
        
        table = (
            "<table style='border-collapse: collapse; width: 100%;'>"
            "<thead><tr style='background: #f5f5f5;'>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>UUID 檔名</th>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>原始路徑</th>"
            "<th style='padding: 8px; border: 1px solid #ddd;'>來源模型</th>"
            "</tr></thead><tbody>"
            + "".join(rows) +
            "</tbody></table>"
        )
        
        if len(files) > 50:
            table += f"<p style='color: #999;'>... 還有 {len(files) - 50} 個檔案</p>"
        
        return format_html(table)
    display_manifest.short_description = '清單內容'
    
    def has_add_permission(self, request):
        """禁止從 Admin 手動新增"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """只允許刪除 STAGING 狀態的資料夾"""
        if obj and obj.status != ArchiveFolder.Status.STAGING:
            return False
        return super().has_delete_permission(request, obj)
