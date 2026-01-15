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

def user_register(request):
    """使用者註冊"""
    from .forms import UserRegistrationForm
    from django.contrib import messages
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '註冊成功！請登入開始你的冒險之旅。')
            return redirect('engineer_rpg:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'EngineerRPG/register.html', {'form': form})

def user_login(request):
    """使用者登入"""
    from .forms import UserLoginForm
    from django.contrib.auth import authenticate, login
    from django.contrib import messages
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'歡迎回來，{user.username}！')
                return redirect('engineer_rpg:dashboard')
            else:
                messages.error(request, '帳號或密碼錯誤，請重試。')
    else:
        form = UserLoginForm()
    
    return render(request, 'EngineerRPG/login.html', {'form': form})

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
    """\u4f7f\u7528\u8005\u5100\u8868\u677f"""
    profile = get_or_create_user_profile(request.user)
    if not profile:
        return redirect('engineer_rpg:setup_profile')
    
    # \u7372\u53d6\u4f7f\u7528\u8005\u6280\u80fd\u8cc7\u8a0a
    total_skills = UserSkill.objects.filter(user_profile=profile).count()
    completed_skills = UserSkill.objects.filter(user_profile=profile, status='COMPLETED').count()
    
    # \u6700\u8fd1\u8a66\u7149\u8a18\u9304
    recent_trials = TrialRecord.objects.filter(user_profile=profile).order_by('-completed_at')[:5]
    
    # \u6bcf\u65e5\u526f\u672c
    today = timezone.now().date()
    daily_trials = Trial.objects.filter(is_daily=True, is_active=True, refresh_date=today)
    
    # \u7d93\u9a57\u503c\u8a08\u7b97
    exp_to_next = profile.experience_to_next_level()
    exp_progress = (profile.experience / exp_to_next * 100) if exp_to_next > 0 else 0
    
    # \u6280\u80fd\u9032\u5ea6\u767e\u5206\u6bd4
    progress_percent = int((completed_skills / total_skills * 100)) if total_skills > 0 else 0
    
    # \u7372\u53d6\u968a\u4f0d\u8cc7\u8a0a
    try:
        team_membership = TeamMembership.objects.select_related('team').get(user=request.user)
    except TeamMembership.DoesNotExist:
        team_membership = None
    
    context = {
        'profile': profile,
        'total_skills': total_skills,
        'completed_skills': completed_skills,
        'recent_trials': recent_trials,
        'daily_trials': daily_trials,
        'exp_progress': exp_progress,
        'exp_to_next': exp_to_next,
        'total_hp': profile.get_total_hp(),
        'total_mp': profile.get_total_mp(),
        'progress_percent': progress_percent,
        'team_membership': team_membership,
    }
    
    return render(request, 'EngineerRPG/dashboard.html', context)

