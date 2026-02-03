#!/usr/bin/env python
"""
測試每日任務生成
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Trial, Question, DailyTrialTask
from EngineerRPG.utils import generate_daily_tasks
from django.utils import timezone

print("=== 每日任務生成測試 ===\n")

# 1. 檢查可用試煉
print("1. 檢查可用試煉...")
trials = Trial.objects.filter(is_active=True, is_daily=True)
print(f"   可用的每日試煉數量: {trials.count()}")
for trial in trials:
    print(f"   - {trial.title} (題目數: {trial.question_count})")

if trials.count() < 3:
    print("\n❌ 錯誤：可用的每日試煉不足 3 個！")
    print("   請在 Admin 後台建立至少 3 個標記為 'is_daily=True' 的試煉。")
    exit(1)

# 2. 檢查可用題目
print("\n2. 檢查可用題目...")
questions = Question.objects.filter(is_active=True)
print(f"   可用題目數量: {questions.count()}")

if questions.count() == 0:
    print("\n❌ 錯誤：沒有可用的題目！")
    print("   請在 Admin 後台建立題目。")
    exit(1)

# 3. 檢查今日任務
print("\n3. 檢查今日任務...")
today = timezone.now().date()
existing_tasks = DailyTrialTask.objects.filter(date=today)
print(f"   今日已存在任務數: {existing_tasks.count()}")

if existing_tasks.exists():
    print("   今日任務已生成：")
    for task in existing_tasks:
        print(f"   - 任務 {task.task_number}: {task.trial.title} ({task.questions.count()} 題)")
else:
    # 4. 嘗試生成任務
    print("\n4. 嘗試生成今日任務...")
    try:
        tasks = generate_daily_tasks(date=today)
        print(f"\n✅ 成功生成 {len(tasks)} 個任務！")
        for task in tasks:
            print(f"   - 任務 {task.task_number}: {task.trial.title} ({task.questions.count()} 題)")
    except Exception as e:
        print(f"\n❌ 生成失敗：{e}")
        import traceback
        traceback.print_exc()

print("\n=== 測試完成 ===")
