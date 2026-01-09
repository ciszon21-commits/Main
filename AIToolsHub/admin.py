from django.contrib import admin
from .models import Category, Tag, AITool, ViewLog, Favorite, Like, Comment, CommentReaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'created_at']
    list_editable = ['order']
    search_fields = ['name']
    ordering = ['order', 'name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    ordering = ['name']


@admin.register(AITool)
class AIToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_by', 'favorite_count', 'like_count', 'view_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'summary', 'created_by__username', 'created_by__first_name', 'created_by__last_name']
    filter_horizontal = ['tags']
    readonly_fields = ['favorite_count', 'like_count', 'view_count', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'category', 'image', 'url', 'summary', 'tags')
        }),
        ('詳細內容', {
            'fields': ('extra_info', 'note_content'),
            'classes': ('collapse',),
        }),
        ('統計資訊', {
            'fields': ('favorite_count', 'like_count', 'view_count'),
            'classes': ('collapse',),
        }),
        ('系統資訊', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ViewLog)
class ViewLogAdmin(admin.ModelAdmin):
    list_display = ['tool', 'user', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['tool__name', 'user__username']
    ordering = ['-viewed_at']


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['tool', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['tool__name', 'user__username']
    ordering = ['-created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['tool', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['tool__name', 'user__username']
    ordering = ['-created_at']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['tool', 'user', 'short_content', 'is_anonymous', 'parent', 'created_at']
    list_filter = ['is_anonymous', 'created_at']
    search_fields = ['tool__name', 'user__username', 'content']
    ordering = ['-created_at']

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = '留言內容'


@admin.register(CommentReaction)
class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ['comment', 'user', 'reaction_type', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    search_fields = ['comment__content', 'user__username']
    ordering = ['-created_at']

