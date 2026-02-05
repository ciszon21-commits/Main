from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Restaurant, MenuItem, LunchOrder
from .forms import LunchOrderForm


def order_list(request):
    """訂單列表 (公開)"""
    orders = LunchOrder.objects.select_related(
        'menu_item', 'menu_item__restaurant'
    ).all()[:50]
    
    context = {
        'orders': orders,
    }
    return render(request, 'LunchOrder/order_list.html', context)


def order_create(request):
    """新增訂單 (公開)"""
    if request.method == 'POST':
        form = LunchOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.employee = None
            order.order_date = timezone.now().date()  # 自動設定今天日期
            order.save()
            messages.success(request, '訂單建立成功！')
            return redirect('lunchorder:order_list')
    else:
        form = LunchOrderForm()
    
    # 取得所有可用菜單並分類
    menu_items = MenuItem.objects.filter(is_available=True).order_by('price')
    
    categories = {
        'chicken': {'name': '雞肉餐盒', 'icon': 'fa-drumstick-bite', 'items': []},
        'pork': {'name': '豬肉餐盒', 'icon': 'fa-bacon', 'items': []},
        'beef': {'name': '牛肉餐盒', 'icon': 'fa-cow', 'items': []},
        'fish': {'name': '鮮魚餐盒', 'icon': 'fa-fish', 'items': []},
        'veg': {'name': '蔬食餐盒', 'icon': 'fa-carrot', 'items': []},
        'single': {'name': '單點品項', 'icon': 'fa-utensils', 'items': []},
        'drink': {'name': '冷泡茶飲', 'icon': 'fa-glass-water', 'items': []},
    }
    
    for item in menu_items:
        name = item.name
        if '雞' in name:
            categories['chicken']['items'].append(item)
        elif '豬' in name or '里肌' in name or '排骨' in name or '軟骨' in name:
            categories['pork']['items'].append(item)
        elif '牛' in name:
            categories['beef']['items'].append(item)
        elif '魚' in name or '鯖' in name:
            categories['fish']['items'].append(item)
        elif '蔬' in name or '菇' in name or '蛋' in name or '地瓜' in name or '飯' in name or '青菜' in name:
            # 這裡稍微混雜了單點的蔬食，先歸類為蔬食/單點
            if item.price < 100:
                categories['single']['items'].append(item)
            else:
                categories['veg']['items'].append(item)
        elif '茶' in name:
            categories['drink']['items'].append(item)
        else:
            categories['single']['items'].append(item)
            
    # 移除空分類
    categories = {k: v for k, v in categories.items() if v['items']}
    
    context = {
        'form': form,
        'menu_categories': categories,
    }
    return render(request, 'LunchOrder/order_form.html', context)


def order_statistics(request):
    """統計報表 (公開)"""
    # 取得篩選條件
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    orders = LunchOrder.objects.all()
    
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__lte=date_to)
    
    # 按員工統計消費金額
    employee_stats = orders.values('employee_name').annotate(
        total_orders=Sum('quantity'),
        total_amount=Coalesce(
            Sum(
                F('quantity') * F('menu_item__price'),
                output_field=DecimalField()
            ),
            0
        )
    ).order_by('-total_amount')
    
    # 總金額
    total_amount = orders.aggregate(
        total=Coalesce(
            Sum(
                F('quantity') * F('menu_item__price'),
                output_field=DecimalField()
            ),
            0
        )
    )['total']
    
    context = {
        'employee_stats': employee_stats,
        'total_amount': total_amount,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'LunchOrder/order_statistics.html', context)


def get_menu_items(request, restaurant_id):
    """AJAX: 取得便當店菜單項目"""
    menu_items = MenuItem.objects.filter(
        restaurant_id=restaurant_id,
        is_available=True
    ).values('id', 'name', 'price')
    
    return JsonResponse(list(menu_items), safe=False)
