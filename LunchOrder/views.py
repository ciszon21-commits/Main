from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum, F, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Restaurant, MenuItem, LunchOrder, RestaurantSchedule
from .forms import LunchOrderForm, MenuImageForm, RestaurantCreateForm
import datetime
import datetime
import calendar
import json


def calendar_view(request):
    """日曆首頁"""
    today = timezone.now().date()
    
    # 2026年國定假日（不含週六週日）
    NATIONAL_HOLIDAYS_2026 = {
        # 元旦
        datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 2),
        # 春節
        datetime.date(2026, 2, 16),
        datetime.date(2026, 2, 17),
        datetime.date(2026, 2, 18),
        datetime.date(2026, 2, 19),
        datetime.date(2026, 2, 20),
        # 二二八和平紀念日
        datetime.date(2026, 2, 27),
        # 兒童節 / 清明節
        datetime.date(2026, 4, 3),
        datetime.date(2026, 4, 6),
        # 勞動節
        datetime.date(2026, 5, 1),
        # 端午節
        datetime.date(2026, 5, 29),
        # 中秋節
        datetime.date(2026, 10, 2),
        # 國慶日
        datetime.date(2026, 10, 9),
        # 其他彈性放假 (依行政機關辦公日曆表)
    }
    
    # 取得當前月份參數，預設為本月
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)
    
    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = today.year
        month = today.month

    # 計算月份資訊
    _, num_days = calendar.monthrange(year, month)
    first_day = datetime.date(year, month, 1)
    
    # 取得當月所有排程
    schedules = RestaurantSchedule.objects.filter(
        date__year=year,
        date__month=month
    ).select_related('restaurant')
    
    schedule_map = {s.date: s.restaurant for s in schedules}
    
    # 建立日曆資料結構
    cal_data = []
    # 填充第一週前面的空白
    start_weekday = first_day.weekday() # 0=Mon, 6=Sun
    # 我們希望週日為第一天 (假設) 或者週一。通常 calendar 預設週一。
    # 這裡假設週一為第一天。
    
    current_week = []
    # 前面補空
    for _ in range(start_weekday):
        current_week.append(None)
        
    for day in range(1, num_days + 1):
        date_obj = datetime.date(year, month, day)
        restaurant = schedule_map.get(date_obj)
        is_holiday = date_obj in NATIONAL_HOLIDAYS_2026
        
        day_info = {
            'date': date_obj,
            'day': day,
            'restaurant': restaurant,
            'is_today': date_obj == today,
            'is_past': date_obj < today,
            'is_sunday': date_obj.weekday() == 6,
            'is_holiday': is_holiday,
        }
        current_week.append(day_info)
        
        if len(current_week) == 7:
            cal_data.append(current_week)
            current_week = []
            
    # 補滿最後一週
    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        cal_data.append(current_week)
        
    # 所有餐廳列表 (供選擇用)
    restaurants = Restaurant.objects.filter(is_active=True)
    
    # 下個/上個月導航
    next_month_date = first_day + datetime.timedelta(days=32)
    next_year, next_month = next_month_date.year, next_month_date.month
    
    prev_month_date = first_day - datetime.timedelta(days=1)
    prev_year, prev_month = prev_month_date.year, prev_month_date.month

    context = {
        'calendar': cal_data,
        'year': year,
        'month': month,
        'restaurants': restaurants,
        'next_year': next_year,
        'next_month': next_month,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'today': today,
    }
    return render(request, 'LunchOrder/calendar.html', context)


