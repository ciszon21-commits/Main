from django.contrib import admin
from .models import Category, Achievement, ViewLog, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


class DeveloperInline(admin.TabularInline):
    model = Achievement.developers.through
    extra = 1
    verbose_name = "協同開發者"
    verbose_name_plural = "協同開發者"


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'view_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'summary', 'documentation']
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    filter_horizontal = ['developers']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'category', 'summary', 'url')
        }),
        ('媒體內容', {
            'fields': ('video', 'documentation')
        }),
        ('開發者', {
            'fields': ('created_by', 'developers')
        }),
        ('統計資訊', {
            'fields': ('view_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # 新建時
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ViewLog)
class ViewLogAdmin(admin.ModelAdmin):
    list_display = ['achievement', 'user', 'viewed_at']
    list_filter = ['viewed_at', 'achievement__category']
    search_fields = ['achievement__name', 'user__username']
    readonly_fields = ['achievement', 'user', 'viewed_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['achievement', 'user', 'content_preview', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at', 'achievement__category']
    search_fields = ['content', 'achievement__name', 'user__username']
    readonly_fields = ['achievement', 'user', 'content', 'created_at']
    list_editable = ['is_resolved']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '留言內容'
    
    def has_add_permission(self, request):
        return False
