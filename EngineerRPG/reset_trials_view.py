@login_required
def reset_daily_trials(request):
    """重置所有每日試煉進度 (用於測試)"""
    profile = get_or_create_user_profile(request.user)
    
    # 刪除所有未完成的每日試煉進度
    from .models import DailyTrialProgress
    deleted_count = DailyTrialProgress.objects.filter(
        user_profile=profile,
        is_completed=False
    ).delete()[0]
    
    messages.success(request, f'已重置 {deleted_count} 個未完成的每日試煉進度!')
    return redirect(request.META.get('HTTP_REFERER', 'engineer_rpg:daily_trial_list'))