def set_daily_restaurant(request):
    """API: 設定每日店家"""
    if request.method == 'POST':
        date_str = request.POST.get('date')
        restaurant_id = request.POST.get('restaurant_id')
        action = request.POST.get('action')
        
        if date_str:
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # 國定假日列表
                NATIONAL_HOLIDAYS_2026 = {
                    datetime.date(2026, 1, 1), datetime.date(2026, 1, 2),
                    datetime.date(2026, 2, 16), datetime.date(2026, 2, 17),
                    datetime.date(2026, 2, 18), datetime.date(2026, 2, 19),
                    datetime.date(2026, 2, 20), datetime.date(2026, 2, 27),
                    datetime.date(2026, 4, 3), datetime.date(2026, 4, 6),
                    datetime.date(2026, 5, 1), datetime.date(2026, 5, 29),
                    datetime.date(2026, 10, 2), datetime.date(2026, 10, 9),
                }
                
                # 週日檢查
                if date_obj.weekday() == 6 and action != 'delete':
                     messages.error(request, '週日無法排程')
                     return redirect('lunchorder:calendar_view')
                
                # 國定假日檢查
                if date_obj in NATIONAL_HOLIDAYS_2026 and action != 'delete':
                     messages.error(request, '國定假日無法排程')
                     return redirect('lunchorder:calendar_view')

                if action == 'delete':
                    RestaurantSchedule.objects.filter(date=date_obj).delete()
                    # 同步刪除該日所有訂單
                    deleted_count = LunchOrder.objects.filter(order_date=date_obj).delete()[0]
                    msg = f'已移除 {date_str} 的排程'
                    if deleted_count:
                        msg += f'，並刪除 {deleted_count} 筆相關訂單'
                    messages.success(request, msg)
                elif restaurant_id:
                    restaurant = Restaurant.objects.get(id=restaurant_id)
                    # 檢查是否為更換店家（已有不同排程）
                    old_schedule = RestaurantSchedule.objects.filter(date=date_obj).first()
                    if old_schedule and old_schedule.restaurant_id != int(restaurant_id):
                        # 更換店家，刪除該日所有訂單
                        deleted_count = LunchOrder.objects.filter(order_date=date_obj).delete()[0]
                        if deleted_count:
                            messages.warning(request, f'因更換店家，已刪除 {deleted_count} 筆原訂單')
                    RestaurantSchedule.objects.update_or_create(
                        date=date_obj,
                        defaults={'restaurant': restaurant}
                    )
                    messages.success(request, f'已設定 {date_str} 為 {restaurant.name}')
                else:
                    messages.error(request, '資料不完整')
            except Exception as e:
                messages.error(request, f'操作失敗: {str(e)}')
        else:
            messages.error(request, '日期錯誤')
            
    return redirect('lunchorder:calendar_view')


def order_list(request):
    """訂單列表 (公開)"""
    orders = LunchOrder.objects.select_related(
        'menu_item', 'menu_item__restaurant'
    ).order_by('-order_date', '-created_at')[:50]
    
    today = timezone.now().date()
    current_year = today.year
    
    # 1. 每月花費統計
    monthly_spending = (
        LunchOrder.objects.filter(order_date__year=current_year)
        .values('order_date__month')
        .annotate(
            total=Sum(
                F('menu_item__price') * F('quantity'),
                output_field=DecimalField()
            )
        )
        .order_by('order_date__month')
    )
    
    month_labels = []
    month_data = []
    total_year_spending = 0
    
    for entry in monthly_spending:
        val = int(entry['total'])
        month_labels.append(f"{entry['order_date__month']}月 (${val:,})")
        month_data.append(val)
        total_year_spending += val
    
    # 2. 種類分佈統計
    category_display_map = dict(MenuItem.CATEGORY_CHOICES)
    category_spending = (
        LunchOrder.objects.filter(order_date__year=current_year)
        .values('menu_item__category')
        .annotate(
            total=Sum(
                F('menu_item__price') * F('quantity'),
                output_field=DecimalField()
            )
        )
        .order_by('-total')
    )
    
    cat_labels = []
    cat_data = []
    for entry in category_spending:
        cat_key = entry['menu_item__category'] or 'single'
        val = int(entry['total'])
        cat_name = category_display_map.get(cat_key, cat_key)
        cat_labels.append(f"{cat_name} (${val:,})")
        cat_data.append(val)
    
    context = {
        'orders': orders,
        'today': today,
        'current_year': current_year,
        'total_year_spending': int(total_year_spending),
        'month_labels_json': json.dumps(month_labels),
        'month_data_json': json.dumps(month_data),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
    }
    return render(request, 'LunchOrder/order_list.html', context)


def order_delete(request, order_id):
    """刪除訂單 (僅限當日)"""
    order = get_object_or_404(LunchOrder, id=order_id)
    today = timezone.now().date()
    
    if order.order_date == today:
        order.delete()
        messages.success(request, '訂單已刪除')
    else:
        messages.error(request, '只能刪除今日的訂單')
        
    return redirect('lunchorder:order_list')


def restaurant_list(request):
    """餐廳列表 (公開)"""
    restaurants = Restaurant.objects.filter(is_active=True)
    context = {
        'restaurants': restaurants,
    }
    return render(request, 'LunchOrder/restaurant_list.html', context)


