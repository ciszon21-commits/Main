from django.contrib import admin
from .models import KnowledgeTeam, KnowledgeTeamMember, Topic, KnowledgeItem, ItemComment


class KnowledgeTeamMemberInline(admin.TabularInline):
    model = KnowledgeTeamMember
    extra = 1
    autocomplete_fields = ['user']


@admin.register(KnowledgeTeam)
class KnowledgeTeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'member_count']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    autocomplete_fields = ['created_by']
    inlines = [KnowledgeTeamMemberInline]

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '成員數'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'order', 'created_at']
    list_filter = ['team', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['team', 'order']


class ItemCommentInline(admin.TabularInline):
    model = ItemComment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(KnowledgeItem)
class KnowledgeItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'topic', 'created_by', 'created_at', 'updated_at']
    list_filter = ['topic__team', 'topic', 'created_at']
    search_fields = ['title', 'content']
    autocomplete_fields = ['topic', 'created_by']
    inlines = [ItemCommentInline]


@admin.register(ItemComment)
class ItemCommentAdmin(admin.ModelAdmin):
    list_display = ['item', 'author', 'short_content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']
    autocomplete_fields = ['item', 'author']

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = '內容摘要'
