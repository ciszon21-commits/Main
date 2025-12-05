from django.contrib import admin
from .models import RndRequest, RndRequestVote


@admin.register(RndRequest)
class RndRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_by', 'priority_level', 'status', 'vote_score', 'created_at']
    list_filter = ['priority_level', 'status', 'created_at']
    search_fields = ['title', 'demand_quantity', 'data_source']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'created_by', 'status', 'priority_level')
        }),
        ('需求內容', {
            'fields': ('demand_quantity', 'data_source', 'processing_flow', 'expected_outcome')
        }),
        ('時間資訊', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(RndRequestVote)
class RndRequestVoteAdmin(admin.ModelAdmin):
    list_display = ['request', 'user', 'vote_type', 'voted_at']
    list_filter = ['vote_type', 'voted_at']
    search_fields = ['request__title', 'user__username']
    readonly_fields = ['voted_at']
    ordering = ['-voted_at']
