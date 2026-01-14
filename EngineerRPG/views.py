from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count, Avg, Prefetch
from django.core.paginator import Paginator
import random
import json

from .models import (
    CharacterClass, UserProfile, SkillNode, Course, UserSkill,
    Equipment, UserEquipment, Item, UserItem, Question, QuestionCategory, Trial, TrialRecord,
    PromotionRequest, EnhancementScroll, Achievement, UserAchievement,
    Team, TeamMembership, GuildPost, GuildComment
)


# ==================== Helper Functions ====================

def get_or_create_user_profile(user):
    """Get or create user profile"""
    try:
        return user.rpg_profile
    except UserProfile.DoesNotExist:
        # Create default profile
        default_class = CharacterClass.objects.first()
        if not default_class:
            raise Exception("No character class available")
        
        profile = UserProfile.objects.create(
            user=user,
            employee_id=f"EMP{user.id:04d}",
            character_class=default_class
        )
        return profile


# ==================== Authentication Views ====================

@login_required
def user_register(request):
    """User registration"""
    return render(request, 'EngineerRPG/register.html')

@login_required  
def user_login(request):
    """User login"""
    return render(request, 'EngineerRPG/login.html')

@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    return redirect('engineer_rpg:index')


# ==================== Main Views ====================

def index(request):
    """Index page"""
    return render(request, 'EngineerRPG/index.html')

@login_required
def dashboard(request):
    """User dashboard"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/dashboard.html', context)

@login_required
def profile_edit(request):
    """Edit user profile"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/profile_edit.html', context)


# ==================== Skill Tree Views ====================

@login_required
def skill_tree(request):
    """Skill tree page"""
    profile = get_or_create_user_profile(request.user)
    
    # Fetch data
    skills = SkillNode.objects.filter(
        Q(character_class=profile.character_class) | Q(character_class__isnull=True)
    ).prefetch_related('parent_skills')
    
    user_skills = UserSkill.objects.filter(user_profile=profile)
    user_skill_dict = {us.skill_node_id: us.status for us in user_skills}
    
    data = []
    for skill in skills:
        data.append({
            'skill': {
                'id': skill.id,
                'name': skill.name,
                'node_type': skill.node_type,
                'position_x': skill.position_x,
                'position_y': skill.position_y,
                'parent_skills': [p.id for p in skill.parent_skills.all()]
            },
            'status': user_skill_dict.get(skill.id, 'LOCKED')
        })
        
    context = {
        'profile': profile,
        'skill_tree_json': json.dumps(data)
    }
    return render(request, 'EngineerRPG/skill_tree.html', context)

@login_required
def skill_detail(request, skill_id):
    """Skill detail page"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    context = {'profile': profile, 'skill': skill}
    return render(request, 'EngineerRPG/skill_detail.html', context)

@login_required
def start_learning(request, skill_id):
    """Start learning a skill"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:skill_tree')

@login_required
def complete_skill(request, skill_id):
    """Complete a skill"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:skill_tree')


# ==================== Equipment Views ====================

@login_required
def equipment_inventory(request):
    """Equipment inventory"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/equipment_inventory.html', context)

@login_required
def equip_item(request, user_equipment_id):
    """Equip an item"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:equipment_inventory')

@login_required
def unequip_item(request, user_equipment_id):
    """Unequip an item"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:equipment_inventory')

@login_required
def enhance_equipment(request, user_equipment_id):
    """Enhance equipment"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:equipment_inventory')


# ==================== Item Views ====================

@login_required
def item_inventory(request):
    """Item inventory"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/item_inventory.html', context)

@login_required
def use_item(request, user_item_id):
    """Use an item"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:item_inventory')

@login_required
def api_consume_item(request, user_item_id):
    """API: Consume an item"""
    return JsonResponse({'success': True})


# ==================== Trial Views ====================

@login_required
def training_hub(request):
    """Training hub"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/training_hub.html', context)

@login_required
def daily_trial_list(request):
    """Daily trial list"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/daily_trial_list.html', context)

@login_required
def start_daily_trial(request, task_id):
    """Start daily trial"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:daily_trial_list')

@login_required
def dungeon_list(request):
    """Dungeon list"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/dungeon_list.html', context)

@login_required
def trial_detail(request, trial_id):
    """Trial detail"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    context = {'profile': profile, 'trial': trial}
    return render(request, 'EngineerRPG/trial_detail.html', context)

@login_required
def start_trial(request, trial_id):
    """Start trial"""
    profile = get_or_create_user_profile(request.user)
    return redirect('engineer_rpg:trial_detail', trial_id=trial_id)

@login_required
def submit_answer(request, trial_id):
    """Submit answer"""
    return JsonResponse({'success': True})

