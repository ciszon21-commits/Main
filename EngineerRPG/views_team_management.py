# 在 views.py 末尾新增以下內容

# ==================== Team Management Views ====================

@login_required
def team_management(request):
    """隊伍管理列表"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    teams = Team.objects.all().prefetch_related('current_members').order_by('-created_at')
    
    context = {
        'profile': profile,
        'teams': teams,
    }
    return render(request, 'EngineerRPG/admin_team_list.html', context)


@login_required
def create_team(request):
    """創建隊伍"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, '隊伍名稱不能為空！')
            return redirect('engineer_rpg:create_team')
        
        # 使用 TeamKnowledgeHub.KnowledgeTeam 創建
        from TeamKnowledgeHub.models import KnowledgeTeam
        team = KnowledgeTeam.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )
        
        messages.success(request, f'隊伍「{name}」創建成功！')
        return redirect('engineer_rpg:edit_team', team_id=team.id)
    
    context = {
        'profile': profile,
    }
    return render(request, 'EngineerRPG/admin_team_form.html', context)


@login_required
def edit_team(request, team_id):
    """編輯隊伍"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        leader_id = request.POST.get('leader')
        
        if not name:
            messages.error(request, '隊伍名稱不能為空！')
        else:
            team.name = name
            team.description = description
            
            if leader_id:
                try:
                    leader_user = User.objects.get(id=leader_id)
                    team.leader = leader_user
                except User.DoesNotExist:
                    pass
            else:
                team.leader = None
            
            team.save()
            messages.success(request, '隊伍資訊已更新！')
            return redirect('engineer_rpg:manage_team_members', team_id=team.id)
    
    # 獲取隊伍成員作為可選隊長
    members = team.current_members.all().select_related('user')
    
    context = {
        'profile': profile,
        'team': team,
        'members': members,
    }
    return render(request, 'EngineerRPG/admin_team_form.html', context)


@login_required
def manage_team_members(request, team_id):
    """管理隊伍成員"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_member':
            user_id = request.POST.get('user_id')
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                user_profile.current_team = team
                user_profile.save()
                messages.success(request, f'已將 {user_profile.user.username} 加入隊伍！')
            except UserProfile.DoesNotExist:
                messages.error(request, '使用者不存在！')
        
        elif action == 'remove_member':
            user_id = request.POST.get('user_id')
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                if user_profile.current_team == team:
                    user_profile.current_team = None
                    user_profile.save()
                    messages.success(request, f'已將 {user_profile.user.username} 移出隊伍！')
            except UserProfile.DoesNotExist:
                messages.error(request, '使用者不存在！')
        
        elif action == 'set_leader':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                team.leader = user
                team.save()
                messages.success(request, f'已將 {user.username} 設為隊長！')
            except User.DoesNotExist:
                messages.error(request, '使用者不存在！')
        
        return redirect('engineer_rpg:manage_team_members', team_id=team.id)
    
    # 獲取隊伍成員
    members = team.current_members.all().select_related('user', 'character_class')
    
    # 獲取所有未分配隊伍的冒險者
    available_members = UserProfile.objects.filter(current_team__isnull=True).select_related('user', 'character_class')
    
    context = {
        'profile': profile,
        'team': team,
        'members': members,
        'available_members': available_members,
    }
    return render(request, 'EngineerRPG/admin_team_members.html', context)


@login_required
def team_dashboard(request):
    """隊伍頁面 - 顯示使用者所屬隊伍"""
    profile = get_or_create_user_profile(request.user)
    
    if not profile.current_team:
        # 沒有隊伍
        context = {
            'profile': profile,
            'has_team': False,
        }
    else:
        # 有隊伍，顯示隊伍資訊
        team = profile.current_team
        members = team.current_members.all().select_related('user', 'character_class').order_by('-level')
        
        context = {
            'profile': profile,
            'has_team': True,
            'team': team,
            'members': members,
            'is_leader': team.is_leader(request.user),
        }
    
    return render(request, 'EngineerRPG/team_dashboard.html', context)
