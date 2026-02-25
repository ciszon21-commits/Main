@login_required
def guild_announcement_create(request):
    """發布公告（僅限管理員）"""
    
    profile = get_or_create_user_profile(request.user)
    
    # 權限檢查：僅限公會幹部或公會長
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '只有公會幹部或公會長才能發布公告')
        return redirect('engineer_rpg:guild_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            post = GuildPost.objects.create(
                author=profile,
                title=title,
                content=content,
                category='ANNOUNCEMENT'  # 自動設為公告
            )
            messages.success(request, '公告發布成功')
            return redirect('engineer_rpg:guild_dashboard')
        else:
            messages.error(request, '請填寫完整資訊')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/guild_announcement_create.html', context)
