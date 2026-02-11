from django.db.models import Sum
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
    Team, TeamMembership, GuildPost, GuildComment, UserCourseProgress,
    DailyTrialTask
)

from .forms import (
    QuestionForm, QuestionImportForm, SkillNodeForm, CourseForm, UserLoginForm,
    UserRegistrationForm, UserProfileEditForm
)

# Import team management functions
from .views_team_management import edit_team, manage_team_members, create_team


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
    """User Registration"""
    if request.user.is_authenticated:
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Login user after registration
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, '註冊成功！')
            return redirect('engineer_rpg:dashboard')
    else:
        form = UserRegistrationForm()
    
    # Calculate XP Budgets (Logic from existing views.py)
    # Note: selected_class_code needs context if used during registration
    # For now, keeping the logic structure found in damaged views.py
    root_xp_current = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    # Placeholder for selected_class_code during registration - may need adjustment
    core_xp_current = 0 
    
    context = {
        'form': form,
        'root_xp_current': root_xp_current,
        'root_xp_limit': 4500,
        'core_xp_current': core_xp_current,
        'core_xp_limit': 118000,
    }
    return render(request, 'EngineerRPG/register.html', context)

@login_required  
def user_login(request):
    """User Login"""
    if request.user.is_authenticated:
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'歡迎回來, {user.username}!')
                return redirect('engineer_rpg:dashboard')
            else:
                messages.error(request, '帳號或密碼錯誤')
    else:
        form = UserLoginForm()
    
    context = {'form': form}
    return render(request, 'EngineerRPG/login.html', context)

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
    """冒險者大廳"""
    profile = get_or_create_user_profile(request.user)
    if not profile:
        return redirect('engineer_rpg:setup_profile')
    
    # 獲取統計資訊
    total_skills = UserSkill.objects.filter(user_profile=profile).count()
    completed_skills = UserSkill.objects.filter(user_profile=profile, status='COMPLETED').count()
    
    # 最近紀錄
    recent_trials = TrialRecord.objects.filter(user_profile=profile).order_by('-completed_at')[:5]
    
    # 每日任務 (使用 DailyTrialTask 模型)
    today = timezone.now().date()
    from .utils import generate_daily_tasks
    
    daily_tasks_query = DailyTrialTask.objects.filter(date=today).order_by('task_number')
    if not daily_tasks_query.exists():
        daily_tasks_query = generate_daily_tasks(date=today)
        
    daily_trials = [task.trial for task in daily_tasks_query]
    
    # 經驗值與進度
    exp_to_next = profile.experience_to_next_level()
    exp_progress = (profile.experience / exp_to_next * 100) if exp_to_next > 0 else 0
    progress_percent = int((completed_skills / total_skills * 100)) if total_skills > 0 else 0
    
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
    }
    return render(request, 'EngineerRPG/dashboard.html', context)

@login_required
def profile_edit(request):
    """編輯個人檔案"""
    profile = get_or_create_user_profile(request.user)
    if not profile:
        return redirect('engineer_rpg:setup_profile')

    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES)
        if form.is_valid():
            # 更新基本資訊
            user = request.user
            user.username = form.cleaned_data['username']
            if form.cleaned_data['email']:
                user.email = form.cleaned_data['email']
            
            # 密碼修改邏輯
            new_password = form.cleaned_data.get('new_password')
            old_password = form.cleaned_data.get('old_password')
            
            if new_password:
                if not user.check_password(old_password):
                    form.add_error('old_password', '原密碼輸入不正確')
                else:
                    user.set_password(new_password)
                    user.save()
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, user)
            
            user.save()
            messages.success(request, '個人檔案已更新！')
            return redirect('engineer_rpg:dashboard')
    else:
        # 初始資料
        initial_data = {
            'username': request.user.username,
            'email': request.user.email,
        }
        form = UserProfileEditForm(initial=initial_data)
        
    context = {
        'profile': profile,
        'form': form,
    }
    return render(request, 'EngineerRPG/profile_edit.html', context)


# ==================== Skill Tree Views ====================

