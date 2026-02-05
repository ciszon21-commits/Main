from django.contrib import admin
from .models import ExpenseCategory, Participant, Expense, ExpenseSplit


class ExpenseSplitInline(admin.TabularInline):
    model = ExpenseSplit
    extra = 1


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'color', 'is_default', 'created_at']
    list_filter = ['is_default']
    search_fields = ['name']
    list_editable = ['is_default', 'color']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'email']
    list_editable = ['is_active']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['date', 'time', 'item_name', 'category', 'amount', 'paid_by', 'created_at']
    list_filter = ['category', 'date', 'paid_by']
    search_fields = ['item_name', 'note']
    date_hierarchy = 'date'
    inlines = [ExpenseSplitInline]
    list_per_page = 20


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ['expense', 'participant', 'share_amount']
    list_filter = ['participant']
    search_fields = ['expense__item_name', 'participant__name']
