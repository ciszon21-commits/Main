from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from .models import Restaurant, MenuItem, LunchOrder, RestaurantSchedule


@admin.register(RestaurantSchedule)
class RestaurantScheduleAdmin(admin.ModelAdmin):
    """便當店排程管理"""
    list_display = ['date', 'restaurant', 'created_at']
    list_filter = ['restaurant', 'date']
    date_hierarchy = 'date'


class MenuItemInline(admin.TabularInline):
    """菜單項目內嵌"""
    model = MenuItem
    extra = 1
    fields = ['name', 'price', 'description', 'is_available']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    """便當店管理"""
    list_display = ['name', 'phone', 'address', 'is_active', 'menu_count']
    list_filter = ['is_active']
    search_fields = ['name', 'phone', 'address']
    inlines = [MenuItemInline]

    def menu_count(self, obj):
        return obj.menu_items.count()
    menu_count.short_description = '品項數量'


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """菜單項目管理"""
    list_display = ['name', 'restaurant', 'price', 'is_available']
    list_filter = ['restaurant', 'is_available']
    search_fields = ['name', 'restaurant__name']


@admin.register(LunchOrder)
class LunchOrderAdmin(admin.ModelAdmin):
    """訂單管理"""
    list_display = ['order_date', 'employee_name', 'menu_item', 'quantity', 'get_subtotal', 'created_at']
    list_filter = ['order_date', 'menu_item__restaurant', 'employee']
    search_fields = ['employee_name', 'menu_item__name']
    date_hierarchy = 'order_date'
    readonly_fields = ['employee_name', 'created_at', 'updated_at']

    def get_subtotal(self, obj):
        return f"${obj.subtotal}"
    get_subtotal.short_description = '小計'

    def changelist_view(self, request, extra_context=None):
        """在列表頁面增加統計資訊"""
        # 取得查詢集
        queryset = self.get_queryset(request)
        
        # 計算每位員工的消費總額
        employee_stats = queryset.values('employee_name').annotate(
            total_amount=Sum(
                F('quantity') * F('menu_item__price'),
                output_field=DecimalField()
            )
        ).order_by('-total_amount')

        # 計算總金額
        total_amount = queryset.aggregate(
            total=Coalesce(
                Sum(
                    F('quantity') * F('menu_item__price'),
                    output_field=DecimalField()
                ),
                0
            )
        )['total']

        extra_context = extra_context or {}
        extra_context['employee_stats'] = employee_stats
        extra_context['total_amount'] = total_amount

        return super().changelist_view(request, extra_context=extra_context)