@login_required
def skill_tree(request):
    """技能樹主頁面"""
    profile = get_or_create_user_profile(request.user)
    if not profile:
        return redirect('engineer_rpg:setup_profile')
    
    # 獲取職業與技能資料
    classes = CharacterClass.objects.all()
    selected_class_code = request.GET.get('class', profile.character_class.code)
    
    # 過戶過濾
    skills = SkillNode.objects.filter(
        Q(character_class__code=selected_class_code) | Q(node_type='ROOT')
    ).prefetch_related('parent_skills')
    
    courses = Course.objects.all()
    user_skills = UserSkill.objects.filter(user_profile=profile)
    user_skill_dict = {us.skill_node_id: us.status for us in user_skills}
    
    # XP 預算計算 (從目前的 views.py 邏輯提取)
    root_xp_current = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    core_xp_current = SkillNode.objects.filter(node_type='CORE', character_class__code=selected_class_code).aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    
    # 格式化 JSON 資料
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
        'skills': skills,
        'courses': courses,
        'classes': classes,
        'selected_class': selected_class_code,
        'skill_tree_json': json.dumps(data),
        # 預算資訊
        'root_xp_current': root_xp_current,
        'root_xp_limit': 4500,
        'core_xp_current': core_xp_current,
        'core_xp_limit': 118000,
    }
    return render(request, 'EngineerRPG/skill_tree.html', context)

@login_required
def skill_detail(request, skill_id):
    """技能詳情頁面"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    
    # 獲取或創建使用者技能記錄
    user_skill, created = UserSkill.objects.get_or_create(
        user_profile=profile,
        skill_node=skill,
        defaults={'status': 'LOCKED'}
    )
    
    # 檢查是否解鎖
    is_unlocked = check_skill_unlocked(profile, skill)
    if is_unlocked and user_skill.status == 'LOCKED':
        user_skill.status = 'AVAILABLE'
        user_skill.save()
    
    # 相關課程
    courses = skill.courses.all()
    
    # 前置技能狀態
    parent_skills = skill.parent_skills.all()
    parents_with_status = []
    for parent in parent_skills:
        parent_user_skill = UserSkill.objects.filter(user_profile=profile, skill_node=parent).first()
        parents_with_status.append({
            'skill': parent,
            'status': parent_user_skill.status if parent_user_skill else 'LOCKED'
        })
        
    context = {
        'profile': profile,
        'skill': skill,
        'user_skill': user_skill,
        'is_unlocked': is_unlocked,
        'courses': courses,
        'parents_with_status': parents_with_status,
    }
    return render(request, 'EngineerRPG/skill_detail_fixed.html', context)

@login_required
def start_learning(request, skill_id):
    """開始學習技能"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    
    user_skill, created = UserSkill.objects.get_or_create(
        user_profile=profile,
        skill_node=skill
    )
    
    if user_skill.status in ['LOCKED', 'AVAILABLE']:
        user_skill.status = 'IN_PROGRESS'
        user_skill.started_at = timezone.now()
        user_skill.save()
        messages.success(request, f'開始學習：{skill.name}')
    
    return redirect('engineer_rpg:skill_detail', skill_id=skill_id)