@login_required
def profile_edit(request):
    """\u7de8\u8f2f\u500b\u4eba\u8cc7\u6599"""
    from .forms import UserProfileEditForm
    from django.contrib import messages
    from django.contrib.auth import update_session_auth_hash
    
    profile = get_or_create_user_profile(request.user)
    if not profile:
        return redirect('engineer_rpg:setup_profile')

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES)
        if form.is_valid():
            # \u66f4\u65b0\u4f7f\u7528\u8005\u8cc7\u6599
            user = request.user
            user.username = form.cleaned_data['username']
            if form.cleaned_data['email']:
                user.email = form.cleaned_data['email']
            
            # \u8655\u7406\u5bc6\u78bc\u8b8a\u66f4
            new_password = form.cleaned_data.get('new_password')
            old_password = form.cleaned_data.get('old_password')
            
            if new_password:
                # \u9a57\u8b49\u820a\u5bc6\u78bc
                if not user.check_password(old_password):
                    form.add_error('old_password', '\u820a\u5bc6\u78bc\u4e0d\u6b63\u78ba')
                else:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)  # \u4fdd\u6301\u767b\u5165\u72c0\u614b
            else:
                user.save()

            if not form.errors:
                # \u66f4\u65b0\u500b\u4eba\u6a94\u6848
                profile.employee_id = form.cleaned_data['employee_id']
                
                # \u8655\u7406\u982d\u50cf
                avatar_index = form.cleaned_data.get('avatar_index')
                if avatar_index and int(avatar_index) > 0:
                    profile.avatar_index = int(avatar_index)
                    profile.avatar_image = None  # \u6e05\u9664\u81ea\u8a02\u982d\u50cf
                    
                # \u8655\u7406\u4e0a\u50b3\u7684\u81ea\u8a02\u982d\u50cf
                if form.cleaned_data.get('avatar_image'):
                    profile.avatar_image = form.cleaned_data['avatar_image']
                    profile.avatar_index = 0  # \u91cd\u8a2d\u7d22\u5f15
                
                profile.save()

                messages.success(request, '\u500b\u4eba\u8cc7\u6599\u5df2\u66f4\u65b0\uff01')
                return redirect('engineer_rpg:dashboard')
    else:
        initial_data = {
            'username': request.user.username,
            'email': request.user.email,
            'employee_id': profile.employee_id,
            'avatar_index': profile.avatar_index,
        }
        form = UserProfileEditForm(initial=initial_data)

    # \u982d\u50cf\u7a31\u865f\u5c0d\u61c9\u8868
    avatar_data = [
        (1, '\u73fe\u5834\u76e3\u5de5'),
        (2, '\u5973\u6027\u5de5\u7a0b\u5e2b'),
        (3, '\u5b89\u5168\u7763\u5c0e'),
        (4, '\u6a5f\u96fb\u6cd5\u5e2b'),
        (5, '\u9435\u5320\u5927\u5e2b'),
        (6, '\u77ee\u4eba\u5de5\u982d'),
        (7, '\u77f3\u5de5\u5b97\u5e2b'),
        (8, '\u77ee\u4eba\u6280\u5e2b'),
        (9, '\u74b0\u5883\u5b88\u8b77\u8005'),
        (10, '\u7cbe\u9748\u5efa\u7bc9\u5e2b'),
        (11, '\u7da0\u80fd\u5c08\u5bb6'),
        (12, '\u7cbe\u9748\u6e2c\u91cf\u5e2b'),
        (13, '\u7378\u4eba\u5de5\u982d'),
        (14, '\u91cd\u88dd\u6230\u58eb'),
        (15, '\u62c6\u9664\u5c08\u5bb6'),
        (16, '\u7378\u4eba\u9818\u73ed'),
        (17, '\u60e1\u9b54\u76e3\u5de5'),
        (18, '\u5730\u7344\u5de5\u7a0b\u5e2b'),
        (19, '\u70c8\u7130\u7763\u5c0e'),
        (20, '\u9b54\u738b\u7e3d\u76e3'),
    ]

    context = {
        'form': form,
        'profile': profile,
        'avatar_data': avatar_data,
    }
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
    """公會交流區文章列表"""
    from django.core.paginator import Paginator
    from django.utils import timezone
    
    profile = get_or_create_user_profile(request.user)
    
    # 獲取分類參數
    current_category = request.GET.get('category', 'ALL')
    
    # 獲取文章查詢集
    posts = GuildPost.objects.select_related('author__user').prefetch_related('comments')
    
    # 分類篩選
    if current_category != 'ALL':
        posts = posts.filter(category=current_category)
    
    # 分離置頂和一般文章
    pinned_posts = posts.filter(is_pinned=True)
    regular_posts = posts.filter(is_pinned=False)
    
    # 分頁
    paginator = Paginator(regular_posts, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': profile,
        'categories': GuildPost.CATEGORY_CHOICES,
        'current_category': current_category,
        'pinned_posts': pinned_posts,
        'page_obj': page_obj,
        'now': timezone.now(),
    }
    return render(request, 'EngineerRPG/guild_exchange_list.html', context)

@login_required
def guild_post_create(request):
    """創建公會文章"""
    from django.contrib import messages
    
    profile = get_or_create_user_profile(request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category = request.POST.get('category', 'GENERAL')
        
        # 驗證
        if not title or not content:
            messages.error(request, '標題和內容不能為空')
            return redirect('engineer_rpg:guild_post_create')
        
        # 公告類別僅限管理員
        if category == 'ANNOUNCEMENT' and profile.role not in ['MANAGER', 'ADMIN']:
            messages.error(request, '只有管理員可以發布公告')
            return redirect('engineer_rpg:guild_post_create')
        
        # 創建文章
        post = GuildPost.objects.create(
            author=profile,
            title=title,
            content=content,
            category=category
        )
        
        messages.success(request, '文章發布成功！')
        return redirect('engineer_rpg:guild_post_detail', post_id=post.id)
    
    # GET 請求 - 根據使用者角色過濾分類選項
    if profile.role in ['MANAGER', 'ADMIN']:
        categories = GuildPost.CATEGORY_CHOICES
    else:
        categories = [c for c in GuildPost.CATEGORY_CHOICES if c[0] != 'ANNOUNCEMENT']
    
    context = {
        'profile': profile,
        'categories': categories,
    }
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
