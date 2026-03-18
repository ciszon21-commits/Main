from django.contrib import admin
from .models import EquipmentCategory, XrEquipment, XrSupportRecord, GoProRentalRecord

@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(XrEquipment)
class XrEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'section', 'category', 'status')
    list_filter = ('section', 'category', 'status')
    search_fields = ('name', 'serial_number', 'specifications')
    ordering = ('section', 'serial_number')

@admin.register(XrSupportRecord)
class XrSupportRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'department', 'nature', 'equipment_count')
    list_filter = ('nature', 'date')
    search_fields = ('department', 'reason')

@admin.register(GoProRentalRecord)
class GoProRentalRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'borrower', 'department', 'equipment')
    list_filter = ('date', 'department')
    search_fields = ('borrower', 'department', 'equipment')