@login_required
def next_question(request, trial_id):
    """Next question"""
    return JsonResponse({'success': True})

@login_required
def submit_trial(request, trial_id):
    """Submit trial"""
    return redirect('engineer_rpg:dashboard')

@login_required
def trial_record_detail(request, record_id):
    """Trial record detail"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/trial_record_detail.html', context)


# ==================== Promotion Views ====================

@login_required
def apply_promotion(request):
    """Apply for promotion"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/apply_promotion.html', context)

@login_required
def promotion_trial(request, request_id):
    """Promotion trial"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/promotion_trial.html', context)


# ==================== Leaderboard ====================

@login_required
def leaderboard(request):
    """Leaderboard"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/leaderboard.html', context)


# ==================== Manager Views ====================

@login_required
def manager_dashboard(request):
    """Manager dashboard"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/manager_dashboard.html', context)

@login_required
def promotion_requests(request):
    """Promotion requests"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/promotion_requests.html', context)

@login_required
def review_request(request, request_id):
    """Review promotion request"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/review_request.html', context)

@login_required
def approve_request(request, request_id):
    """Approve promotion request"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    return redirect('engineer_rpg:promotion_requests')

@login_required
def reject_request(request, request_id):
    """Reject promotion request"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    return redirect('engineer_rpg:promotion_requests')

@login_required
def manage_skill_tree(request):
    """Manage skill tree"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/manage_skill_tree.html', context)

@login_required
def manage_questions(request):
    """Manage questions"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/question_management.html', context)


# ==================== Admin Views ====================

@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    
    context = {
        'profile': profile,
        'total_users': UserProfile.objects.count(),
        'total_questions': Question.objects.count(),
        'total_skills': SkillNode.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'total_items': Item.objects.count(),
    }
    return render(request, 'EngineerRPG/admin_dashboard.html', context)

@login_required
def user_management(request):
    """User management"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/user_management.html', context)

@login_required
def create_user(request):
    """Create user"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/create_user.html', context)

@login_required
def edit_user(request, user_id):
    """Edit user"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/edit_user.html', context)

@login_required
def question_management(request):
    """Question management"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/question_management.html', context)

@login_required
def create_question(request):
    """Create question"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/create_question.html', context)

@login_required
def edit_question(request, question_id):
    """Edit question"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/edit_question.html', context)

@login_required
def category_management(request):
    """Category management"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/category_management.html', context)

@login_required
def dungeon_management(request):
    """Dungeon management"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/dungeon_management.html', context)

@login_required
def create_dungeon(request):
    """Create dungeon"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/create_dungeon.html', context)

@login_required
def edit_dungeon(request, dungeon_id):
    """Edit dungeon"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/edit_dungeon.html', context)

@login_required
def import_questions_view(request):
    """Import questions"""
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    context = {'profile': profile}
    return render(request, 'EngineerRPG/import_questions.html', context)

@login_required
def download_template(request, format):
    """Download template"""
    return HttpResponse("Template")

@login_required
def skill_tree_editor(request):
    """Skill tree editor"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    
    classes = CharacterClass.objects.all()
    selected_class = request.GET.get('class', 'CIVIL')
    
    skills = SkillNode.objects.filter(Q(character_class__code=selected_class) | Q(character_class__isnull=True))
    courses = Course.objects.all()
    
    context = {
        'profile': profile,
        'classes': classes,
        'selected_class': selected_class,
        'skills': skills,
        'courses': courses,
    }
    return render(request, 'EngineerRPG/skill_tree_editor.html', context)


# ==================== Guild Views ====================

@login_required
def guild_dashboard(request):
    """Guild dashboard"""
    profile = get_or_create_user_profile(request.user)
    
    # Check permissions
    is_manager = profile.role in ['OFFICER', 'MANAGER', 'ADMIN']
    
    # Fetch data
    teams = Team.objects.all().prefetch_related('current_members__user', 'current_members__character_class')
    free_members = UserProfile.objects.filter(current_team__isnull=True).select_related('user', 'character_class')
    announcements = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-created_at')[:5]
    hot_posts = GuildPost.objects.exclude(category='ANNOUNCEMENT').order_by('-views', '-created_at')[:5]
    
    context = {
        'profile': profile,
        'teams': teams,
        'free_members': free_members,
        'announcements': announcements,
        'hot_posts': hot_posts,
        'is_manager': is_manager,
    }
    
    return render(request, 'EngineerRPG/guild_dashboard.html', context)

@login_required
def guild_exchange_list(request):
    """Guild exchange list"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/guild_exchange_list.html', context)

@login_required
def guild_post_create(request):
    """Create guild post"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/guild_post_create.html', context)

