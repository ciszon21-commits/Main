from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Restaurant, MenuItem, LunchOrder, RestaurantSchedule
from .forms import LunchOrderForm, MenuImageForm, RestaurantCreateForm
import datetime
import calendar
import json
from .utils import NATIONAL_HOLIDAYS_2026, CATEGORY_META, is_past_order_cutoff, is_past_schedule_cutoff


def calendar_view(request):
    """日曆首頁"""
    today = timezone.now().date()
    
    # 從 utils 取得 2026 年國定假日
    
    # 取得當前月份參數，優先使用 GET，其次使用 Session，最後預設為本月
    year_param = request.GET.get('year')
    month_param = request.GET.get('month')
    
    if year_param and month_param:
        try:
            year = int(year_param)
            month = int(month_param)
            # 更新 Session
            request.session['calendar_year'] = year
            request.session['calendar_month'] = month
        except ValueError:
            year = today.year
            month = today.month
    else:
        # 若無參數，預設為本月 (不從 Session 讀取，以免使用者想回首頁時還停留在舊月份)
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
        
        # 計算是否超過今日截止時間 (10:15)
        is_past_cutoff_time = is_past_order_cutoff(date_obj, today)
        
        # 計算是否超過今日排程設定時間 (11:00)
        is_past_schedule_cutoff_time = is_past_schedule_cutoff(date_obj, today)

        day_info = {
            'date': date_obj,
            'day': day,
            'restaurant': restaurant,
            'is_today': date_obj == today,
            'is_past': date_obj < today,
            'is_past_cutoff': is_past_cutoff_time,
            'is_past_schedule_cutoff': is_past_schedule_cutoff_time,
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
    """API: 設定每日店家 (僅限管理員)"""
    if request.method == 'POST':
        # 已認證但非管理員 → 拒絕
        if request.user.is_authenticated and not request.user.is_staff:
            messages.error(request, '僅限管理員可以設定店家排程')
            return redirect('lunchorder:calendar_view')
        date_str = request.POST.get('date')
        restaurant_id = request.POST.get('restaurant_id')
        action = request.POST.get('action')
        
        # 取得年份和月份參數，以便重導向回原本的月份
        year = request.POST.get('year')
        month = request.POST.get('month')
        
        base_url = reverse('lunchorder:calendar_view')
        if year and month:
            next_url = f"{base_url}?year={year}&month={month}"
        else:
            next_url = base_url
        
        if date_str:
            try:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # 使用 utils 中定義的 NATIONAL_HOLIDAYS_2026
                
                # 11:00 AM排程時間檢查
                today_local = timezone.localtime(timezone.now()).date()
                if is_past_schedule_cutoff(date_obj, today_local):
                     messages.error(request, '每日早上 11:00 後無法再設定或更換今日的店家')
                     return redirect(next_url)

                # 週日檢查
                if date_obj.weekday() == 6 and action != 'delete':
                     messages.error(request, '週日無法排程')
                     return redirect(next_url)
                
                # 國定假日檢查
                if date_obj in NATIONAL_HOLIDAYS_2026 and action != 'delete':
                     messages.error(request, '國定假日無法排程')
                     return redirect(next_url)

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
            
        return redirect(next_url)

    return redirect('lunchorder:calendar_view')


def order_list(request):
    """訂單列表 (公開)"""
    today = timezone.now().date()

    # ---- 篩選參數 ----
    filter_year = request.GET.get('year')
    filter_month = request.GET.get('month')

    try:
        filter_year = int(filter_year) if filter_year else None
        filter_month = int(filter_month) if filter_month else None
    except ValueError:
        filter_year = None
        filter_month = None
    # 如果沒有指定月份，預設為最新有訂單的月份
    if not filter_year or not filter_month:
        latest = LunchOrder.objects.order_by('-order_date').values_list('order_date', flat=True).first()
        if latest:
            filter_year = latest.year
            filter_month = latest.month
        else:
            filter_year = today.year
            filter_month = today.month

    # 基礎 queryset — 永遠按月篩選
    orders_qs = LunchOrder.objects.select_related(
        'menu_item', 'menu_item__restaurant'
    ).filter(
        order_date__year=filter_year,
        order_date__month=filter_month,
    )

    orders = orders_qs.order_by('-order_date', '-created_at')[:100]

    # ---- 取得所有可用的年月 (供篩選下拉選單) ----
    available_months_qs = (
        LunchOrder.objects.values('order_date__year', 'order_date__month')
        .distinct()
        .order_by('-order_date__year', '-order_date__month')
    )
    available_months = [
        {
            'year': m['order_date__year'],
            'month': m['order_date__month'],
            'label': f"{m['order_date__year']}年{m['order_date__month']}月",
            'selected': (filter_year == m['order_date__year'] and filter_month == m['order_date__month']),
        }
        for m in available_months_qs
    ]

    # ---- 圓餅圖統計 ----
    # chart_year 可獨立於月份篩選，有自己的 GET 參數
    chart_year_param = request.GET.get('chart_year')
    try:
        chart_year = int(chart_year_param) if chart_year_param else None
    except ValueError:
        chart_year = None
    if not chart_year:
        chart_year = filter_year if filter_year else today.year

    # 取得所有有訂單的年份 (供年份下拉選單)
    year_values = list(
        LunchOrder.objects.values_list('order_date__year', flat=True)
        .distinct()
        .order_by('-order_date__year')
    )
    if today.year not in year_values:
        year_values.insert(0, today.year)
    available_years = [
        {'year': y, 'selected': y == chart_year}
        for y in year_values
    ]

    # 1. 每月花費統計 (整年)
    monthly_spending = (
        LunchOrder.objects.filter(order_date__year=chart_year)
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

    # 2. 種類分佈統計 (依篩選月份或整年)
    category_display_map = dict(MenuItem.CATEGORY_CHOICES)
    cat_filter = LunchOrder.objects.filter(order_date__year=chart_year)
    if filter_month:
        cat_filter = cat_filter.filter(order_date__month=filter_month)

    category_spending = (
        cat_filter
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

    # ---- 篩選月份小計 ----
    if filter_year and filter_month:
        filter_month_total = int(
            LunchOrder.objects.filter(
                order_date__year=filter_year,
                order_date__month=filter_month,
            ).aggregate(
                total=Coalesce(
                    Sum(F('menu_item__price') * F('quantity'), output_field=DecimalField()),
                    0, output_field=DecimalField()
                )
            )['total']
        )
    else:
        filter_month_total = None

    context = {
        'orders': orders,
        'today': today,
        'current_year': chart_year,
        'total_year_spending': int(total_year_spending),
        'month_labels_json': json.dumps(month_labels),
        'month_data_json': json.dumps(month_data),
        'cat_labels_json': json.dumps(cat_labels),
        'cat_data_json': json.dumps(cat_data),
        # 篩選相關
        'available_months': available_months,
        'filter_year': filter_year,
        'filter_month': filter_month,
        'filter_month_total': filter_month_total,
        # 年份篩選
        'available_years': available_years,
        'chart_year': chart_year,
    }
    return render(request, 'LunchOrder/order_list.html', context)


def order_delete(request, order_id):
    """刪除訂單 (僅限當日)"""
    order = get_object_or_404(LunchOrder, id=order_id)
    today = timezone.localtime(timezone.now()).date()
    
    if order.order_date >= today:
        order.delete()
        messages.success(request, '訂單已刪除')
    else:
        messages.error(request, '無法刪除過去的訂單')
        
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

    today = timezone.localtime(timezone.now()).date()
    now = timezone.localtime(timezone.now())
    # 檢查是否超過截止時間
    is_past_cutoff = is_past_order_cutoff(target_date, today, now)

    if is_past_cutoff:
        return render(request, 'LunchOrder/order_cutoff.html')

    if request.method == 'POST':
        form = LunchOrderForm(request.POST) # 先綁定資料，以便之後驗證或傳遞

        # Check for reservation confirmation
        is_future_order = target_date > today
        is_confirmed = request.POST.get('confirmed') == 'true'

        if is_future_order and not is_confirmed:
             # 必須設定正確的 queryset，否則驗證會失敗 (為了顯示正確的品項名稱)
            if target_restaurant:
                form.fields['menu_item'].queryset = MenuItem.objects.filter(
                    restaurant=target_restaurant,
                    is_available=True
                )
            
            if form.is_valid():
                # 取得選購的餐點名稱供顯示
                menu_item = form.cleaned_data['menu_item']
                context = {
                    'form': form,
                    'target_date': target_date,
                    'target_restaurant': target_restaurant,
                    'menu_item_name': menu_item.name,
                }
                return render(request, 'LunchOrder/order_confirm_reservation.html', context)
            else:
                 messages.error(request, '表單驗證失敗，請確認所有欄位已填寫')
                 # 這裡可以選擇直接回傳錯誤，或者讓流程繼續走下去顯示錯誤在原表單
                 # 為了簡單起見，這裡不 return，讓它掉到下面原本的逻辑去處理顯示錯誤 (或者這裡直接 return redirect)
                 # 但為了讓使用者修正，我們應該 fall through to render the form with errors.
                 pass 

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
    
    
    
    categories = {}
    for item in menu_queryset:
        cat_key = item.category or 'single'
        if cat_key not in categories:
            meta = CATEGORY_META.get(cat_key, {'name': cat_key, 'icon': 'fa-utensils'})
            categories[cat_key] = {'name': meta['name'], 'icon': meta['icon'], 'items': []}
        categories[cat_key]['items'].append(item)
    
    
    context = {
        'form': form,
        'menu_categories': categories,
        'target_date': target_date,
        'target_restaurant': target_restaurant,
        'is_past_cutoff': is_past_cutoff,
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

    # 收集每個品項的備註
    notes_by_item = {}
    for order in orders.filter(notes__gt='').values('menu_item__name', 'notes', 'employee_name'):
        item_name = order['menu_item__name']
        if item_name not in notes_by_item:
            notes_by_item[item_name] = []
        notes_by_item[item_name].append(order['notes'])
    
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
        'notes_by_item': notes_by_item,
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


def admin_list(request):
    """管理員名單"""
    from django.contrib.auth.models import User

    admins = User.objects.filter(is_staff=True).select_related('profile').order_by('username')

    admin_data = []
    for user in admins:
        profile = getattr(user, 'profile', None)
        admin_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': profile.emp_email if profile and profile.emp_email else user.email,
            'department': profile.dept_display if profile else '—',
            'company': profile.company_display if profile else '—',
            'is_superuser': user.is_superuser,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
        })

    context = {
        'admin_data': admin_data,
        'total_count': len(admin_data),
    }
    return render(request, 'LunchOrder/admin_list.html', context)


def admin_search_users(request):
    """API: 搜尋非管理員使用者 (供新增管理員用)"""
    from django.contrib.auth.models import User
    from django.db.models import Q

    q = request.GET.get('q', '').strip()
    if not q or len(q) < 1:
        return JsonResponse([], safe=False)

    users = User.objects.filter(is_staff=False).filter(
        Q(username__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q) |
        Q(profile__emp_name__icontains=q)
    ).select_related('profile').distinct()[:10]

    results = []
    for user in users:
        profile = getattr(user, 'profile', None)
        results.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'department': profile.dept_display if profile else '—',
            'company': profile.company_display if profile else '—',
        })

    return JsonResponse(results, safe=False)


def admin_add(request):
    """POST: 將使用者設為管理員 (is_staff=True)"""
    if request.method == 'POST':
        from django.contrib.auth.models import User
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                user.is_staff = True
                user.save(update_fields=['is_staff'])
                profile = getattr(user, 'profile', None)
                name = user.get_full_name() or user.username
                messages.success(request, f'已將「{name}」設為管理員')
            except User.DoesNotExist:
                messages.error(request, '找不到該使用者')
        else:
            messages.error(request, '未指定使用者')
    return redirect('lunchorder:admin_list')


def admin_remove(request):
    """POST: 移除管理員權限 (is_staff=False)"""
    if request.method == 'POST':
        from django.contrib.auth.models import User
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                if user.is_superuser:
                    messages.error(request, '無法移除超級管理員的權限')
                else:
                    user.is_staff = False
                    user.save(update_fields=['is_staff'])
                    profile = getattr(user, 'profile', None)
                    name = user.get_full_name() or user.username
                    messages.success(request, f'已移除「{name}」的管理員權限')
            except User.DoesNotExist:
                messages.error(request, '找不到該使用者')
        else:
            messages.error(request, '未指定使用者')
    return redirect('lunchorder:admin_list')

