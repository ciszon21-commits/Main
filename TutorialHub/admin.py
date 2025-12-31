from django.contrib import admin
from .models import (
    Tutorial,
    TutorialMaintainer,
    TutorialStep,
    StepSnippet,
    ReadingLog,
    Question,
    Answer
)


class TutorialMaintainerInline(admin.TabularInline):
    """教材維護者內嵌管理"""
    model = TutorialMaintainer
    extra = 1
    fields = ['user', 'role', 'contribution_score']


class TutorialStepInline(admin.StackedInline):
    """教材步驟內嵌管理"""
    model = TutorialStep
    extra = 0
    fields = ['title', 'order', 'is_expanded_default']
    show_change_link = True


@admin.register(Tutorial)
class TutorialAdmin(admin.ModelAdmin):
    """教材管理介面"""
    list_display = [
        'title',
        'is_published',
        'view_count',
        'step_count',
        'image_count',
        'code_count',
        'unique_readers',
        'created_at',
    ]
    list_filter = ['is_published', 'created_at', 'updated_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'view_count',
        'step_count',
        'image_count',
        'code_count',
        'total_reading_time',
        'unique_readers',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'slug', 'description', 'cover_image', 'is_published')
        }),
        ('統計資訊', {
            'fields': (
                'view_count',
                'step_count',
                'image_count',
                'code_count',
                'unique_readers',
                'total_reading_time',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TutorialMaintainerInline, TutorialStepInline]


class StepSnippetInline(admin.TabularInline):
    """步驟片段內嵌管理"""
    model = StepSnippet
    extra = 1
    fields = ['snippet_type', 'order', 'content', 'image', 'language', 'caption', 'link_url', 'link_text']


@admin.register(TutorialStep)
class TutorialStepAdmin(admin.ModelAdmin):
    """教材步驟管理介面"""
    list_display = ['title', 'tutorial', 'order', 'is_expanded_default', 'created_at']
    list_filter = ['tutorial', 'is_expanded_default', 'created_at']
    search_fields = ['title', 'tutorial__title']
    
    inlines = [StepSnippetInline]


@admin.register(StepSnippet)
class StepSnippetAdmin(admin.ModelAdmin):
    """步驟片段管理介面"""
    list_display = ['__str__', 'step', 'snippet_type', 'language', 'order']
    list_filter = ['snippet_type', 'language', 'step__tutorial']
    search_fields = ['content', 'caption', 'step__title', 'link_url', 'link_text']


@admin.register(TutorialMaintainer)
class TutorialMaintainerAdmin(admin.ModelAdmin):
    """教材維護者管理介面"""
    list_display = ['user', 'tutorial', 'role', 'contribution_score', 'joined_at']
    list_filter = ['role', 'joined_at', 'tutorial']
    search_fields = ['user__username', 'tutorial__title']


@admin.register(ReadingLog)
class ReadingLogAdmin(admin.ModelAdmin):
    """閱讀記錄管理介面"""
    list_display = [
        'user',
        'tutorial',
        'reading_time_display',
        'first_read_at',
        'last_read_at'
    ]
    list_filter = ['first_read_at', 'last_read_at', 'tutorial']
    search_fields = ['user__username', 'tutorial__title']
    readonly_fields = ['first_read_at', 'last_read_at']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """提問管理介面"""
    list_display = ['user', 'step', 'is_resolved', 'created_at']
    list_filter = ['is_resolved', 'created_at', 'step__tutorial']
    search_fields = ['content', 'user__username', 'step__title']
    readonly_fields = ['created_at']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """回答管理介面"""
    list_display = ['user', 'question', 'is_from_maintainer', 'created_at']
    list_filter = ['is_from_maintainer', 'created_at']
    search_fields = ['content', 'user__username', 'question__content']
    readonly_fields = ['created_at', 'is_from_maintainer']