@login_required
def complete_skill(request, skill_id):
    """完成技能學習"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    user_skill = get_object_or_404(UserSkill, user_profile=profile, skill_node=skill)
    
    if user_skill.status == 'IN_PROGRESS':
        user_skill.status = 'COMPLETED'
        user_skill.progress = 100
        user_skill.completed_at = timezone.now()
        user_skill.save()
        
        # 獎勵經驗值
        profile.experience += skill.exp_reward
        profile.save()
        
        messages.success(request, f'恭喜完成技能：{skill.name}！獲得 {skill.exp_reward} 經驗值。')
    
    return redirect('engineer_rpg:skill_tree')


# ==================== 裝備系統 ====================

@login_required
def equipment_inventory(request):
    """個人裝備清單"""
    profile = get_or_create_user_profile(request.user)
    user_equipments = UserEquipment.objects.filter(user_profile=profile).select_related('equipment')
    context = {
        'profile': profile,
        'user_equipments': user_equipments
    }
    return render(request, 'EngineerRPG/equipment_inventory.html', context)

@login_required
def equip_item(request, user_equipment_id):
    """穿戴裝備"""
    profile = get_or_create_user_profile(request.user)
    user_equip = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    
    # 卸下同部位裝備
    UserEquipment.objects.filter(
        user_profile=profile, 
        equipment__slot=user_equip.equipment.slot,
        is_equipped=True
    ).update(is_equipped=False)
    
    user_equip.is_equipped = True
    user_equip.save()
    messages.success(request, f'已裝備：{user_equip.equipment.name}')
    return redirect('engineer_rpg:equipment_inventory')

@login_required
def unequip_item(request, user_equipment_id):
    """卸下裝備"""
    profile = get_or_create_user_profile(request.user)
    user_equip = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    user_equip.is_equipped = False
    user_equip.save()
    messages.success(request, f'已卸下：{user_equip.equipment.name}')
    return redirect('engineer_rpg:equipment_inventory')

# ==================== 道具系統 ====================

@login_required
def item_inventory(request):
    """個人道具包"""
    profile = get_or_create_user_profile(request.user)
    user_items = UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item')
    context = {
        'profile': profile,
        'user_items': user_items
    }
    return render(request, 'EngineerRPG/item_inventory.html', context)

@login_required
def use_item(request, user_item_id):
    """使用道具"""
    if request.method != 'POST':
        return redirect('engineer_rpg:item_inventory')
        
    profile = get_or_create_user_profile(request.user)
    user_item = get_object_or_404(UserItem, id=user_item_id, user_profile=profile)
    
    if user_item.quantity > 0:
        # TODO: 實作不同道具的效果邏輯
        user_item.quantity -= 1
        user_item.save()
        messages.success(request, f'使用了道具：{user_item.item.name}')
    else:
        messages.error(request, '道具數量不足')
        
    return redirect('engineer_rpg:item_inventory')

# ==================== 副本與試煉 ====================

@login_required
def dungeon_list(request):
    """副本列表"""
    profile = get_or_create_user_profile(request.user)
    
    # 獲取所有副本分類，並預抓取啟用的副本
    categories = QuestionCategory.objects.all().prefetch_related(
        Prefetch('dungeons', 
                 queryset=Trial.objects.filter(trial_type='DUNGEON', is_active=True).order_by('required_level'),
                 to_attr='active_dungeons')
    )
    
    # 獲取已通過的副本 ID
    passed_dungeon_ids = TrialRecord.objects.filter(
        user_profile=profile,
        trial__trial_type='DUNGEON',
        is_passed=True
    ).values_list('trial_id', flat=True)
    
    context = {
        'profile': profile,
        'categories': categories,
        'passed_dungeon_ids': set(passed_dungeon_ids),
    }
    return render(request, 'EngineerRPG/dungeon_list.html', context)

@login_required
def start_trial(request, trial_id):
    """開始試煉"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    
    # 權限檢查
    if profile.level < trial.required_level:
        messages.error(request, f'等級不足！需要等級 {trial.required_level}')
        return redirect('engineer_rpg:trial_detail', trial_id=trial_id)
    
    # 抽取題目
    all_questions = list(trial.questions.filter(is_active=True))
    if not all_questions:
        messages.error(request, '此試煉目前沒有可用的題目')
        return redirect('engineer_rpg:trial_detail', trial_id=trial_id)
        
    selected_questions = random.sample(all_questions, min(trial.question_count, len(all_questions)))
    
    # 初始化 Session
    request.session['trial_id'] = trial.id
    request.session['trial_questions'] = [q.id for q in selected_questions]
    request.session['trial_start_time'] = timezone.now().isoformat()
    request.session['trial_answers'] = {}
    request.session['current_question_index'] = 0
    request.session['trial_hp'] = profile.get_total_hp()
    request.session['trial_mp'] = profile.get_total_mp()
    
    # 清除每日試煉 ID (如果有的話)
    if 'daily_task_id' in request.session:
        del request.session['daily_task_id']
    
    current_question = selected_questions[0]
    
    context = {
        'profile': profile,
        'trial': trial,
        'question': current_question,
        'current_index': 0,
        'total_questions': len(selected_questions),
        'base_hp': profile.get_total_hp(),
        'initial_hp': profile.get_total_hp(),
        'initial_mp': profile.get_total_mp(),
        'heart_range': range(1, max(profile.get_total_hp(), 5) + 1),
        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)