def restaurant_create(request):
    """新增便當店"""
    if request.method == 'POST':
        form = RestaurantCreateForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            
            # 處理圖片上傳
            if request.FILES.get('image'):
                import os
                import time
                image_file = request.FILES['image']
                ext = os.path.splitext(image_file.name)[1]
                timestamp = int(time.time())
                new_filename = f"menu_{timestamp}{ext}"
                
                from django.conf import settings
                save_dir = os.path.join(settings.BASE_DIR, 'LunchOrder', 'static', 'LunchOrder')
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                
                save_path = os.path.join(save_dir, new_filename)
                with open(save_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                
                restaurant.image_file = new_filename
            
            restaurant.is_active = True
            restaurant.save()
            messages.success(request, f'已成功新增便當店：{restaurant.name}')
            return redirect('lunchorder:restaurant_list')
    else:
        form = RestaurantCreateForm()
    
    context = {
        'form': form,
    }
    return render(request, 'LunchOrder/restaurant_create.html', context)


def order_create(request):
    """新增訂單 (公開)"""
    # 取得日期參數，預設為今天
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = timezone.now().date()
    else:
        target_date = timezone.now().date()
        
    # 檢查該日期是否有排程
    schedule = RestaurantSchedule.objects.filter(date=target_date).first()
    target_restaurant = schedule.restaurant if schedule else None

    # 如果有傳入 restaurant_id，則優先使用該餐廳 (覆蓋排程)
    restaurant_id = request.GET.get('restaurant_id')
    if restaurant_id:
        try:
            target_restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            pass

    if request.method == 'POST':
        form = LunchOrderForm(request.POST)
        # 必須設定正確的 queryset，否則驗證會失敗
        if target_restaurant:
            form.fields['menu_item'].queryset = MenuItem.objects.filter(
                restaurant=target_restaurant,
                is_available=True
            )
        if form.is_valid():
            order = form.save(commit=False)
            order.employee = None
            order.order_date = target_date  # 使用目標日期
            order.save()
            messages.success(request, f'訂單建立成功！日期：{target_date}')
            return redirect('lunchorder:order_list')
        else:
            messages.error(request, '表單驗證失敗，請確認所有欄位已填寫')
    else:
        form = LunchOrderForm()
    
    # 設定表單的 queryset 為目標餐廳的菜單
    if target_restaurant:
        form.fields['menu_item'].queryset = MenuItem.objects.filter(
            restaurant=target_restaurant,
            is_available=True
        ).order_by('price')
    
    # 如果有指定餐廳 (排程或參數)，才載入菜單
    if target_restaurant:
        menu_queryset = MenuItem.objects.filter(
            restaurant=target_restaurant,
            is_available=True
        ).order_by('price')
    
    category_meta = {
        'chicken': {'name': '雞肉餐盒', 'icon': 'fa-drumstick-bite'},
        'duck': {'name': '鴨肉料理', 'icon': 'fa-feather'},
        'pork': {'name': '豬肉餐盒', 'icon': 'fa-bacon'},
        'beef': {'name': '牛肉餐盒', 'icon': 'fa-cow'},
        'fish': {'name': '鮮魚餐盒', 'icon': 'fa-fish'},
        'noodle': {'name': '麵食/粥品', 'icon': 'fa-bowl-food'},
        'soup': {'name': '精選湯品', 'icon': 'fa-mug-hot'},
        'veg': {'name': '蔬食餐盒', 'icon': 'fa-carrot'},
        'side': {'name': '美味小菜', 'icon': 'fa-utensils'},
        'single': {'name': '單點品項', 'icon': 'fa-utensils'},
        'drink': {'name': '冷泡茶飲', 'icon': 'fa-glass-water'},
        'other': {'name': '其他', 'icon': 'fa-ellipsis'},
    }
    
    categories = {}
    for item in menu_queryset:
        cat_key = item.category or 'single'
        if cat_key not in categories:
            meta = category_meta.get(cat_key, {'name': cat_key, 'icon': 'fa-utensils'})
            categories[cat_key] = {'name': meta['name'], 'icon': meta['icon'], 'items': []}
        categories[cat_key]['items'].append(item)
    
    
    context = {
        'form': form,
        'menu_categories': categories,
        'target_date': target_date,
        'target_restaurant': target_restaurant,
    }
    return render(request, 'LunchOrder/order_form.html', context)


def order_statistics(request):
    """每日訂單彙總報表"""
    today = timezone.now().date()
    
    # 取得選擇的日期，預設為今天
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today
    
    # 取得該日期的排程餐廳
    schedule = RestaurantSchedule.objects.filter(date=selected_date).select_related('restaurant').first()
    
    # 取得該日所有訂單
    orders = LunchOrder.objects.filter(
        order_date=selected_date
    ).select_related('menu_item', 'menu_item__restaurant').order_by('employee_name')
    
    # 總金額
    total_amount = orders.aggregate(
        total=Coalesce(
            Sum(
                F('quantity') * F('menu_item__price'),
                output_field=DecimalField()
            ),
            0,
            output_field=DecimalField()
        )
    )['total']
    
    # 總份數
    total_quantity = orders.aggregate(
        total=Coalesce(Sum('quantity'), 0, output_field=IntegerField())
    )['total']
    
    # 取得有訂單的日期列表（用於快速導航）
    order_dates = LunchOrder.objects.values_list(
        'order_date', flat=True
    ).distinct().order_by('-order_date')[:30]
    
    # 品項統計
    item_stats = orders.values(
        'menu_item__name', 
        'menu_item__price', 
        'menu_item__category',
        'menu_item__restaurant__name' # 如果當日有多家餐廳混訂，這會很有用
    ).annotate(
        total_qty=Sum('quantity'),
        total_price=Sum(F('quantity') * F('menu_item__price'), output_field=DecimalField())
    ).order_by('-total_qty')
    
    # 前一天/後一天導航
    prev_date = selected_date - datetime.timedelta(days=1)
    next_date = selected_date + datetime.timedelta(days=1)
    
    context = {
        'selected_date': selected_date,
        'schedule': schedule,
        'orders': orders,
        'total_amount': total_amount,
        'total_quantity': total_quantity,
        'item_stats': item_stats,
        'order_dates': order_dates,
        'today': today,
        'prev_date': prev_date,
        'next_date': next_date,
    }
    return render(request, 'LunchOrder/order_statistics.html', context)


def get_menu_items(request, restaurant_id):
    """AJAX: 取得便當店菜單項目"""
    menu_items = MenuItem.objects.filter(
        restaurant_id=restaurant_id,
        is_available=True
    ).values('id', 'name', 'price')
    
    return JsonResponse(list(menu_items), safe=False)


def restaurant_update_menu(request, restaurant_id):
    """更新餐廳菜單圖片與品項"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    # 建立 FormSet
    from django.forms import inlineformset_factory
    from .forms import MenuItemForm
    
    MenuItemFormSet = inlineformset_factory(
        Restaurant, MenuItem,
        form=MenuItemForm,
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = MenuImageForm(request.POST, request.FILES)
        formset = MenuItemFormSet(request.POST, instance=restaurant)
        
        # 優先處理圖片/電話/地址/名稱更新 (與 FormSet 分開驗證)
        if form.is_valid():
            # 更新基本資料
            if form.cleaned_data.get('name'):
                restaurant.name = form.cleaned_data['name']
            if form.cleaned_data.get('phone'):
                restaurant.phone = form.cleaned_data['phone']
            if form.cleaned_data.get('address'):
                restaurant.address = form.cleaned_data['address']
            
            # 處理圖片上傳 (如果有)
            if request.FILES.get('image'):
                image_file = request.FILES['image']
                
                # 產生唯一檔名
                import os
                import time
                ext = os.path.splitext(image_file.name)[1]
                timestamp = int(time.time())
                new_filename = f"menu_{restaurant.id}_{timestamp}{ext}"
                
                # 儲存路徑
                from django.conf import settings
                
                save_dir = os.path.join(settings.BASE_DIR, 'LunchOrder', 'static', 'LunchOrder')
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)
                    
                save_path = os.path.join(save_dir, new_filename)
                
                with open(save_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                
                restaurant.image_file = new_filename
            
            restaurant.save()
            
            # 如果是點擊「更新圖片/資訊」按鈕 (檢查是否只有基本資料更新)
            # 這裡簡單判斷：只要 form valid 且沒有 formset errors，就視為基本資料更新成功
            # 為了避免與 formset 衝突，我們可以在這裡直接回應，除非 formset 也有提交
            
            # 但為了讓使用者可以同時更新，我們繼續檢查 formset
            # 如果這次請求主要是為了更新圖片/資訊 (通常是點擊了上面的按鈕)
            if 'image' in request.FILES or form.cleaned_data.get('phone') != restaurant.phone or form.cleaned_data.get('address') != restaurant.address or form.cleaned_data.get('name') != restaurant.name:
                 # 如果真的有變更，就提示
                 pass

            # 為了確保「更新圖片」按鈕的體驗，如果有點擊該按鈕 (通常會是 submit)，
            # 我們假設使用者可能只改了這邊。
            # 但因為是一個 form，我們統一處理。
            
            # 為了符合之前的修復邏輯 (優先處理上方區塊)，我們檢查是否有上傳圖片或修改資料
            if request.FILES.get('image') or form.has_changed():
                 messages.success(request, f'已更新 {restaurant.name} 的基本資料與圖片！')
                 # 若不return，會繼續處理 formset，可能會覆蓋 message 或有其他邏輯
                 # 為了簡單，若有更動上方，就先 redirect
                 return redirect('lunchorder:restaurant_update_menu', restaurant_id=restaurant.id)
            
        if formset.is_valid():
            # 儲存菜單項目
            formset.save()
            
            messages.success(request, f'已更新 {restaurant.name} 的菜單與品項！')
            return redirect('lunchorder:restaurant_update_menu', restaurant_id=restaurant.id)
    else:
        form = MenuImageForm(initial={
            'name': restaurant.name,
            'phone': restaurant.phone,
            'address': restaurant.address
        })
        formset = MenuItemFormSet(instance=restaurant)
        
    context = {
        'restaurant': restaurant,
        'form': form,
        'formset': formset,
        'category_choices': MenuItem.CATEGORY_CHOICES,
    }
    return render(request, 'LunchOrder/restaurant_update_menu.html', context)


def menu_item_add(request, restaurant_id):
    """API: 新增菜單品項"""
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        import json
        data = json.loads(request.body)
        
        name = data.get('name', '').strip()
        price = data.get('price', 0)
        category = data.get('category', 'single')
        
        if not name:
            return JsonResponse({'success': False, 'error': '品項名稱不可為空'})
        
        item = MenuItem.objects.create(
            restaurant=restaurant,
            name=name,
            price=price,
            category=category,
            is_available=True
        )
        
        return JsonResponse({
            'success': True,
            'item': {
                'id': item.id,
                'name': item.name,
                'price': str(item.price),
                'category': item.category,
                'category_display': item.get_category_display(),
            }
        })
    return JsonResponse({'success': False, 'error': '無效請求'})



def menu_item_edit(request, restaurant_id, item_id):
    """API: 編輯菜單品項"""
    if request.method == 'POST':
        restaurant = get_object_or_404(Restaurant, id=restaurant_id)
        menu_item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
        
        import json
        try:
            data = json.loads(request.body)
            
            name = data.get('name', '').strip()
            price = data.get('price')
            category = data.get('category')
            
            if not name:
                return JsonResponse({'success': False, 'error': '品項名稱不能為空'})
                
            menu_item.name = name
            menu_item.price = price
            menu_item.category = category
            menu_item.save()
            
            return JsonResponse({
                'success': True,
                'item': {
                    'id': menu_item.id,
                    'name': menu_item.name,
                    'price': str(menu_item.price),
                    'category_display': menu_item.get_category_display(),
                    'category': menu_item.category
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def menu_item_delete(request, restaurant_id):
    """API: 刪除菜單品項"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        item_ids = data.get('item_ids', [])
        
        if not item_ids:
            return JsonResponse({'success': False, 'error': '未選擇品項'})
        
        deleted_count = MenuItem.objects.filter(
            id__in=item_ids,
            restaurant_id=restaurant_id
        ).delete()[0]
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count
        })
    return JsonResponse({'success': False, 'error': '無效請求'})


def restaurant_delete(request, restaurant_id):
    """刪除便當店 (包含圖片與菜單)"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        # 刪除圖片檔案
        if restaurant.image_file:
            import os
            from django.conf import settings
            image_path = os.path.join(settings.BASE_DIR, 'LunchOrder', 'static', 'LunchOrder', restaurant.image_file)
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass
        
        name = restaurant.name
        restaurant.delete()
        messages.success(request, f'已刪除餐廳：{name}')
        return redirect('lunchorder:restaurant_list')
    
    # 如果不是 POST，導回更新頁面 (雖然前端應該只送 POST)
    return redirect('lunchorder:restaurant_update_menu', restaurant_id=restaurant_id)
