from django.contrib import admin
from .models import Project, Discipline, Stage, QuantityFile, PriceInquiryFile, BudgetFile, FinalBudgetFile, PriceAdjustment, AuditLog

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status', 'created_at', 'deleted_at')
    search_fields = ('code', 'name')
    list_filter = ('status', 'deleted_at')

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('project', 'code', 'name', 'responsible_user', 'is_overall')
    search_fields = ('code', 'name', 'project__name')
    list_filter = ('is_overall', 'project')

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'order', 'deadline')
    list_filter = ('project',)

@admin.register(QuantityFile)
class QuantityFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'discipline', 'version', 'uploaded_by', 'is_submitted')
    list_filter = ('project', 'is_submitted')

@admin.register(PriceInquiryFile)
class PriceInquiryFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'discipline', 'version', 'uploaded_by', 'is_submitted')
    list_filter = ('project', 'is_submitted')

@admin.register(BudgetFile)
class BudgetFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'discipline', 'budget_type', 'version', 'is_submitted')
    list_filter = ('project', 'budget_type', 'is_submitted')

@admin.register(FinalBudgetFile)
class FinalBudgetFileAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'file_type', 'version', 'is_confidential', 'is_submitted')
    list_filter = ('project', 'file_type', 'is_submitted')

@admin.register(PriceAdjustment)
class PriceAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('project', 'discipline', 'item_code', 'item_name', 'original_price', 'adjusted_price')
    search_fields = ('item_code', 'item_name')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id')
    list_filter = ('action', 'model_name')
    search_fields = ('user__username', 'model_name')
    readonly_fields = ('timestamp',)