@login_required
def submit_answer(request, trial_id):
    """提交答案 (API)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
        
    profile = get_or_create_user_profile(request.user)
    question_ids = request.session.get('trial_questions', [])
    current_index = request.session.get('current_question_index', 0)
    
    if current_index >= len(question_ids):
        return JsonResponse({'error': 'No more questions'}, status=400)
        
    question = get_object_or_404(Question, id=question_ids[current_index])
    user_answer = request.POST.get('answer', '')
    current_mp = int(request.POST.get('current_mp', 100))
    hp_damage = 0
    
    # 判斷正確性
    if question.question_type == 'MULTIPLE':
        user_answer_list = request.POST.getlist('answer')
        is_correct = set(user_answer_list) == set(question.correct_answer)
    else:
        is_correct = user_answer == str(question.correct_answer)
        
    # 紀錄 Session
    trial_answers = request.session.get('trial_answers', {})
    trial_answers[str(question.id)] = {'user_answer': user_answer, 'is_correct': is_correct}
    request.session['trial_answers'] = trial_answers
    
    # 處理血量扣減
    daily_task_id = request.session.get('daily_task_id')
    if daily_task_id:
        from .models import DailyTrialProgress, DailyTrialTask
        progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task_id=daily_task_id)
        if not is_correct:
            damage = 10
            if question.difficulty == 'C': damage = 5
            elif question.difficulty in ['A', 'S']: damage = 15
            hp_damage = damage
            progress.current_hp = max(0, progress.current_hp - damage)
        progress.current_mp = current_mp
        progress.save()
        current_hp = progress.current_hp
    else:
        current_hp = request.session.get('trial_hp', 3)
        if not is_correct:
            damage = 1
            hp_damage = damage
            current_hp = max(0, current_hp - damage)
        request.session['trial_hp'] = current_hp
        request.session['trial_mp'] = current_mp

    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'remaining_hp': current_hp,
        'hp_damage': hp_damage,
        'is_game_over': current_hp <= 0,
        'current_index': current_index,
        'total_questions': len(question_ids),
    })

@login_required
def next_question(request, trial_id):
    """下一題"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    question_ids = request.session.get('trial_questions', [])
    current_index = request.session.get('current_question_index', 0)
    
    # 更新索引
    next_index = current_index + 1
    request.session['current_question_index'] = next_index
    
    # 同步 DailyTrialProgress
    daily_task_id = request.session.get('daily_task_id')
    if daily_task_id:
        from .models import DailyTrialProgress
        progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task_id=daily_task_id)
        progress.current_question_index = next_index
        progress.save()
    
    if next_index >= len(question_ids):
        # 結算邏輯
        return redirect('engineer_rpg:submit_trial', trial_id=trial_id)
        
    next_question_obj = get_object_or_404(Question, id=question_ids[next_index])
    
    # 渲染下一題
    context = {
        'profile': profile,
        'trial': trial,
        'question': next_question_obj,
        'current_index': next_index,
        'total_questions': len(question_ids),
        'remaining_hp': request.session.get('trial_hp'),
        'remaining_mp': request.session.get('trial_mp'),
        'is_daily_task': bool(daily_task_id),
        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)

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
    """每日練功副本列表"""
    profile = get_or_create_user_profile(request.user)
    today = timezone.now().date()
    from .models import DailyTrialTask, DailyTrialProgress
    from .utils import generate_daily_tasks
    
    # 獲取或產生今日任務
    daily_tasks = DailyTrialTask.objects.filter(date=today, is_active=True).order_by('task_number')
    if not daily_tasks.exists():
        daily_tasks = generate_daily_tasks(date=today)
    
    # 建立進度列表
    task_progress_list = []
    for task in daily_tasks:
        try:
            progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task=task)
        except DailyTrialProgress.DoesNotExist:
            progress = None
            
        is_timeout = False
        if progress and not progress.is_completed and progress.started_at:
            time_limit_seconds = task.trial.time_limit_minutes * 60
            elapsed_seconds = (timezone.now() - progress.started_at).total_seconds()
            if elapsed_seconds > time_limit_seconds:
                 is_timeout = True
                 
        task_progress_list.append({
            'task': task,
            'progress': progress,
            'question_count': task.questions.count(),
            'is_timeout': is_timeout,
        })
        
    # 計算刷新時間
    now = timezone.now()
    tomorrow = timezone.make_aware(timezone.datetime.combine(today + timezone.timedelta(days=1), timezone.datetime.min.time()))
    time_until_refresh = tomorrow - now
    
    context = {
        'profile': profile,
        'task_progress_list': task_progress_list,
        'time_until_refresh': time_until_refresh,
        'today': today,
        'total_completed': sum(1 for item in task_progress_list if item['progress'] and item['progress'].is_completed),
        'total_passed': sum(1 for item in task_progress_list if item['progress'] and item['progress'].is_passed),
        'total_exp_earned': sum(item['task'].trial.exp_reward for item in task_progress_list if item['progress'] and item['progress'].is_passed),
    }
    return render(request, 'EngineerRPG/daily_trial.html', context)

