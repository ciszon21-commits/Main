from django.contrib import admin
from .models import Announcement, DroneReviewer, DroneReservation


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """公告管理"""
    list_display = ['title', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']

    def save_model(self, request, obj, form, change):
        if not change:  # 新增時
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DroneReviewer)
class DroneReviewerAdmin(admin.ModelAdmin):
    """簽核人管理"""
    list_display = ['user', 'get_full_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = '姓名'


@admin.register(DroneReservation)
class DroneReservationAdmin(admin.ModelAdmin):
    """預約管理"""
    list_display = [
        'id',
        'applicant',
        'get_applicant_name',
        'usage_start_datetime',
        'usage_end_datetime',
        'location',
        'status',
        'reviewer',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'usage_start_datetime']
    search_fields = [
        'applicant__username',
        'applicant__first_name',
        'applicant__last_name',
        'project_number',
        'location'
    ]
    raw_id_fields = ['applicant', 'reviewer']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('申請人資訊', {
            'fields': ('applicant', 'phone_extension', 'project_number')
        }),
        ('申請內容', {
            'fields': ('reason', 'usage_start_datetime', 'usage_end_datetime', 'location', 'notes')
        }),
        ('簽核資訊', {
            'fields': ('status', 'reviewer', 'review_datetime', 'rejection_reason')
        }),
        ('時間戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_applicant_name(self, obj):
        return obj.applicant.get_full_name() or obj.applicant.username
    get_applicant_name.short_description = '申請人姓名'
