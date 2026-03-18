from django.contrib import admin
from .models import XrEquipment, GoProAccessory, VrComputer, XrSupportRecord, GoProRentalRecord

@admin.register(XrEquipment)
class XrEquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'status', 'specifications')
    list_filter = ('status',)
    search_fields = ('name', 'serial_number', 'note')

@admin.register(GoProAccessory)
class GoProAccessoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'rented_quantity')
    search_fields = ('name',)

@admin.register(VrComputer)
class VrComputerAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'local_account', 'specifications')
    search_fields = ('serial_number', 'note')

@admin.register(XrSupportRecord)
class XrSupportRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'department', 'nature', 'equipment_count', 'support_people')
    list_filter = ('nature', 'date')
    search_fields = ('department', 'reason')
    filter_horizontal = ('rented_equipments',) # 讓多選更易用

@admin.register(GoProRentalRecord)
class GoProRentalRecordAdmin(admin.ModelAdmin):
    list_display = ('date', 'department', 'borrower', 'equipment')
    list_filter = ('date', 'department')
    search_fields = ('department', 'borrower', 'equipment', 'reason')