@login_required
def trial_detail(request, trial_id):
    """試煉副本詳情"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    can_start = profile.level >= trial.required_level
    
    context = {
        'profile': profile,
        'trial': trial,
        'can_start': can_start,
    }
    return render(request, 'EngineerRPG/trial_detail.html', context)

@login_required
def trial_record_detail(request, record_id):
    """試煉紀錄詳情"""
    profile = get_or_create_user_profile(request.user)
    record = get_object_or_404(TrialRecord, id=record_id, user_profile=profile)
    context = {
        'profile': profile,
        'record': record
    }
    return render(request, 'EngineerRPG/trial_record_detail.html', context)


# ==================== Promotion Views ====================

@login_required
def submit_trial(request, trial_id):
    """提交試煉並結算"""
    if request.method != 'POST':
        return redirect('engineer_rpg:trial_detail', trial_id=trial_id)
        
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    
    # 獲取題組
    question_ids = request.session.get('trial_questions', [])
    questions = Question.objects.filter(id__in=question_ids)
    
    # 統計得分
    correct_count = 0
    total_count = len(questions)
    answer_details = {}
    
    for question in questions:
        user_answer = request.POST.get(f'question_{question.id}')
        correct_answer = question.correct_answer
        
        if question.question_type == 'MULTIPLE':
            user_answer_list = request.POST.getlist(f'question_{question.id}')
            is_correct = set(user_answer_list) == set(correct_answer)
        else:
            is_correct = user_answer == correct_answer
            
        if is_correct:
            correct_count += 1
            
        answer_details[str(question.id)] = {
            'user_answer': user_answer,
            'correct_answer': correct_answer,
            'is_correct': is_correct,
        }
    
    # 計算時間
    start_time_str = request.session.get('trial_start_time')
    time_spent = 0
    if start_time_str:
        start_time = timezone.datetime.fromisoformat(start_time_str)
        time_spent = (timezone.now() - start_time).total_seconds()
    
    # 計算血量
    initial_hp = request.session.get('trial_hp', 3)
    wrong_answers = total_count - correct_count
    remaining_hp = max(0, initial_hp - (wrong_answers if not request.session.get('daily_task_id') else 0))
    # 注意：每日試煉的 HP 已在 submit_answer 扣除，這裡處理的一般試煉
    
    score = int((correct_count / total_count) * 100) if total_count > 0 else 0
    is_passed = score >= 60 and (remaining_hp > 0 or request.session.get('daily_task_id'))
    
    # 經驗值與重複挑戰檢查
    is_dungeon_repeat = False
    if trial.trial_type == 'DUNGEON':
        if TrialRecord.objects.filter(user_profile=profile, trial=trial, is_passed=True).exists():
            is_dungeon_repeat = True
            
    exp_reward = trial.exp_reward
    if is_dungeon_repeat:
        exp_reward = max(1, int(exp_reward * 0.01)) # 重複挑戰僅 1% 經驗
        
    # 建立紀錄
    record = TrialRecord.objects.create(
        user_profile=profile,
        trial=trial,
        score=score,
        total_questions=total_count,
        correct_answers=correct_count,
        time_spent_seconds=int(time_spent),
        answer_details=answer_details,
        exp_gained=exp_reward if is_passed else 0,
        is_passed=is_passed,
    )
    
    # 處理每日試煉相關
    daily_task_id = request.session.get('daily_task_id')
    if daily_task_id:
        from .models import DailyTrialTask, DailyTrialProgress
        try:
            daily_task = DailyTrialTask.objects.get(id=daily_task_id)
            progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task=daily_task)
            progress.is_completed = True
            progress.is_passed = is_passed
            progress.completed_at = timezone.now()
            progress.save()
            record.daily_task = daily_task
            record.save()
        except Exception:
            pass
            
    # 結算獎勵
    if is_passed:
        profile.experience += exp_reward
        # 升級邏輯
        while profile.experience >= profile.experience_to_next_level() and profile.level < 100:
            profile.experience -= profile.experience_to_next_level()
            profile.level += 1
            messages.success(request, f'恭喜升級！目前的等級是 {profile.level}')
        
        # 掉落道具獎勵 (僅限首通或特定機率)
        if not is_dungeon_repeat and trial.item_reward:
             user_item, created = UserItem.objects.get_or_create(
                 user_profile=profile, item=trial.item_reward,
                 defaults={'quantity': 0}
             )
             user_item.quantity += 1
             user_item.save()
             messages.success(request, f'獲得首通獎勵：{trial.item_reward.name}')
             
        profile.save()
        messages.success(request, f'試煉通過！獲得 {exp_reward} 經驗值。')
    else:
        messages.error(request, '試煉失敗，請再接再厲！')
        
    # 清理 Session
    for key in ['trial_id', 'trial_questions', 'trial_start_time', 'trial_answers', 'current_question_index', 'trial_hp', 'trial_mp', 'daily_task_id']:
        if key in request.session:
            del request.session[key]
            
    return redirect('engineer_rpg:dashboard')

# ==================== 晉升系統 ====================

@login_required
def apply_promotion(request):
    """晉升申請頁面"""
    profile = get_or_create_user_profile(request.user)
    
    # 檢查是否具備晉升資格 (例如 Intern -> Assistant 需要特定課程完成)
    eligible = False
    if profile.rank == 'INTERN' and profile.level >= 10:
        eligible = True
    elif profile.rank == 'ASSISTANT' and profile.level >= 50:
        eligible = True
        
    if request.method == 'POST' and eligible:
        # 建立申請紀錄
        PromotionRequest.objects.get_or_create(
            user_profile=profile,
            current_rank=profile.rank,
            target_rank='ASSISTANT' if profile.rank == 'INTERN' else 'ENGINEER',
            status='PENDING'
        )
        messages.success(request, '晉升申請已提交，請等待管理員審核。')
        return redirect('engineer_rpg:dashboard')
        
    context = {
        'profile': profile,
        'eligible': eligible,
    }
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
    """主管/管理員儀表板"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
        
    # 獲取統計資訊
    pending_promotions = PromotionRequest.objects.filter(status='PENDING').count()
    recent_trials = TrialRecord.objects.all().order_by('-completed_at')[:10]
    
    context = {
        'profile': profile,
        'pending_promotions': pending_promotions,
        'recent_trials': recent_trials,
    }
    return render(request, 'EngineerRPG/manager_dashboard.html', context)

@login_required
def promotion_requests(request):
    """晉升申請列表"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
        
    requests = PromotionRequest.objects.filter(status='PENDING').select_related('user_profile__user')
    context = {
        'profile': profile,
        'requests': requests,
    }
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
    """冒險者公會儀表板"""
    profile = get_or_create_user_profile(request.user)
    
    # 檢查主管權限
    is_manager = profile.role in ['OFFICER', 'MANAGER', 'ADMIN']
    
    # 獲取團隊與成員資料
    teams = Team.objects.all().prefetch_related('current_members__user', 'current_members__character_class')
    free_members = UserProfile.objects.filter(current_team__isnull=True).select_related('user', 'character_class')
    
    # 布告欄摘要
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
    """布告欄文章詳情"""
    profile = get_or_create_user_profile(request.user)
    post = get_object_or_404(GuildPost, id=post_id)
    
    # 增加瀏覽次數
    post.views += 1
    post.save(update_fields=['views'])
    
    comments = post.comments.all().select_related('author__user')
    
    context = {
        'profile': profile,
        'post': post,
        'comments': comments,
    }
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
