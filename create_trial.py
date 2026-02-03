#!/usr/bin/env python
"""
建立額外的每日試煉
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CoDevStudio.settings')
django.setup()

from EngineerRPG.models import Trial, Question
from django.utils import timezone
import random

print("=== 建立每日試煉 ===\n")

# 獲取所有題目
all_questions = list(Question.objects.filter(is_active=True))
print(f"可用題目數: {len(all_questions)}")

if len(all_questions) < 10:
    print("警告：題目數量不足，將使用所有可用題目")
    selected_questions = all_questions
else:
    selected_questions = random.sample(all_questions, 10)

# 建立第三個每日試煉
trial = Trial.objects.create(
    title="每日工程實務挑戰",
    description="測試工程實務知識的每日挑戰，涵蓋監造、施工管理等多個領域。",
    trial_type='DAILY',
    question_count=10,
    time_limit_minutes=20,
    required_level=1,
    exp_reward=150,
    is_daily=True,
    is_active=True,
    refresh_date=timezone.now().date()
)

trial.questions.set(selected_questions)

print(f"✅ 成功建立試煉：{trial.title}")
print(f"   題目數：{trial.questions.count()}")
print(f"   經驗獎勵：{trial.exp_reward}")

# 驗證現在有足夠的試煉
daily_trials = Trial.objects.filter(is_active=True, is_daily=True)
print(f"\n現在共有 {daily_trials.count()} 個每日試煉")

print("\n=== 完成 ===")
