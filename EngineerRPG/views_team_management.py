# Team Management Views
# 隊伍管理相關的 view 函數

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Team, UserProfile, TeamMembership

# Helper function
def get_or_create_user_profile(user):
    """Get or create user profile"""
    try:
        return user.rpg_profile
    except UserProfile.DoesNotExist:
        return None

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
        
        # 創建隊伍
        team = Team.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )
        
        messages.success(request, f'隊伍「{name}」創建成功！')
        return redirect('engineer_rpg:manage_team_members', team_id=team.id)
    
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
                
                # 同時創建 TeamMembership 記錄和更新 UserProfile
                from django.utils import timezone
                
                # 創建 TeamMembership 記錄
                membership, created = TeamMembership.objects.get_or_create(
                    team=team,
                    user=user_profile.user,
                    defaults={
                        'role': 'MEMBER',
                        'joined_at': timezone.now()
                    }
                )
                
                # 更新 UserProfile
                user_profile.current_team = team
                user_profile.save()
                
                messages.success(request, f'已將 {user_profile.user.username} 加入隊伍！')
            except UserProfile.DoesNotExist:
                messages.error(request, '使用者不存在！')
            except Exception as e:
                messages.error(request, f'加入隊伍失敗：{str(e)}')
        
        elif action == 'remove_member':
            user_id = request.POST.get('user_id')
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                if user_profile.current_team == team:
                    # 同時刪除 TeamMembership 記錄和更新 UserProfile
                    TeamMembership.objects.filter(
                        team=team,
                        user=user_profile.user
                    ).delete()
                    
                    user_profile.current_team = None
                    user_profile.save()
                    
                    messages.success(request, f'已將 {user_profile.user.username} 移出隊伍！')
            except UserProfile.DoesNotExist:
                messages.error(request, '使用者不存在！')
            except Exception as e:
                messages.error(request, f'移出隊伍失敗：{str(e)}')
        
        elif action == 'set_leader':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                
                # 更新隊長
                team.leader = user
                team.save()
                
                # 更新 TeamMembership 中的角色
                TeamMembership.objects.filter(team=team, role='LEADER').update(role='MEMBER')
                TeamMembership.objects.filter(team=team, user=user).update(role='LEADER')
                
                messages.success(request, f'已將 {user.username} 設為隊長！')
            except User.DoesNotExist:
                messages.error(request, '使用者不存在！')
            except Exception as e:
                messages.error(request, f'設定隊長失敗：{str(e)}')
        
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
    """隊伍頁面 - 顯示隊伍資訊，公會幹部/會長可透過 team_id 查看其他隊伍"""
    profile = get_or_create_user_profile(request.user)
    
    is_guild_manager = profile.role in ['MANAGER', 'OFFICER']
    target_team = None
    team_id_param = request.GET.get('team_id')
    
    if team_id_param and is_guild_manager:
        target_team = get_object_or_404(Team, id=team_id_param)
    else:
        target_team = profile.current_team
    
    if not target_team:
        # 沒有隊伍
        context = {
            'profile': profile,
            'has_team': False,
        }
    else:
        # 有隊伍，顯示隊伍資訊
        team = target_team
        members = team.current_members.all().select_related('user', 'character_class').order_by('-level')
        
        # 判斷是否為隊長或副隊長
        is_dept_manager = False
        try:
            membership = TeamMembership.objects.get(team=team, user=request.user)
            if membership.role in ['LEADER', 'VICE_LEADER']:
                is_dept_manager = True
        except TeamMembership.DoesNotExist:
            pass
            
        can_review_promotions = is_dept_manager
        can_view_promotions = is_dept_manager or is_guild_manager
            
        # 取得該隊伍成員的待審核晉升申請
        pending_promotions = []
        if can_view_promotions:
            from .models import PromotionRequest
            # 撈取 current_team 為此團隊，且 status 為 PENDING 的申請
            pending_promotions = PromotionRequest.objects.filter(
                applicant__current_team=team,
                status='PENDING'
            ).select_related('applicant__user', 'applicant__character_class')
        
        context = {
            'profile': profile,
            'has_team': True,
            'team': team,
            'members': members,
            'is_leader': team.is_leader(request.user),
            'is_dept_manager': is_dept_manager,
            'can_review_promotions': can_review_promotions,
            'can_view_promotions': can_view_promotions,
            'pending_promotions': pending_promotions,
        }
    
    return render(request, 'EngineerRPG/team_dashboard.html', context)
