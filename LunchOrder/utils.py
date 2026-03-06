import datetime
from django.utils import timezone

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

# 餐點分類 metadata
CATEGORY_META = {
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


def is_past_order_cutoff(target_date, today, current_time=None):
    """
    檢查是否超過今日的訂購截止時間 (當天 10:15)
    If target_date is not today, it's not past cutoff time if target_date > today.
    (If target_date < today it might be past cutoff, but typically we only care about today's cutoff)
    This function primarily checks if order_date == today and time > 10:15
    """
    if target_date != today:
        return False
        
    if current_time:
        now_local = current_time
    else:
        now_local = timezone.localtime(timezone.now())
        
    cutoff_time = now_local.replace(hour=10, minute=15, second=0, microsecond=0)
    return now_local > cutoff_time


def is_past_schedule_cutoff(target_date, today, current_time=None):
    """
    檢查是否超過今日的排程設定截止時間 (當天 11:00)
    """
    if target_date != today:
        return False
        
    if current_time:
        now_local = current_time
    else:
        now_local = timezone.localtime(timezone.now())
        
    cutoff_time = now_local.replace(hour=11, minute=0, second=0, microsecond=0)
    return now_local > cutoff_time
