from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import RPGTeam, UserProfile, RPGTeamMember
from .utils.permissions import has_whitelist_permission

def get_or_create_user_profile(user):
    try:
        return user.rpg_profile
    except UserProfile.DoesNotExist:
        return None

@login_required
def team_management(request):
    """隊伍管理列表"""
    if not has_whitelist_permission(request.user, 'OFFICER'):
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    teams = RPGTeam.objects.all().prefetch_related('members__user_profile__user').order_by('-created_at')
    
    return render(request, 'EngineerRPG/admin_team_list.html', {
        'profile': get_or_create_user_profile(request.user),
        'teams': teams,
    })

@login_required
def create_team(request):
    """創建隊伍"""
    if not has_whitelist_permission(request.user, 'OFFICER'):
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, '隊伍名稱不能為空')
            return redirect('engineer_rpg:create_team')
            
        team = RPGTeam.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )
        messages.success(request, f'隊伍 {name} 建立成功')
        return redirect('engineer_rpg:manage_team_members', team_id=team.id)
        
    return render(request, 'EngineerRPG/admin_team_form.html', {
        'profile': get_or_create_user_profile(request.user)
    })

@login_required
def edit_team(request, team_id):
    """編輯隊伍"""
    if not has_whitelist_permission(request.user, 'OFFICER'):
        return redirect('engineer_rpg:dashboard')
        
    team = get_object_or_404(RPGTeam, id=team_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            team.name = name
            team.description = request.POST.get('description', '').strip()
            team.save()
            messages.success(request, '隊伍資訊已更新')
            return redirect('engineer_rpg:team_management')
            
    return render(request, 'EngineerRPG/admin_team_form.html', {
        'profile': get_or_create_user_profile(request.user),
        'team': team
    })

@login_required
def manage_team_members(request, team_id):
    """管理隊伍成員"""
    if not has_whitelist_permission(request.user, 'OFFICER'):
        return redirect('engineer_rpg:dashboard')
        
    team = get_object_or_404(RPGTeam, id=team_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        try:
            if action == 'add_member':
                profile = UserProfile.objects.get(id=user_id)
                # Check if already in ANY team?
                if RPGTeamMember.objects.filter(user_profile=profile).exists():
                    messages.error(request, '該成員已在其他隊伍中')
                else:
                    RPGTeamMember.objects.create(team=team, user_profile=profile)
                    messages.success(request, f'{profile.user.username} 加入成功')
                    
            elif action == 'remove_member':
                profile = UserProfile.objects.get(id=user_id)
                RPGTeamMember.objects.filter(team=team, user_profile=profile).delete()
                # Check if leader
                if team.leader == profile.user:
                    team.leader = None
                    team.save()
                messages.success(request, '成員已移除')
                
            elif action == 'set_leader':
                user = User.objects.get(id=user_id)
                team.leader = user
                team.save()
                # Update member roles if using Role field
                RPGTeamMember.objects.filter(team=team).update(role='MEMBER')
                try:
                    m = RPGTeamMember.objects.get(team=team, user_profile__user=user)
                    m.role = 'LEADER'
                    m.save()
                except RPGTeamMember.DoesNotExist:
                    pass
                messages.success(request, f'隊長已設定為 {user.username}')
                
        except Exception as e:
            messages.error(request, f'操作失敗: {e}')
            
        return redirect('engineer_rpg:manage_team_members', team_id=team.id)

    # Members
    members = RPGTeamMember.objects.filter(team=team).select_related('user_profile__user', 'user_profile__character_class')
    
    # Available users (not in any team)
    joined_ids = RPGTeamMember.objects.values_list('user_profile_id', flat=True)
    available_members = UserProfile.objects.exclude(id__in=joined_ids).select_related('user', 'character_class')
    
    return render(request, 'EngineerRPG/admin_team_members.html', {
        'profile': get_or_create_user_profile(request.user),
        'team': team,
        'members': members,
        'available_members': available_members
    })

@login_required
def delete_team(request, team_id):
    """刪除隊伍"""
    if not has_whitelist_permission(request.user, 'OFFICER'):
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        RPGTeam.objects.filter(id=team_id).delete()
        messages.success(request, '隊伍已刪除')
        
    return redirect('engineer_rpg:team_management')

@login_required
def team_dashboard(request):
    """隊伍頁面 - 顯示使用者所屬隊伍 (Placeholder, use views.py version usually)"""
    return redirect('engineer_rpg:team_dashboard')