@login_required
def guild_post_detail(request, post_id):
    """Guild post detail"""
    profile = get_or_create_user_profile(request.user)
    post = get_object_or_404(GuildPost, id=post_id)
    context = {'profile': profile, 'post': post}
    return render(request, 'EngineerRPG/guild_post_detail.html', context)


# ==================== API Views ====================

@login_required
def api_user_stats(request):
    """API: User stats"""
    return JsonResponse({'success': True})

@login_required
def api_skill_tree_data(request):
    """API: Skill tree data"""
    profile = get_or_create_user_profile(request.user)
    
    skills = SkillNode.objects.filter(
        Q(character_class=profile.character_class) | Q(character_class__isnull=True)
    ).prefetch_related('parent_skills')
    
    user_skills = UserSkill.objects.filter(user_profile=profile)
    user_skill_dict = {us.skill_node_id: us.status for us in user_skills}
    
    data = []
    for skill in skills:
        data.append({
            'id': skill.id,
            'name': skill.name,
            'type': skill.node_type,
            'position': {'x': skill.position_x, 'y': skill.position_y},
            'parents': [p.id for p in skill.parent_skills.all()],
            'status': user_skill_dict.get(skill.id, 'LOCKED'),
        })
    
    return JsonResponse({'skills': data})

@login_required
def api_skill_editor_data(request):
    """API: Get skill editor data"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    class_code = request.GET.get('class', 'CIVIL')
    
    skills = SkillNode.objects.filter(
        Q(node_type='ROOT') | Q(character_class__code=class_code)
    ).prefetch_related('parent_skills', 'courses')
    
    nodes = []
    for skill in skills:
        nodes.append({
            'id': skill.id,
            'name': skill.name,
            'description': skill.description,
            'type': skill.node_type,
            'x': skill.position_x,
            'y': skill.position_y,
            'parents': [p.id for p in skill.parent_skills.all()],
            'courses': [c.id for c in skill.courses.all()],
            'exp_reward': skill.exp_reward,
        })
        
    all_courses = Course.objects.all().values('id', 'title', 'content_type')
    
    return JsonResponse({
        'nodes': nodes,
        'courses': list(all_courses)
    })

@login_required
@csrf_exempt
def api_save_skill_layout(request):
    """API: Save skill layout (manual drag & drop)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])
        
        for item in updates:
            SkillNode.objects.filter(id=item['id']).update(
                position_x=item['x'],
                position_y=item['y']
            )
            
        return JsonResponse({'status': 'success', 'count': len(updates)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@csrf_exempt
def api_save_skill_node(request):
    """API: Save skill node"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        data = json.loads(request.body)
        node_id = data.get('id')
        
        if node_id:
            node = get_object_or_404(SkillNode, id=node_id)
        else:
            node = SkillNode()
            node.position_x = 100
            node.position_y = 100
            
        node.name = data.get('name')
        node.description = data.get('description', '')
        node.node_type = data.get('type')
        node.exp_reward = data.get('exp_reward', 50)
        
        if node.node_type == 'ROOT':
            node.character_class = None
        else:
            class_code = data.get('class_code')
            if class_code:
                try:
                    node.character_class = CharacterClass.objects.get(code=class_code)
                except CharacterClass.DoesNotExist:
                    node.character_class = None
            
        node.save()
        
        # Parents
        parent_ids = data.get('parents', [])
        if parent_ids is not None:
             parent_skills = SkillNode.objects.filter(id__in=parent_ids)
             node.parent_skills.set(parent_skills)

        # Courses
        course_ids = data.get('courses', [])
        if course_ids is not None:
             courses = Course.objects.filter(id__in=course_ids)
             node.courses.set(courses)

        return JsonResponse({'success': True, 'id': node.id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@csrf_exempt
def api_delete_skill_node(request):
    """API: Delete skill node"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        data = json.loads(request.body)
        node_id = data.get('id')
        SkillNode.objects.filter(id=node_id).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def api_manage_skill_course(request):
    """API: Manage skill course - Deprecated/Placeholder"""
    return JsonResponse({'success': True})

@login_required
@csrf_exempt
def api_auto_layout_skill_tree(request):
    """API: Auto layout skill tree"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({'error': 'Permission denied'}, status=403)
        
    try:
        data = json.loads(request.body)
        class_code = data.get('class_code')
        
        skills = SkillNode.objects.filter(
            Q(node_type='ROOT') | Q(character_class__code=class_code)
        ).prefetch_related('parent_skills')
        
        levels = {} 
        skill_map = {s.id: s for s in skills}
        
        for s in skills:
            levels[s.id] = 0
            
        changed = True
        iterations = 0
        while changed and iterations < 100:
            changed = False
            iterations += 1
            for s in skills:
                current_level = levels[s.id]
                max_parent_level = -1
                for p in s.parent_skills.all():
                    if p.id in levels:
                        max_parent_level = max(max_parent_level, levels[p.id])
                
                if max_parent_level >= current_level:
                    levels[s.id] = max_parent_level + 1
                    changed = True
                    
        level_groups = {}
        for s_id, lvl in levels.items():
            if lvl not in level_groups:
                level_groups[lvl] = []
            level_groups[lvl].append(skill_map[s_id])
            
        count = 0
        for lvl in sorted(level_groups.keys()):
            nodes = level_groups[lvl]
            nodes.sort(key=lambda x: x.name)
            
            x_pos = lvl * 250 + 50
            start_y = 50
            
            for i, node in enumerate(nodes):
                y_pos = start_y + i * 150
                node.position_x = x_pos
                node.position_y = y_pos
                node.save()
                count += 1
                
        return JsonResponse({'success': True, 'count': count})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==================== Team Views (Old) ====================

@login_required
def team_detail(request, team_id):
    """Team detail"""
    profile = get_or_create_user_profile(request.user)
    team = get_object_or_404(Team, id=team_id)
    context = {'profile': profile, 'team': team}
    return render(request, 'EngineerRPG/team_detail.html', context)

@login_required
def team_member_detail(request, team_id, member_id):
    """Team member detail"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/team_member_detail.html', context)

@login_required
def team_manage_members(request, team_id):
    """Manage team members"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/team_manage_members.html', context)

@login_required
def team_add_member(request, team_id):
    """Add team member"""
    return redirect('engineer_rpg:team_detail', team_id=team_id)

@login_required
def team_remove_member(request, team_id, member_id):
    """Remove team member"""
    return redirect('engineer_rpg:team_detail', team_id=team_id)

@login_required
def member_profile_detail(request, member_id):
    """Member profile detail"""
    profile = get_or_create_user_profile(request.user)
    context = {'profile': profile}
    return render(request, 'EngineerRPG/member_profile_detail.html', context)


# ==================== Team Management Views (New) ====================

@login_required
def team_management(request):
    """Team management list"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    
    teams = Team.objects.all().prefetch_related('current_members').order_by('-created_at')
    
    context = {
        'profile': profile,
        'teams': teams,
    }
    return render(request, 'EngineerRPG/admin_team_list.html', context)


@login_required
def create_team(request):
    """Create team"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Team name cannot be empty')
            return redirect('engineer_rpg:create_team')
        
        from TeamKnowledgeHub.models import KnowledgeTeam
        team = KnowledgeTeam.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )
        
        messages.success(request, f'Team "{name}" created successfully')
        return redirect('engineer_rpg:edit_team', team_id=team.id)
    
    context = {
        'profile': profile,
    }
    return render(request, 'EngineerRPG/admin_team_form.html', context)


@login_required
def edit_team(request, team_id):
    """Edit team"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:dashboard')
    
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        leader_id = request.POST.get('leader')
        
        if not name:
            messages.error(request, 'Team name cannot be empty')
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
            messages.success(request, 'Team information updated')
            return redirect('engineer_rpg:manage_team_members', team_id=team.id)
    
    members = team.current_members.all().select_related('user')
    
    context = {
        'profile': profile,
        'team': team,
        'members': members,
    }
    return render(request, 'EngineerRPG/admin_team_form.html', context)

@login_required
def delete_team(request, team_id):
    """Disband team"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
        return redirect('engineer_rpg:team_management')
    
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        name = team.name
        team.delete()
        messages.success(request, f'Team "{name}" disbanded successfully')
    
    return redirect('engineer_rpg:team_management')


@login_required
def manage_team_members(request, team_id):
    """Manage team members"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, 'Permission denied')
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
                messages.success(request, f'Added {user_profile.user.username} to team')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User not found')
        
        elif action == 'remove_member':
            user_id = request.POST.get('user_id')
            try:
                user_profile = UserProfile.objects.get(id=user_id)
                if user_profile.current_team == team:
                    user_profile.current_team = None
                    user_profile.save()
                    messages.success(request, f'Removed {user_profile.user.username} from team')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User not found')
        
        elif action == 'set_leader':
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                team.leader = user
                team.save()
                messages.success(request, f'Set {user.username} as team leader')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
        
        return redirect('engineer_rpg:manage_team_members', team_id=team.id)
    
    members = team.current_members.all().select_related('user', 'character_class')
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
    """Team dashboard - show user's team"""
    profile = get_or_create_user_profile(request.user)
    
    if not profile.current_team:
        context = {
            'profile': profile,
            'has_team': False,
        }
    else:
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
