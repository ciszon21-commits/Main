# EngineerRPG/utils/__init__.py
"""
每日試煉系統工具函式
"""
import random
from django.utils import timezone
from ..models import (
    DailyTrialTask, DailyTrialProgress, Trial, Question
)


def generate_daily_tasks(date=None):
    """
    生成每日試煉任務 - 每天隨機從題庫抽取題目
    
    Args:
        date: 指定日期，預設為今天
    
    Returns:
        list: 生成的 DailyTrialTask 列表
    """
    if date is None:
        date = timezone.now().date()
    
    # 檢查是否已經生成過今天的任務
    existing_tasks = DailyTrialTask.objects.filter(date=date)
    if existing_tasks.exists():
        print(f"今日任務已存在: {date}")
        return list(existing_tasks)
    
    # 1. 選擇 3 個試煉模板（作為任務框架，不看綁定的題目）
    trial_templates = Trial.objects.filter(
        is_active=True, 
        is_daily=True
    ).order_by('?')[:3]  # 隨機排序取 3 個
    
    if trial_templates.count() < 3:
        print(f"警告：試煉模板不足 3 個（目前: {trial_templates.count()}）")
        # 如果不足 3 個，就用現有的
        trial_templates = list(trial_templates)
        # 補足到 3 個（重複使用）
        while len(trial_templates) < 3 and trial_templates:
            trial_templates.append(trial_templates[0])
    else:
        trial_templates = list(trial_templates)
    
    # 2. 從題庫隨機抽取所有可用題目
    all_questions = list(Question.objects.filter(is_active=True))
    if not all_questions:
        print("錯誤：沒有可用的題目")
        return []
    
    print(f"題庫總題目數: {len(all_questions)}")
    random.shuffle(all_questions)
    
    # 3. 分配題目給 3 個任務（每個任務 10 題）
    created_tasks = []
    question_index = 0
    questions_per_task = 10
    
    for i, trial in enumerate(trial_templates[:3], 1):
        # 建立每日任務
        daily_task = DailyTrialTask.objects.create(
            date=date,
            task_number=i,
            trial=trial,
            is_active=True
        )
        
        # 分配題目（每個任務 10 題，如果題目不足則分配剩餘的）
        remaining_questions = len(all_questions) - question_index
        question_count = min(questions_per_task, remaining_questions)
        
        if question_count > 0:
            task_questions = all_questions[question_index:question_index + question_count]
            daily_task.questions.set(task_questions)
            question_index += question_count
            print(f"已建立任務 {i}: {trial.title} ({question_count} 題)")
        else:
            print(f"警告：任務 {i} 沒有可用題目（題目已用完）")
        
        created_tasks.append(daily_task)
    
    print(f"成功生成 {len(created_tasks)} 個每日任務，共使用 {question_index} 題")
    return created_tasks


def cleanup_old_tasks(keep_days=1):
    """
    清理舊的每日任務
    
    Args:
        keep_days: 保留最近幾天的任務，預設為 1（只保留今天）
    
    Returns:
        int: 刪除的任務數量
    """
    cutoff_date = timezone.now().date() - timezone.timedelta(days=keep_days - 1)
    
    # 刪除指定日期之前的任務
    old_tasks = DailyTrialTask.objects.filter(date__lt=cutoff_date)
    count = old_tasks.count()
    
    if count > 0:
        old_tasks.delete()
        print(f"已刪除 {count} 個舊任務（{cutoff_date} 之前）")
    else:
        print("沒有需要清理的舊任務")
    
    return count


def refresh_daily_tasks():
    """
    刷新每日任務（清理舊任務並生成新任務）
    
    這個函式應該在每天凌晨 12 點執行
    """
    print(f"=== 開始刷新每日任務 {timezone.now()} ===")
    
    # 清理舊任務
    cleanup_old_tasks(keep_days=1)
    
    # 生成新任務
    today = timezone.now().date()
    tasks = generate_daily_tasks(date=today)
    
    print(f"=== 每日任務刷新完成 ===")
    return tasks


def get_or_create_daily_progress(user_profile, daily_task):
    """
    獲取或建立使用者的每日試煉進度
    
    Args:
        user_profile: UserProfile 實例
        daily_task: DailyTrialTask 實例
    
    Returns:
        DailyTrialProgress: 進度實例
    """
    progress, created = DailyTrialProgress.objects.get_or_create(
        user_profile=user_profile,
        daily_task=daily_task,
        defaults={
            'initial_hp': user_profile.get_total_hp(),
            'initial_mp': user_profile.get_total_mp(),
            'current_hp': user_profile.get_total_hp(),
            'current_mp': user_profile.get_total_mp(),
        }
    )
    
    if created:
        print(f"建立新的每日試煉進度: {user_profile.user.username} - {daily_task}")
    
    return progress
