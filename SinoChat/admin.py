from django.contrib import admin
from .models import ChatRoom, ChatRoomMember, ChatMessage, ChatFile, ChatFileDownloadLog


class ChatRoomMemberInline(admin.TabularInline):
    model = ChatRoomMember
    extra = 0
    raw_id_fields = ['user']


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'visibility', 'member_count', 'is_active', 'created_at']
    list_filter = ['visibility', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'creator__username']
    raw_id_fields = ['creator']
    inlines = [ChatRoomMemberInline]
    ordering = ['-updated_at']


@admin.register(ChatRoomMember)
class ChatRoomMemberAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['room__name', 'user__username']
    raw_id_fields = ['room', 'user']


class ChatFileInline(admin.TabularInline):
    model = ChatFile
    extra = 0


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'sender', 'message_type', 'content_preview', 'created_at', 'is_deleted']
    list_filter = ['message_type', 'is_deleted', 'created_at']
    search_fields = ['content', 'sender__username', 'room__name']
    raw_id_fields = ['room', 'sender']
    inlines = [ChatFileInline]
    ordering = ['-created_at']

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '內容預覽'


@admin.register(ChatFile)
class ChatFileAdmin(admin.ModelAdmin):
    list_display = ['original_name', 'message', 'file_size_display', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['original_name', 'message__content']
    raw_id_fields = ['message']


@admin.register(ChatFileDownloadLog)
class ChatFileDownloadLogAdmin(admin.ModelAdmin):
    list_display = ['file', 'downloaded_by', 'downloaded_at', 'ip_address']
    list_filter = ['downloaded_at']
    search_fields = ['file__original_name', 'downloaded_by__username', 'downloaded_by__first_name', 'downloaded_by__last_name']
    raw_id_fields = ['file', 'downloaded_by']
