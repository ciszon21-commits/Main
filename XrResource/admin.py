from django.contrib import admin
from .models import (
    EquipmentCategory, XrEquipment, XrSupportRecord, GoProRentalRecord, 
    XrBulkItem, XrRentalRecord, XrUserProfile, RentalNature, 
    XrRentalEquipment, XrRentalAttachment
)

@admin.register(RentalNature)
class RentalNatureAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

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
@admin.register(XrBulkItem)
class XrBulkItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'total_count', 'available_count', 'reserved_count')
    list_filter = ('section',)
    search_fields = ('name',)

class XrRentalEquipmentInline(admin.TabularInline):
    model = XrRentalEquipment
    extra = 0

@admin.register(XrRentalRecord)
class XrRentalRecordAdmin(admin.ModelAdmin):
    list_display = ('activity_name', 'nature', 'borrower_name', 'activity_date', 'status', 'created_at')
    list_filter = ('status', 'nature', 'activity_date')
    search_fields = ('activity_name', 'borrower_name', 'borrower_id')
    # filter_horizontal = ('equipments',) # 經由 through 中間表時不可用
    inlines = [XrRentalEquipmentInline]

@admin.register(XrUserProfile)
class XrUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_user_name', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__last_name', 'user__first_name')

    def get_readonly_fields(self, request, obj=None):
        if obj: # 編輯模式
            return ('user',)
        return () # 新增模式可以選擇使用者

    def get_user_name(self, obj):
        return f"{obj.user.last_name}{obj.user.first_name}"
    get_user_name.short_description = '姓名'

@admin.register(XrRentalAttachment)
class XrRentalAttachmentAdmin(admin.ModelAdmin):
    list_display = ('rental_record', 'file', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('rental_record__activity_name',)

# 移除先前的 User 整合，保持在 XrResource 內獨立管理
