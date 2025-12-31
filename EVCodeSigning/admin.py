"""
EVCodeSigning Admin - Django Admin 設定
"""
from django.contrib import admin
from django.contrib.auth.models import User
from .models import SigningAdmin, SigningRequest, SigningFile


class SigningFileInline(admin.TabularInline):
    """簽章檔案 Inline"""
    model = SigningFile
    extra = 0
    readonly_fields = ['original_filename', 'file_size', 'uploaded_at', 'signed_at']
    fields = ['original_filename', 'file_size', 'original_file', 'signed_file', 'uploaded_at', 'signed_at']


@admin.register(SigningAdmin)
class SigningAdminAdmin(admin.ModelAdmin):
    """
    簽章管理員管理
    僅 superuser 可以設定
    """
    list_display = ['user', 'user_full_name', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'created_by']
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('管理員資訊', {
            'fields': ('user', 'is_active')
        }),
        ('建立資訊', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    user_full_name.short_description = '姓名'
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建時記錄設定者
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SigningRequest)
class SigningRequestAdmin(admin.ModelAdmin):
    """簽章申請管理"""
    list_display = ['title', 'applicant', 'status', 'file_count', 'assigned_admin', 'created_at']
    list_filter = ['status', 'created_at', 'completed_at']
    search_fields = ['title', 'description', 'applicant__username', 'applicant__first_name']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    autocomplete_fields = ['applicant', 'assigned_admin']
    inlines = [SigningFileInline]
    
    fieldsets = (
        ('申請資訊', {
            'fields': ('title', 'description', 'applicant')
        }),
        ('狀態管理', {
            'fields': ('status', 'reject_reason', 'assigned_admin')
        }),
        ('時間資訊', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_count(self, obj):
        return f"{obj.signed_file_count}/{obj.file_count}"
    file_count.short_description = '已簽章/總檔案'


@admin.register(SigningFile)
class SigningFileAdmin(admin.ModelAdmin):
    """簽章檔案管理"""
    list_display = ['original_filename', 'request', 'file_size_display', 'is_signed', 'uploaded_at', 'signed_at']
    list_filter = ['uploaded_at', 'signed_at']
    search_fields = ['original_filename', 'request__title']
    readonly_fields = ['original_filename', 'file_size', 'uploaded_at', 'signed_at']
    
    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = '檔案大小'
    
    def is_signed(self, obj):
        return obj.is_signed
    is_signed.short_description = '已簽章'
    is_signed.boolean = True
