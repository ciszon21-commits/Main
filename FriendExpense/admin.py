from django.contrib import admin
from .models import ExpenseGroup, Member, Expense, ExpenseSplit


class MemberInline(admin.TabularInline):
    model = Member
    extra = 1


class ExpenseSplitInline(admin.TabularInline):
    model = ExpenseSplit
    extra = 1


@admin.register(ExpenseGroup)
class ExpenseGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'member_count', 'total_expense']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    inlines = [MemberInline]

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = '成員數'

    def total_expense(self, obj):
        return f"${obj.get_total_expense():,.2f}"
    total_expense.short_description = '總支出'


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'user', 'created_at', 'balance_display']
    list_filter = ['group', 'created_at']
    search_fields = ['name', 'group__name']

    def balance_display(self, obj):
        balance = obj.get_balance()
        if balance > 0:
            return f"+${balance:,.2f}"
        elif balance < 0:
            return f"-${abs(balance):,.2f}"
        return "$0.00"
    balance_display.short_description = '淨額'


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'paid_by', 'group', 'expense_date']
    list_filter = ['group', 'expense_date']
    search_fields = ['description', 'notes']
    inlines = [ExpenseSplitInline]


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ['expense', 'member', 'amount']
    list_filter = ['expense__group']
