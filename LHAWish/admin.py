from django.contrib import admin
from .models import Post, Comment, PostInteraction, Petition, Endorsement, PetitionComment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'type', 'category', 'status', 'author', 'created_at']
    list_filter = ['type', 'status', 'category']
    search_fields = ['title', 'content', 'author__username', 'author__last_name']
    list_per_page = 30
    date_hierarchy = 'created_at'
    raw_id_fields = ['author']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'is_official', 'created_at']
    list_filter = ['is_official', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['post', 'author']


@admin.register(PostInteraction)
class PostInteractionAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'liked', 'saved']
    list_filter = ['liked', 'saved']
    raw_id_fields = ['post', 'user']


@admin.register(Petition)
class PetitionAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'assigned_group', 'proposer', 'endorsement_threshold', 'created_at']
    list_filter = ['status', 'assigned_group']
    search_fields = ['title', 'content', 'proposer__username', 'proposer__last_name']
    list_per_page = 30
    date_hierarchy = 'created_at'
    raw_id_fields = ['proposer', 'response_by']
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'content', 'proposer', 'assigned_group', 'is_anonymous', 'display_name')
        }),
        ('狀態管理', {
            'fields': ('status', 'endorsement_threshold', 'deadline')
        }),
        ('撤案', {
            'fields': ('withdraw_reason',),
            'classes': ('collapse',),
        }),
        ('回應', {
            'fields': ('response_content', 'response_at', 'response_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Endorsement)
class EndorsementAdmin(admin.ModelAdmin):
    list_display = ['petition', 'user', 'created_at']
    raw_id_fields = ['petition', 'user']


@admin.register(PetitionComment)
class PetitionCommentAdmin(admin.ModelAdmin):
    list_display = ['petition', 'author', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['petition', 'author']
