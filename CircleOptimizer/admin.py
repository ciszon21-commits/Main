from django.contrib import admin
from .models import Shape, CircleConfig, Circle


class CircleInline(admin.TabularInline):
    """圓的內聯編輯器"""
    model = Circle
    extra = 0
    readonly_fields = ['circle_index', 'arc_length', 'start_angle', 'end_angle']


@admin.register(Shape)
class ShapeAdmin(admin.ModelAdmin):
    """Shape Admin"""
    list_display = ['name', 'points_count', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'points_count']


@admin.register(CircleConfig)
class CircleConfigAdmin(admin.ModelAdmin):
    """Circle Configuration Admin"""
    list_display = ['id', 'shape', 'config_type', 'total_area', 'is_optimized', 'created_at']
    list_filter = ['config_type', 'is_optimized', 'created_at']
    search_fields = ['shape__name']
    readonly_fields = ['created_at', 'updated_at', 'circle_count']
    inlines = [CircleInline]


@admin.register(Circle)
class CircleAdmin(admin.ModelAdmin):
    """Circle Admin"""
    list_display = ['id', 'config', 'circle_index', 'center_x', 'center_y', 'radius', 'arc_length']
    list_filter = ['config__config_type']
    search_fields = ['config__shape__name']
