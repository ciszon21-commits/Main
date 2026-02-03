#!/usr/bin/env python
"""
清理試煉標題中的日期
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Trial
import re

print("=== 清理試煉標題 ===\n")

# 獲取所有每日試煉
daily_trials = Trial.objects.filter(is_daily=True)
print(f"找到 {daily_trials.count()} 個每日試煉\n")

updated_count = 0
for trial in daily_trials:
    old_title = trial.title
    
    # 移除標題中的日期部分 [YYYY-MM-DD]
    new_title = re.sub(r'\[?\d{4}-\d{2}-\d{2}\]?\s*', '', old_title)
    
    if new_title != old_title:
        trial.title = new_title.strip()
        trial.refresh_date = None  # 重置 refresh_date
        trial.save()
        print(f"✅ 更新: '{old_title}' -> '{new_title}'")
        updated_count += 1
    else:
        print(f"⏭️  跳過: '{old_title}' (無需更新)")

print(f"\n=== 完成：更新了 {updated_count} 個試煉 ===")
