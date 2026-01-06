from django.contrib import admin
from .models import PatentApplication, PatentRebuttal, GrantedPatent, PatentAnnuity


class PatentRebuttalInline(admin.TabularInline):
    model = PatentRebuttal
    extra = 0
    fields = ['rebuttal_type', 'document_date', 'fee', 'notes']


class PatentAnnuityInline(admin.TabularInline):
    model = PatentAnnuity
    extra = 0
    fields = ['year', 'write_off_plan_number', 'write_off_date', 'notes']


@admin.register(PatentApplication)
class PatentApplicationAdmin(admin.ModelAdmin):
    list_display = ['plan_number', 'name', 'category', 'status', 'patent_firm', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['plan_number', 'name', 'patent_firm', 'firm_case_number']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PatentRebuttalInline]
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('plan_number', 'outsource_number', 'item_number', 'name', 'category')
        }),
        ('事務所資訊', {
            'fields': ('patent_firm', 'firm_case_number')
        }),
        ('狀態', {
            'fields': ('status',)
        }),
        ('系統資訊', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PatentRebuttal)
class PatentRebuttalAdmin(admin.ModelAdmin):
    list_display = ['application', 'rebuttal_type', 'document_date', 'fee', 'created_at']
    list_filter = ['rebuttal_type', 'document_date']
    search_fields = ['application__name', 'application__plan_number']
    readonly_fields = ['created_at']


@admin.register(GrantedPatent)
class GrantedPatentAdmin(admin.ModelAdmin):
    list_display = ['patent_number', 'patent_name', 'start_date', 'end_date', 'granted_at']
    list_filter = ['start_date', 'granted_at']
    search_fields = ['patent_number', 'patent_name', 'application__name']
    readonly_fields = ['granted_at', 'updated_at']
    inlines = [PatentAnnuityInline]
    
    fieldsets = (
        ('專利資訊', {
            'fields': ('application', 'patent_number', 'patent_name', 'patent_period', 'description')
        }),
        ('期間', {
            'fields': ('start_date', 'end_date')
        }),
        ('證書', {
            'fields': ('certificate',)
        }),
        ('系統資訊', {
            'fields': ('granted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PatentAnnuity)
class PatentAnnuityAdmin(admin.ModelAdmin):
    list_display = ['granted_patent', 'year', 'write_off_plan_number', 'write_off_date', 'created_at']
    list_filter = ['year', 'write_off_date']
    search_fields = ['granted_patent__patent_name', 'write_off_plan_number']
    readonly_fields = ['created_at']
