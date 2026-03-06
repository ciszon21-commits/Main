from django.contrib import admin
from .models import Project, Scene, UserActionLog, HazardType, PresetHotspot
from django.utils.html import format_html
import json

class SceneInline(admin.TabularInline):
    model = Scene
    extra = 1
    fields = ('title', 'image', 'order', 'pitch', 'yaw', 'hfov')
    ordering = ('order',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'district', 'created_at', 'scene_count')
    search_fields = ('name', 'description', 'city', 'district', 'address_detail')
    inlines = [SceneInline]

    def scene_count(self, obj):
        return obj.scenes.count()
    scene_count.short_description = "場景數量"

@admin.register(HazardType)
class HazardTypeAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'name', 'description_short')
    search_fields = ('name', 'description')
    ordering = ('serial_number',)

    def description_short(self, obj):
        return obj.description[:60] + '...' if len(obj.description) > 60 else obj.description
    description_short.short_description = "危害類型說明"


@admin.register(PresetHotspot)
class PresetHotspotAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'source_folder', 'title', 'hazard_type', 'preview_image', 'created_at')
    list_filter = ('source_folder', 'hazard_type')
    search_fields = ('title', 'description', 'original_filename')
    ordering = ('serial_number',)
    readonly_fields = ('original_filename', 'created_at', 'updated_at', 'preview_image_large')

    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:50px;border-radius:4px;">', obj.image.url)
        return '—'
    preview_image.short_description = '圖片預覽'

    def preview_image_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:300px;border-radius:6px;">', obj.image.url)
        return '—'
    preview_image_large.short_description = '圖片'


class SceneAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'order', 'preview_image')
    list_filter = ('project',)
    search_fields = ('title', 'project__name')
    ordering = ('project', 'order')

    def preview_image(self, obj):
        if obj.image:
            return "有圖片"
        return "無圖片"
    preview_image.short_description = "圖片"


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    """
    使用者操作記錄管理介面
    
    提供詳細的操作記錄查看、篩選、搜尋功能
    """
    list_display = (
        'created_at',
        'user_display',
        'action_type_display',
        'object_display',
        'ip_address',
        'request_path_short',
    )
    
    list_filter = (
        'action_type',
        'content_type',
        ('created_at', admin.DateFieldListFilter),
        'user',
    )
    
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'ip_address',
        'object_repr',
        'request_path',
    )
    
    readonly_fields = (
        'user',
        'action_type',
        'content_type',
        'object_id',
        'object_repr',
        'action_detail_display',
        'ip_address',
        'user_agent',
        'request_path',
        'request_method',
        'session_key',
        'created_at',
    )
    
    # 只讀模式，不允許修改或刪除記錄
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # 分頁設置
    list_per_page = 50
    
    # 日期階層
    date_hierarchy = 'created_at'
    
    # 使用 select_related 優化查詢
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content_type')
    
    # 自定義顯示欄位
    def user_display(self, obj):
        if obj.user:
            return f"{obj.user.username}"
        return "匿名用戶"
    user_display.short_description = "使用者"
    user_display.admin_order_field = 'user__username'
    
    def action_type_display(self, obj):
        # 使用顏色標記不同的操作類型
        colors = {
            'CREATE': '#28a745',  # 綠色
            'UPDATE': '#ffc107',  # 黃色
            'DELETE': '#dc3545',  # 紅色
            'VIEW': '#17a2b8',    # 青色
            'LOGIN': '#6610f2',   # 紫色
            'LOGOUT': '#6c757d',  # 灰色
            'UPLOAD': '#007bff',  # 藍色
            'DOWNLOAD': '#20c997',# 青綠色
            'REFERENCE': '#fd7e14',# 橘色
            'REORDER': '#e83e8c', # 粉紅色
            'MOVE': '#6f42c1',    # 紫色
            'SET_COVER': '#17a2b8',# 青色
            'OTHER': '#6c757d',   # 灰色
        }
        color = colors.get(obj.action_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_action_type_display()
        )
    action_type_display.short_description = "操作類型"
    action_type_display.admin_order_field = 'action_type'
    
    def object_display(self, obj):
        if obj.object_repr:
            return obj.object_repr
        elif obj.content_type and obj.object_id:
            return f"{obj.content_type} #{obj.object_id}"
        return "系統操作"
    object_display.short_description = "操作對象"
    
    def request_path_short(self, obj):
        if len(obj.request_path) > 50:
            return obj.request_path[:47] + "..."
        return obj.request_path
    request_path_short.short_description = "請求路徑"
    request_path_short.admin_order_field = 'request_path'
    
    def action_detail_display(self, obj):
        """
        以格式化的 JSON 顯示操作詳情
        """
        if obj.action_detail:
            try:
                formatted_json = json.dumps(obj.action_detail, ensure_ascii=False, indent=2)
                return format_html('<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', formatted_json)
            except Exception:
                return str(obj.action_detail)
        return "無詳細資訊"
    action_detail_display.short_description = "操作詳情 (JSON)"
    
    # 自定義操作
    actions = ['export_to_csv']
    
    def export_to_csv(self, request, queryset):
        """
        匯出選中的記錄為 CSV
        """
        import csv
        from django.http import HttpResponse
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="user_actions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # 添加 BOM 以支援 Excel 正確顯示中文
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            '操作時間',
            '使用者',
            '操作類型',
            '操作對象',
            'IP地址',
            '請求路徑',
            '請求方法',
        ])
        
        for log in queryset:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.user.username if log.user else '匿名用戶',
                log.get_action_type_display(),
                log.object_repr or f"{log.content_type} #{log.object_id}" if log.content_type else '系統操作',
                log.ip_address,
                log.request_path,
                log.request_method,
            ])
        
        return response
    export_to_csv.short_description = "匯出為 CSV"

