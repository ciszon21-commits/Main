from django.contrib import admin
from .models import MLModel, ClashReport, ClassificationResult


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['model_type', 'is_active', 'uploaded_at', 'file']
    list_filter = ['model_type', 'is_active', 'uploaded_at']
    search_fields = ['description']
    readonly_fields = ['uploaded_at']
    fieldsets = [
        ('基本資訊', {
            'fields': ['model_type', 'file', 'is_active']
        }),
        ('詳細資訊', {
            'fields': ['description', 'uploaded_at']
        }),
    ]
    
    def get_list_display_links(self, request, list_display):
        return ['model_type']


@admin.register(ClashReport)
class ClashReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'uploaded_at', 'is_deleted']
    list_filter = ['is_deleted', 'uploaded_at']
    search_fields = ['title', 'user__username']
    readonly_fields = ['uploaded_at', 'deleted_at']
    
    def get_queryset(self, request):
        """包含已刪除的報告"""
        return ClashReport.objects.all()


@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'report', 'row_index', 'distance',
        'predicted_class', 'confidence', 'status'
    ]
    list_filter = ['predicted_class', 'status']
    search_fields = ['report__title', 'item1_type', 'item2_type']
    readonly_fields = ['created_at']
