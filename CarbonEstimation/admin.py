from django.contrib import admin
from .models import MainCategory, ComponentItem, Scenario, ScenarioData, SectionCategory, SectionItem, ScenarioSectionData


@admin.register(MainCategory)
class MainCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order']
    list_editable = ['order']
    search_fields = ['code', 'name']
    ordering = ['order', 'code']


@admin.register(ComponentItem)
class ComponentItemAdmin(admin.ModelAdmin):
    list_display = [
        'item_no', 'work_item', 'category', 'unit',
        'carbon_before', 'carbon_after', 'cost_before', 'cost_after'
    ]
    list_filter = ['category']
    search_fields = ['item_no', 'work_item']
    ordering = ['category__order', 'order', 'item_no']
    list_per_page = 50
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('category', 'item_no', 'work_item', 'unit', 'description', 'order')
        }),
        ('數量', {
            'fields': ('default_quantity',)
        }),
        ('碳排資料', {
            'fields': ('carbon_before', 'carbon_after', 'carbon_unit')
        }),
        ('費用資料', {
            'fields': ('cost_before', 'cost_after')
        }),
        ('其他資訊', {
            'fields': ('notes', 'reference'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SectionCategory)
class SectionCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order']
    list_editable = ['order']
    search_fields = ['code', 'name']
    ordering = ['order', 'code']


@admin.register(SectionItem)
class SectionItemAdmin(admin.ModelAdmin):
    list_display = ['work_item', 'category', 'unit', 'carbon_per_unit', 'order']
    list_filter = ['category']
    search_fields = ['work_item']
    ordering = ['category__order', 'order']
    list_per_page = 50
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('category', 'work_item', 'unit', 'order')
        }),
        ('碳排資料', {
            'fields': ('carbon_per_unit',)
        }),
        ('其他資訊', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
