from django.contrib import admin
from .models import Course, Registration, PDFDownloadLog, CourseComment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """課程管理介面"""
    list_display = [
        'title',
        'instructor_name',
        'location',
        'created_by',
        'course_datetime',
        'registration_start',
        'registration_end',
        'current_participants_count',
        'max_participants',
        'registration_status',
    ]
    list_filter = ['created_at', 'course_datetime', 'created_by']
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'current_participants_count', 'pdf_download_count']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'description', 'instructor_name', 'location', 'created_by')
        }),
        ('時間設定', {
            'fields': ('course_datetime', 'registration_start', 'registration_end')
        }),
        ('附件與限制', {
            'fields': ('pdf_file', 'max_participants')
        }),
        ('統計資訊', {
            'fields': ('current_participants_count', 'pdf_download_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """報名記錄管理介面"""
    list_display = ['course', 'user', 'registered_at']
    list_filter = ['registered_at', 'course']
    search_fields = ['course__title', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['registered_at']


@admin.register(PDFDownloadLog)
class PDFDownloadLogAdmin(admin.ModelAdmin):
    """PDF 下載記錄管理介面"""
    list_display = ['course', 'user', 'downloaded_at']
    list_filter = ['downloaded_at', 'course']
    search_fields = ['course__title', 'user__username']
    readonly_fields = ['downloaded_at']


@admin.register(CourseComment)
class CourseCommentAdmin(admin.ModelAdmin):
    """課程留言管理介面"""
    list_display = ['course', 'user', 'content_preview', 'created_at']
    list_filter = ['created_at', 'course']
    search_fields = ['course__title', 'user__username', 'content']
    readonly_fields = ['created_at']
    
    def content_preview(self, obj):
        """留言內容預覽（截斷50字）"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '留言內容'
