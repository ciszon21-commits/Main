"""
GeoDataHub Admin
=================
Django Admin 配置
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import GeoCategory, GeoLocation, GeoDataSource, DataTag, GeoDataView


@admin.register(DataTag)
class DataTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(GeoCategory)
class GeoCategoryAdmin(admin.ModelAdmin):
    list_display = ['icon_display', 'name', 'color_display', 'opensearch_pattern', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']

    def icon_display(self, obj):
        return obj.icon
    icon_display.short_description = '圖示'

    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 2px 10px; border: 2px solid #000;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = '顏色'


@admin.register(GeoLocation)
class GeoLocationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'city', 'country', 'geometry_type', 'is_manually_adjusted', 'created_at']
    list_filter = ['geometry_type', 'country', 'is_manually_adjusted']
    search_fields = ['address', 'city', 'district']
    readonly_fields = ['geo_hash', 'created_at', 'updated_at']
    
    fieldsets = (
        ('座標', {
            'fields': ('latitude', 'longitude', 'accuracy', 'is_manually_adjusted')
        }),
        ('地址資訊', {
            'fields': ('address', 'city', 'district', 'country')
        }),
        ('幾何資料', {
            'fields': ('geometry_type', 'geometry_data'),
            'classes': ('collapse',)
        }),
        ('系統資訊', {
            'fields': ('geo_hash', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GeoDataSource)
class GeoDataSourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'source_type', 'location_display', 'is_visible', 'view_count', 'created_by', 'created_at']
    list_filter = ['source_type', 'category', 'is_visible', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'location__address']
    raw_id_fields = ['location', 'created_by']
    filter_horizontal = ['tags']
    readonly_fields = ['file_size', 'file_type', 'view_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('title', 'description', 'source_type', 'category', 'tags')
        }),
        ('地理位置', {
            'fields': ('location',)
        }),
        ('檔案上傳', {
            'fields': ('file', 'file_size', 'file_type', 'thumbnail'),
            'classes': ('collapse',)
        }),
        ('外部連結', {
            'fields': ('external_url',),
            'classes': ('collapse',)
        }),
        ('OpenSearch 參考', {
            'fields': ('opensearch_index', 'opensearch_doc_id'),
            'classes': ('collapse',)
        }),
        ('中繼資料', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('狀態', {
            'fields': ('is_visible', 'is_featured', 'view_count')
        }),
        ('系統資訊', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def location_display(self, obj):
        if obj.location:
            return f"({obj.location.latitude:.4f}, {obj.location.longitude:.4f})"
        return '-'
    location_display.short_description = '座標'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GeoDataView)
class GeoDataViewAdmin(admin.ModelAdmin):
    list_display = ['source', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['source__title', 'user__username', 'ip_address']
    raw_id_fields = ['source', 'user']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'
