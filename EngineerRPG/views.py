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
    RPGTeam, RPGTeamMember, GuildPost, GuildComment, DailyTrialTask, DailyTrialProgress
)


from .forms import (
    QuestionForm, QuestionImportForm, SkillNodeForm, CourseForm, UserLoginForm,
    UserRegistrationForm, UserProfileEditForm
)

# ==================== 輔助函數 ====================

def get_or_create_user_profile(user):
    """獲取或自動建立使用者檔案"""
    try:
        if hasattr(user, 'rpg_profile'):
            return user.rpg_profile
        return UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        # 如果使用者沒有檔案，自動建立一個
        default_class = CharacterClass.objects.first()
        if not default_class:
            default_class = CharacterClass.objects.create(
                code='CIVIL',
                name='土木戰士',
                description='專精土木工程的職業'
            )
        
        profile = UserProfile.objects.create(
            user=user,
            employee_id=f'EMP{user.id:05d}',
            character_class=default_class,
            role='ADVENTURER'
        )
        return profile


def check_skill_unlocked(user_profile, skill_node):
    """檢查技能是否已解鎖"""
    # 檢查等級需求
    if user_profile.level < skill_node.min_level:
        return False

    # 檢查前置技能是否皆完成
    parent_skills = skill_node.parent_skills.all()
    if parent_skills.exists():
        completed_parents = UserSkill.objects.filter(
            user_profile=user_profile,
            skill_node__in=parent_skills,
            status='COMPLETED'
        ).count()
        return completed_parents == parent_skills.count()
    return True



from .utils.permissions import has_whitelist_permission, get_whitelist_role, PRIVILEGE_RANK


# # ==================== 使用者註冊與登入 ====================

# def user_register(request):
#     """使用者註冊"""
#     if request.user.is_authenticated:
#         return redirect('engineer_rpg:dashboard')
    
#     if request.method == 'POST':
#         form = UserRegistrationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             user.backend = 'django.contrib.auth.backends.ModelBackend'
#             login(request, user)
#             messages.success(request, f'歡迎加入監造冒險者公會！您已成為 {user.rpg_profile.character_class.name}')
#             return redirect('engineer_rpg:dashboard')
#     else:
#         form = UserRegistrationForm()
    
#     context = {
#         'form': form,
#     }
    
#     return render(request, 'EngineerRPG/register.html', context)


def user_login(request):
    """使用者登入"""
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
                messages.success(request, f'歡迎回來，{user.username}！')
                return redirect('engineer_rpg:dashboard')
            else:
                messages.error(request, '使用者名稱或密碼錯誤')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'EngineerRPG/login.html', context)


def user_logout(request):
    """使用者登出"""
    logout(request)
    messages.success(request, '您已成功登出')
    return redirect('engineer_rpg:index')


# ==================== 首頁與儀表板 ====================

def index(request):
    """公會入口頁"""
    return render(request, 'EngineerRPG/index.html')


@login_required
def dashboard(request):
    """冒險者儀表板"""
    profile = get_or_create_user_profile(request.user)
    if not profile:
        return redirect('engineer_rpg:setup_profile')
    
    # 獲取統計數據
    total_skills = UserSkill.objects.filter(user_profile=profile).count()
    completed_skills = UserSkill.objects.filter(user_profile=profile, status='COMPLETED').count()
    
    recent_trials = TrialRecord.objects.filter(user_profile=profile).order_by('-completed_at')[:5]
    
    today = timezone.now().date()
    daily_trials = Trial.objects.filter(is_daily=True, is_active=True, refresh_date=today)
    
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
    
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.username = form.cleaned_data['username']
            if form.cleaned_data['email']:
                user.email = form.cleaned_data['email']
            
            new_password = form.cleaned_data.get('new_password')
            old_password = form.cleaned_data.get('old_password')
            
            if new_password:
                if not user.check_password(old_password):
                    form.add_error('old_password', '舊密碼不正確')
                else:
                    user.set_password(new_password)
                    user.save()
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, user)
            else:
                user.save()

            if not form.errors:
                profile.employee_id = form.cleaned_data['employee_id']
                
                avatar_index = form.cleaned_data.get('avatar_index')
                if avatar_index and int(avatar_index) > 0:
                    profile.avatar_index = int(avatar_index)
                    profile.avatar_image = None 
                    
                if form.cleaned_data.get('avatar_image'):
                    profile.avatar_image = form.cleaned_data['avatar_image']
                    profile.avatar_index = 0
                
                profile.save()
                messages.success(request, '個人資料更新成功！')
                return redirect('engineer_rpg:dashboard')
    else:
        initial_data = {
            'username': request.user.username,
            'email': request.user.email,
            'employee_id': profile.employee_id,
            'avatar_index': profile.avatar_index,
        }
        form = UserProfileEditForm(initial=initial_data)

    context = {
        'form': form,
        'profile': profile,
        'default_avatars': range(1, 21)
    }
    return render(request, 'EngineerRPG/profile_edit.html', context)


@login_required
def select_character_class(request):
    """選擇職業"""
    profile = get_or_create_user_profile(request.user)
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        if class_id:
            try:
                character_class = CharacterClass.objects.get(id=class_id)
                profile.character_class = character_class
                profile.save()
                messages.success(request, f'已轉職為 {character_class.name}')
                return redirect('engineer_rpg:dashboard')
            except CharacterClass.DoesNotExist:
                messages.error(request, '無效的職業選擇')
    
    classes = CharacterClass.objects.all()
    return render(request, 'EngineerRPG/select_class.html', {'profile': profile, 'classes': classes})


# ==================== 技能樹系統 ====================

@login_required
def skill_tree(request):
    """技能樹主體"""
    profile = get_or_create_user_profile(request.user)
    
    skills = SkillNode.objects.filter(
        Q(character_class=profile.character_class) | Q(character_class__isnull=True)
    ).prefetch_related('parent_skills')
    
    user_skills = UserSkill.objects.filter(user_profile=profile).select_related('skill_node')
    user_skill_dict = {us.skill_node_id: us for us in user_skills}
    
    skill_tree_data = []
    for skill in skills:
        user_skill = user_skill_dict.get(skill.id)
        is_unlocked = check_skill_unlocked(profile, skill)
        
        skill_tree_data.append({
            'skill': skill,
            'user_skill': user_skill,
            'is_unlocked': is_unlocked,
            'status': user_skill.status if user_skill else ('AVAILABLE' if is_unlocked else 'LOCKED'),
        })
    
    context = {
        'profile': profile,
        'skill_tree_data': skill_tree_data,
        'skill_tree_json': json.dumps([{
            'id': item['skill'].id,
            'name': item['skill'].name,
            'node_type': item['skill'].node_type,
            'x': item['skill'].position_x,
            'y': item['skill'].position_y,
            'status': item['status'],
            'parents': [p.id for p in item['skill'].parent_skills.all()]
        } for item in skill_tree_data])
    }
    
    return render(request, 'EngineerRPG/skill_tree.html', context)


@login_required
def skill_detail(request, skill_id):
    """技能詳細資訊"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    
    user_skill, created = UserSkill.objects.get_or_create(
        user_profile=profile,
        skill_node=skill,
        defaults={'status': 'LOCKED'}
    )
    
    is_unlocked = check_skill_unlocked(profile, skill)
    if is_unlocked and user_skill.status == 'LOCKED':
        user_skill.status = 'AVAILABLE'
        user_skill.save()
    
    context = {
        'profile': profile,
        'skill': skill,
        'user_skill': user_skill,
        'is_unlocked': is_unlocked,
        'courses': skill.courses.all(),
        'parents': skill.parent_skills.all(),
    }
    return render(request, 'EngineerRPG/skill_detail.html', context)


@login_required
def start_learning(request, skill_id):
    """開始修練某個技能"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    
    user_skill, _ = UserSkill.objects.get_or_create(user_profile=profile, skill_node=skill)
    
    if user_skill.status in ['LOCKED', 'AVAILABLE']:
        user_skill.status = 'IN_PROGRESS'
        user_skill.started_at = timezone.now()
        user_skill.save()
        messages.success(request, f'已開始挑戰：{skill.name}')
    
    return redirect('engineer_rpg:skill_detail', skill_id=skill_id)


@login_required
def complete_skill(request, skill_id):
    """完成技能（結算經驗值與升級）"""
    profile = get_or_create_user_profile(request.user)
    skill = get_object_or_404(SkillNode, id=skill_id)
    
    user_skill = get_object_or_404(UserSkill, user_profile=profile, skill_node=skill)
    
    if user_skill.status == 'IN_PROGRESS':
        user_skill.status = 'COMPLETED'
        user_skill.progress = 100
        user_skill.completed_at = timezone.now()
        user_skill.save()
        
        profile.experience += skill.exp_reward
        while profile.experience >= profile.experience_to_next_level():
            profile.experience -= profile.experience_to_next_level()
            profile.level += 1
            messages.success(request, f'恭喜升級！當前等級：Lv.{profile.level}')
        
        profile.save()
        messages.success(request, f'成功獲得 {skill.name} 的技能認證！')
    
    return redirect('engineer_rpg:skill_tree')


# ==================== 裝備系統 ====================

@login_required
def equipment_inventory(request):
    """裝備庫頁面"""
    profile = get_or_create_user_profile(request.user)
    
    user_equipments = UserEquipment.objects.filter(user_profile=profile).select_related('equipment')
    
    context = {
        'profile': profile,
        'helmets': user_equipments.filter(equipment__equipment_type='HELMET'),
        'armors': user_equipments.filter(equipment__equipment_type='ARMOR'),
        'boots': user_equipments.filter(equipment__equipment_type='BOOTS'),
        'tools': user_equipments.filter(equipment__equipment_type='TOOL'),
        'equipped': {
            'helmet': profile.equipped_helmet,
            'armor': profile.equipped_armor,
            'boots': profile.equipped_boots,
            'tools': [getattr(profile, f'equipped_tool_{i}') for i in range(1, 6)]
        }
    }
    return render(request, 'EngineerRPG/equipment_inventory.html', context)


@login_required
def equip_item(request, user_equipment_id):
    """裝備道具"""
    profile = get_or_create_user_profile(request.user)
    ue = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    
    etype = ue.equipment.equipment_type
    if etype == 'HELMET':
        profile.equipped_helmet = ue
    elif etype == 'ARMOR':
        profile.equipped_armor = ue
    elif etype == 'BOOTS':
        profile.equipped_boots = ue
    elif etype == 'TOOL':
        slot = request.POST.get('slot', '1')
        setattr(profile, f'equipped_tool_{slot}', ue)
        
    ue.is_equipped = True
    ue.save()
    profile.update_stats()
    profile.save()
    
    messages.success(request, f'已裝備 {ue.equipment.name}')
    return redirect('engineer_rpg:equipment_inventory')


@login_required
def unequip_item(request, user_equipment_id):
    """卸下裝備"""
    profile = get_or_create_user_profile(request.user)
    ue = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    
    if profile.equipped_helmet == ue: profile.equipped_helmet = None
    elif profile.equipped_armor == ue: profile.equipped_armor = None
    elif profile.equipped_boots == ue: profile.equipped_boots = None
    else:
        for i in range(1, 6):
            if getattr(profile, f'equipped_tool_{i}') == ue:
                setattr(profile, f'equipped_tool_{i}', None)
                break
                
    ue.is_equipped = False
    ue.save()
    profile.update_stats()
    profile.save()
    
    messages.success(request, f'已卸下 {ue.equipment.name}')
    return redirect('engineer_rpg:equipment_inventory')


@login_required
def enhance_equipment(request, user_equipment_id):
    """強化裝備"""
    profile = get_or_create_user_profile(request.user)
    ue = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    
    if ue.enhancement_level >= ue.equipment.max_enhancement:
        messages.error(request, '已達最高強化等級')
    elif profile.enhancement_tickets < 1:
        messages.error(request, '強化券不足')
    else:
        profile.enhancement_tickets -= 1
        ue.enhancement_level += 1
        ue.save()
        profile.save()
        messages.success(request, f'強化成功！當前等級：+{ue.enhancement_level}')
        
    return redirect('engineer_rpg:equipment_inventory')


# ==================== 道具系統 ====================

@login_required
def item_inventory(request):
    """道具背包"""
    profile = get_or_create_user_profile(request.user)
    user_items = UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item')
    return render(request, 'EngineerRPG/item_inventory.html', {'user_items': user_items, 'profile': profile})


@login_required
def use_item(request, user_item_id):
    """在地圖外使用道具（如補血或 Buff，目前主要在試煉中使用）"""
    messages.info(request, '此道具需在試煉或副本戰鬥中方可發揮效果')
    return redirect('engineer_rpg:item_inventory')


@csrf_exempt
@login_required
def api_consume_item(request, user_item_id):
    """AJAX: 消耗道具"""
    if request.method != 'POST': return JsonResponse({'success': False}, status=405)
    
    profile = get_or_create_user_profile(request.user)
    ui = get_object_or_404(UserItem, id=user_item_id, user_profile=profile)
    
    if ui.quantity > 0:
        ui.quantity -= 1
        ui.save()
        return JsonResponse({'success': True, 'remaining': ui.quantity})
    return JsonResponse({'success': False, 'message': '數量不足'}, status=400)


# ==================== 試煉與副本系統 (關鍵邏輯) ====================

@login_required
def training_hub(request):
    """修練中心導向頁"""
    return render(request, 'EngineerRPG/training_hub.html')


@login_required
def daily_trial_list(request):
    """?????????"""
    profile = get_or_create_user_profile(request.user)
    today = timezone.now().date()
    
    from .utils import generate_daily_tasks
    tasks = DailyTrialTask.objects.filter(date=today, is_active=True).order_by('task_number')
    if not tasks.exists():
        tasks = generate_daily_tasks(date=today)
    
    task_progress_list = []
    total_passed = 0
    total_exp_earned = 0
    for t in tasks:
        progress = DailyTrialProgress.objects.filter(user_profile=profile, daily_task=t).first()
        if progress and progress.is_completed and progress.is_passed:
            total_passed += 1
            total_exp_earned += t.trial.exp_reward
        task_progress_list.append({
            'task': t,
            'progress': progress,
            'question_count': t.questions.count(),
        })
    
    now = timezone.now()
    tomorrow = timezone.datetime.combine(
        today + timezone.timedelta(days=1),
        timezone.datetime.min.time()
    )
    tomorrow = timezone.make_aware(tomorrow)
    time_until_refresh = tomorrow - now
    
    context = {
        'profile': profile,
        'task_progress_list': task_progress_list,
        'time_until_refresh': time_until_refresh,
        'total_passed': total_passed,
        'total_exp_earned': total_exp_earned,
        'today': today
    }
    return render(request, 'EngineerRPG/daily_trial.html', context)


@login_required
def start_daily_trial(request, task_id):
    """啟動每日試煉進度"""
    profile = get_or_create_user_profile(request.user)
    task = get_object_or_404(DailyTrialTask, id=task_id)
    
    from .utils import get_or_create_daily_progress
    progress = get_or_create_daily_progress(profile, task)
    
    if progress.is_completed:
        messages.warning(request, '任務已完成')
        return redirect('engineer_rpg:daily_trial_list')
        
    if progress.current_hp <= 0:
        messages.error(request, '生命值不足，無法重啟挑戰')
        return redirect('engineer_rpg:daily_trial_list')
        
    questions = list(task.questions.all())
    
    # 設置會話狀態
    request.session['daily_task_id'] = task.id
    request.session['trial_questions'] = [q.id for q in questions]
    request.session['current_question_index'] = 0
    request.session['trial_start_time'] = timezone.now().isoformat()
    
    if not progress.started_at:
        progress.started_at = timezone.now()
        progress.save()
        
    context = {
        'profile': profile,
        'trial': task.trial,
        'question': questions[0],
        'total': len(questions),
        'current': 0,
        'hp': progress.current_hp,
        'mp': progress.current_mp,
        'is_daily': True,
        'items': UserItem.objects.filter(user_profile=profile, quantity__gt=0)
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)

@login_required
def dungeon_list(request):
    """地下城副本列表"""
    profile = get_or_create_user_profile(request.user)
    categories = QuestionCategory.objects.all().prefetch_related(
        Prefetch('dungeons', 
                 queryset=Trial.objects.filter(trial_type='DUNGEON', is_active=True).order_by('required_level'),
                 to_attr='active_dungeons')
    )
    return render(request, 'EngineerRPG/dungeon_list.html', {'profile': profile, 'categories': categories})


@login_required
def trial_detail(request, trial_id):
    """副本詳情頁"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    can_start = profile.level >= trial.required_level
    return render(request, 'EngineerRPG/trial_detail.html', {'profile': profile, 'trial': trial, 'can_start': can_start})


@login_required
def start_trial(request, trial_id):
    """啟動地下城/試煉進度"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    
    all_questions = list(trial.questions.filter(is_active=True))
    if len(all_questions) < trial.question_count:
        messages.error(request, '題目配置不足，請聯繫管理員')
        return redirect('engineer_rpg:trial_detail', trial_id=trial.id)
        
    selected = random.sample(all_questions, trial.question_count)
    
    # Session 初始化
    request.session['trial_id'] = trial.id
    request.session['trial_questions'] = [q.id for q in selected]
    request.session['current_question_index'] = 0
    request.session['trial_answers'] = {}
    request.session['trial_hp'] = profile.get_total_hp()
    request.session['trial_start_time'] = timezone.now().isoformat()
    
    context = {
        'profile': profile,
        'trial': trial,
        'question': selected[0],
        'total': len(selected),
        'current': 0,
        'hp': profile.get_total_hp(),
        'mp': profile.get_total_mp(),
        'items': UserItem.objects.filter(user_profile=profile, quantity__gt=0)
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)


@login_required
def submit_answer(request, trial_id):
    """API: 提交單題答案並回傳結果"""
    if request.method != 'POST': return JsonResponse({'error': 'Method forbidden'}, status=405)
    
    profile = get_or_create_user_profile(request.user)
    q_ids = request.session.get('trial_questions', [])
    c_idx = request.session.get('current_question_index', 0)
    
    if c_idx >= len(q_ids): return JsonResponse({'error': 'No more questions'}, status=400)
    
    question = get_object_or_404(Question, id=q_ids[c_idx])
    user_ans = request.POST.get('answer', '')
    
    # 判斷正確性
    is_correct = False
    if question.question_type == 'MULTIPLE':
        ans_list = request.POST.getlist('answer')
        is_correct = set(ans_list) == set(question.correct_answer.split(',') if isinstance(question.correct_answer, str) else [])
    else:
        is_correct = user_ans == str(question.correct_answer)
        
    # 紀錄答案進 Session
    trial_answers = request.session.get('trial_answers', {})
    trial_answers[str(question.id)] = {'ans': user_ans, 'correct': is_correct}
    request.session['trial_answers'] = trial_answers
    
    # 血量更新
    daily_tid = request.session.get('daily_task_id')
    curr_hp = 0
    
    if daily_tid:
        progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task_id=daily_tid)
        if not is_correct: progress.current_hp = max(0, progress.current_hp - 1)
        if not progress.answers: progress.answers = {}
        progress.answers[str(question.id)] = {'user_answer': user_ans, 'is_correct': is_correct}
        progress.save()
        curr_hp = progress.current_hp
    else:
        curr_hp = request.session.get('trial_hp', profile.get_total_hp())
        if not is_correct:
            curr_hp = max(0, curr_hp - 1)
            request.session['trial_hp'] = curr_hp
            
    return JsonResponse({
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'remaining_hp': curr_hp,
        'is_game_over': curr_hp <= 0,
        'current_index': c_idx,
        'total': len(q_ids)
    })


@login_required
def next_question(request, trial_id):
    """跳轉至下一題或進行結算"""
    idx = request.session.get('current_question_index', 0) + 1
    q_ids = request.session.get('trial_questions', [])
    
    if idx >= len(q_ids):
        return redirect('engineer_rpg:submit_trial', trial_id=trial_id)
        
    request.session['current_question_index'] = idx
    # 此處重定向至顯示題目用的視圖
    is_daily = 'daily_task_id' in request.session
    if is_daily:
        return redirect('engineer_rpg:start_daily_trial', task_id=request.session['daily_task_id'])
    else:
        return redirect('engineer_rpg:start_trial', trial_id=trial_id)


@login_required
def submit_trial(request, trial_id):
    """試煉/副本結算邏輯"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    
    answers = request.session.get('trial_answers', {})
    correct_count = sum(1 for a in answers.values() if a.get('correct'))
    score = int(correct_count / len(answers) * 100) if answers else 0
    passed = score >= 60  # 通過門檻 60 分
    
    # 建立正式記錄
    record = TrialRecord.objects.create(
        user_profile=profile,
        trial=trial,
        score=score,
        is_passed=passed,
        correct_answers=correct_count,
        total_questions=len(answers),
        completed_at=timezone.now()
    )
    
    # 發放獎勵
    exp_gain = trial.exp_reward if passed else int(trial.exp_reward * 0.2)
    profile.experience += exp_gain
    while profile.experience >= profile.experience_to_next_level():
        profile.experience -= profile.experience_to_next_level()
        profile.level += 1
        messages.success(request, f'升級了！Lv.{profile.level}')
    profile.save()
    
    # 清除 Session
    for key in ['daily_task_id', 'trial_id', 'trial_questions', 'current_question_index', 'trial_answers', 'trial_hp', 'trial_start_time']:
        if key in request.session: del request.session[key]
        
    context = {
        'profile': profile,
        'record': record,
        'exp_gain': exp_gain
    }
    return render(request, 'EngineerRPG/trial_result.html', context)


@login_required
def trial_record_detail(request, record_id):
    """試煉記錄詳情頁"""
    profile = get_or_create_user_profile(request.user)
    record = get_object_or_404(TrialRecord, id=record_id, user_profile=profile)
    
    context = {
        'profile': profile,
        'record': record,
    }
    
    return render(request, 'EngineerRPG/trial_record.html', context)


# ==================== 隊伍管理 ====================

@login_required
def team_dashboard(request):
    """RPG 團隊中心"""
    profile = get_or_create_user_profile(request.user)
    led_teams = RPGTeam.objects.filter(leader=request.user, is_active=True)
    current_membership = RPGTeamMember.objects.filter(
        user_profile=profile
    ).select_related('team').first()
    
    return render(request, 'EngineerRPG/team_dashboard.html', {
        'profile': profile,
        'led_teams': led_teams,
        'current_team': current_membership.team if current_membership else None
    })


@login_required
def team_detail(request, team_id):
    """RPG 團隊詳情（戰力與成員分析）"""
    profile = get_or_create_user_profile(request.user)
    team = get_object_or_404(RPGTeam, id=team_id)
    memberships = RPGTeamMember.objects.filter(team=team).select_related('user_profile__user', 'user_profile__character_class')
    
    # 獲取各成員技能進度
    member_data = []
    for m in memberships:
        p = m.user_profile
        completed = UserSkill.objects.filter(user_profile=p, status='COMPLETED').count()
        total = SkillNode.objects.filter(character_class=p.character_class).count()
        member_data.append({
            'profile': p,
            'completion': round(completed / total * 100, 1) if total > 0 else 0
        })
        
    return render(request, 'EngineerRPG/team_detail.html', {
        'profile': profile,
        'team': team,
        'member_data': member_data,
        'is_leader': team.leader == request.user
    })


@login_required
def team_manage_members(request, team_id):
    """管理RPG團隊成員"""
    team = get_object_or_404(RPGTeam, id=team_id)
    if team.leader != request.user and request.user.rpg_profile.role not in ['MANAGER', 'ADMIN']:
        return redirect('engineer_rpg:team_detail', team_id=team_id)
        
    current = RPGTeamMember.objects.filter(team=team).select_related('user_profile__user')
    # 獲取還沒加入任何團隊的使用者
    joined_profiles = RPGTeamMember.objects.values_list('user_profile_id', flat=True)
    available = UserProfile.objects.exclude(id__in=joined_profiles).exclude(user=team.leader)
    
    return render(request, 'EngineerRPG/team_manage_members.html', {'team': team, 'current': current, 'available': available})


@login_required
def team_add_member(request, team_id):
    """新增RPG團隊成員"""
    if request.method != 'POST': 
        return redirect('engineer_rpg:team_manage_members', team_id=team_id)
    
    team = get_object_or_404(RPGTeam, id=team_id)
    uid = request.POST.get('user_id')
    target = get_object_or_404(UserProfile, id=uid)
    
    # 檢查是否已在其他團隊
    existing = RPGTeamMember.objects.filter(user_profile=target).exists()
    if not existing and not team.is_full():
        RPGTeamMember.objects.create(team=team, user_profile=target, role='MEMBER')
        messages.success(request, f'已加入 {target.user.username}')
    elif team.is_full():
        messages.error(request, '團隊已滿')
    else:
        messages.error(request, f'{target.user.username} 已在其他團隊')
    
    return redirect('engineer_rpg:team_manage_members', team_id=team_id)


@login_required
def team_remove_member(request, team_id, member_id):
    """移除RPG團隊成員"""
    if request.method != 'POST': 
        return redirect('engineer_rpg:team_manage_members', team_id=team_id)
    
    team = get_object_or_404(RPGTeam, id=team_id)
    membership = get_object_or_404(RPGTeamMember, team=team, user_profile_id=member_id)
    username = membership.user_profile.user.username
    
    # 刪除成員關係
    membership.delete()
    
    messages.success(request, f'已移除 {username}')
    return redirect('engineer_rpg:team_manage_members', team_id=team_id)



# ==================== 公會與討論區 ====================

@login_required
def guild_dashboard(request):
    """公會概覽頁面"""
    profile = get_or_create_user_profile(request.user)
    ann = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-created_at')[:5]
    posts = GuildPost.objects.exclude(category='ANNOUNCEMENT').order_by('-created_at')[:10]

    # 熱門話題：依留言數 + 瀏覽數排序
    hot_posts = (GuildPost.objects.exclude(category='ANNOUNCEMENT')
                 .annotate(comment_count=Count('comments'))
                 .order_by('-comment_count', '-views')[:5])

    # 成員名錄：有隊伍的團隊 & 自由冒險者
    teams = RPGTeam.objects.filter(is_active=True).select_related('leader')
    members_in_teams = RPGTeamMember.objects.values_list('user_profile_id', flat=True)
    free_members = UserProfile.objects.exclude(id__in=members_in_teams).select_related('user', 'character_class')

    is_manager = profile.role in ('OFFICER', 'MANAGER', 'ADMIN')

    return render(request, 'EngineerRPG/guild_dashboard.html', {
        'profile': profile,
        'announcements': ann,
        'recent_posts': posts,
        'hot_posts': hot_posts,
        'teams': teams,
        'free_members': free_members,
        'is_manager': is_manager,
    })


@login_required
def guild_exchange_list(request):
    """冒險者交流板"""
    profile = get_or_create_user_profile(request.user)
    cat = request.GET.get('category')
    posts = GuildPost.objects.exclude(category='ANNOUNCEMENT').select_related('author__user')
    if cat and cat != 'ALL':
        posts = posts.filter(category=cat)
    posts = posts.order_by('-created_at')

    pinned_posts = GuildPost.objects.filter(is_pinned=True).exclude(category='ANNOUNCEMENT').select_related('author__user')
    page = Paginator(posts, 20).get_page(request.GET.get('page'))

    return render(request, 'EngineerRPG/guild_exchange_list.html', {
        'profile': profile,
        'page_obj': page,
        'categories': GuildPost.CATEGORY_CHOICES,
        'pinned_posts': pinned_posts,
        'current_category': cat or 'ALL',
        'now': timezone.now(),
    })


@login_required
def guild_post_create(request):
    """發起新討論"""
    profile = get_or_create_user_profile(request.user)
    if request.method == 'POST':
        post = GuildPost.objects.create(
            author=profile,
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            category=request.POST.get('category', 'GENERAL')
        )
        return redirect('engineer_rpg:guild_post_detail', post_id=post.id)
    return render(request, 'EngineerRPG/guild_post_create.html', {'profile': profile, 'categories': GuildPost.CATEGORY_CHOICES})


@login_required
def guild_post_detail(request, post_id):
    """貼文詳情與交流"""
    profile = get_or_create_user_profile(request.user)
    post = get_object_or_404(GuildPost, id=post_id)
    post.views += 1
    post.save()
    
    if request.method == 'POST':
        GuildComment.objects.create(post=post, author=profile, content=request.POST.get('content'))
        return redirect('engineer_rpg:guild_post_detail', post_id=post.id)
        
    return render(request, 'EngineerRPG/guild_post_detail.html', {'profile': profile, 'post': post, 'comments': post.comments.all()})


@login_required
def guild_announcement_create(request):
    """發布系統級公告"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ('OFFICER', 'MANAGER', 'ADMIN'):
        return redirect('engineer_rpg:guild_dashboard')
    if request.method == 'POST':
        GuildPost.objects.create(
            author=profile,
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            category='ANNOUNCEMENT',
        )
        messages.success(request, '公告已發布')
        return redirect('engineer_rpg:guild_announcement_list')
    return render(request, 'EngineerRPG/guild_announcement_create.html', {'profile': profile})


# ==================== 主管與管理員後台 ====================

@login_required
def manager_dashboard(request):
    """主管控制台"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
        
    pending_requests = PromotionRequest.objects.filter(status='PENDING').order_by('created_at')
    return render(request, 'EngineerRPG/manager_dashboard.html', {'profile': profile, 'pending_requests': pending_requests})





# ==================== 排行榜 ====================

def leaderboard(request):
    """冒險者戰力榜"""
    top = UserProfile.objects.all().order_by('-level', '-experience')[:100]
    return render(request, 'EngineerRPG/leaderboard.html', {'top_profiles': top})


# ==================== API 服務 ====================

@login_required
@csrf_exempt
def api_auto_layout_skill_tree(request):
    """AJAX: 自動排版算法"""
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return JsonResponse({'success': False}, status=403)
    # ==================== 管理員與後台系統 ====================

@login_required
def admin_dashboard(request):
    """系統管理員儀表板"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'):
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
        
    context = {
        'profile': profile,
        'total_users': UserProfile.objects.count(),
        'total_skills': SkillNode.objects.count(),
        'total_questions': Question.objects.count(),
        'total_equipment': Equipment.objects.count(),
        'total_items': Item.objects.count(),
    }
    return render(request, 'EngineerRPG/admin_dashboard.html', context)


@login_required
def user_management(request):
    """使用者管理"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'):
        return redirect('engineer_rpg:dashboard')
    
    users = UserProfile.objects.all().select_related('user', 'character_class')
    return render(request, 'EngineerRPG/user_management.html', {'profile': profile, 'users': users})


@login_required
def question_management(request):
    """題目管理列表"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
        
    category_id = request.GET.get('category')
    search_query = request.GET.get('q')
    
    questions = Question.objects.all().order_by('-created_at')
    if category_id:
        questions = questions.filter(category_id=category_id)
    if search_query:
        questions = questions.filter(content__icontains=search_query)
        
    paginator = Paginator(questions, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'profile': profile,
        'page_obj': page_obj,
        'categories': QuestionCategory.objects.all(),
        'selected_category': int(category_id) if category_id else None,
        'search_query': search_query,
    }
    return render(request, 'EngineerRPG/management/question_list.html', context)


@login_required
def category_management(request):
    """題目分類管理"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'):
        return redirect('engineer_rpg:dashboard')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            QuestionCategory.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description')
            )
            messages.success(request, '分類建立成功')
        elif action == 'delete':
            QuestionCategory.objects.filter(id=request.POST.get('id')).delete()
            messages.success(request, '分類已刪除')
        return redirect('engineer_rpg:category_management')
        
    return render(request, 'EngineerRPG/management/category_list.html', {
        'profile': profile,
        'categories': QuestionCategory.objects.all()
    })


@login_required
def dungeon_management(request):
    """地下城副本管理"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'):
        return redirect('engineer_rpg:dashboard')
        
    dungeons = Trial.objects.filter(trial_type='DUNGEON').order_by('-created_at')
    return render(request, 'EngineerRPG/management/dungeon_list.html', {'profile': profile, 'dungeons': dungeons})


# ==================== 晉升系統 ====================

@login_required
def apply_promotion(request):
    """申請職位晉升"""
    profile = get_or_create_user_profile(request.user)
    
    if request.method == 'POST':
        target_role = request.POST.get('target_role')
        # 檢查是否已有處理中的申請
        if PromotionRequest.objects.filter(user_profile=profile, status='PENDING').exists():
            messages.warning(request, '您已有申請正在審核中')
            return redirect('engineer_rpg:dashboard')
            
        PromotionRequest.objects.create(
            user_profile=profile,
            target_role=target_role,
            status='PENDING'
        )
        messages.success(request, '晉升申請已送出，請等待管理員審核')
        return redirect('engineer_rpg:dashboard')
        
    return render(request, 'EngineerRPG/apply_promotion.html', {'profile': profile})


@login_required
def promotion_trial(request, request_id):
    """晉升試煉"""
    profile = get_or_create_user_profile(request.user)
    promotion_request = get_object_or_404(PromotionRequest, id=request_id, applicant=profile)
    
    # 這裡可以實現晉升試煉的具體邏輯
    # 目前暫時重定向到每日試煉列表
    return redirect('engineer_rpg:daily_trial_list')


@login_required
def promotion_requests(request):
    """管理員：處理晉升申請"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
        
    requests = PromotionRequest.objects.filter(status='PENDING').order_by('-created_at')
    return render(request, 'EngineerRPG/promotion_requests.html', {'profile': profile, 'requests': requests})


@login_required
def review_request(request, request_id):
    """審核晉升申請"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
        
    promo_request = get_object_or_404(PromotionRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            promo_request.status = 'APPROVED'
            promo_request.user_profile.role = promo_request.target_role
            promo_request.user_profile.save()
            messages.success(request, '已核准晉升')
        elif action == 'reject':
            promo_request.status = 'REJECTED'
            messages.warning(request, '已拒絕晉升')
            
        promo_request.reviewed_by = profile
        promo_request.reviewed_at = timezone.now()
        promo_request.save()
        return redirect('engineer_rpg:promotion_requests')
        
    return render(request, 'EngineerRPG/review_request.html', {'profile': profile, 'promo_request': promo_request})


@login_required
def approve_request(request, request_id):
    """核准晉升申請"""
    profile = get_or_create_user_profile(request.user)
    
    if not has_whitelist_permission(request.user, 'MANAGER'):
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
    
    promotion_request = get_object_or_404(PromotionRequest, id=request_id)
    
    if promotion_request.status == 'PENDING':
        promotion_request.status = 'APPROVED'
        promotion_request.reviewer = request.user
        promotion_request.reviewed_at = timezone.now()
        promotion_request.save()
        
        # 更新申請者的等級
        applicant = promotion_request.applicant
        applicant.level = promotion_request.target_level
        applicant.save()
        
        messages.success(request, f'已核准 {applicant.user.username} 的晉升申請')
    
    return redirect('engineer_rpg:manager_dashboard')


@login_required
def reject_request(request, request_id):
    """拒絕晉升申請"""
    profile = get_or_create_user_profile(request.user)
    
    if not has_whitelist_permission(request.user, 'MANAGER'):
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
    
    promotion_request = get_object_or_404(PromotionRequest, id=request_id)
    
    if promotion_request.status == 'PENDING':
        promotion_request.status = 'REJECTED'
        promotion_request.reviewer = request.user
        promotion_request.reviewed_at = timezone.now()
        
        if request.method == 'POST':
            promotion_request.review_comment = request.POST.get('comment', '')
        
        promotion_request.save()
        
        messages.success(request, f'已拒絕 {promotion_request.applicant.user.username} 的晉升申請')
    
    return redirect('engineer_rpg:manager_dashboard')


# ==================== 技能樹編輯器 API ====================

@login_required
def skill_tree_editor(request):
    """技能樹編輯器頁面"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
        
    classes = CharacterClass.objects.all()
    selected_class = request.GET.get('class', 'CIVIL')
    
    return render(request, 'EngineerRPG/skill_tree_editor.html', {
        'profile': profile,
        'classes': classes,
        'selected_class': selected_class
    })


@login_required
@csrf_exempt
def api_save_skill_layout(request):
    """API: 儲存技能座標"""
    if request.method != 'POST' or not has_whitelist_permission(request.user, 'MANAGER'):
        return JsonResponse({'success': False}, status=403)
    try:
        data = json.loads(request.body)
        updates = data.get('updates', [])
        for item in updates:
            SkillNode.objects.filter(id=item['id']).update(
                position_x=item['x'],
                position_y=item['y']
            )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@csrf_exempt
def api_save_skill_node(request):
    """API: 儲存/新增技能節點"""
    if request.method != 'POST' or not has_whitelist_permission(request.user, 'MANAGER'):
        return JsonResponse({'success': False}, status=403)
    try:
        data = json.loads(request.body)
        node_id = data.get('id')
        if node_id:
            node = SkillNode.objects.get(id=node_id)
        else:
            node = SkillNode(position_x=100, position_y=100)
            
        node.name = data.get('name')
        node.description = data.get('description', '')
        node.node_type = data.get('type')
        
        if node.node_type != 'ROOT':
            class_code = data.get('class_code')
            if class_code:
                node.character_class = CharacterClass.objects.get(code=class_code)
        else:
            node.character_class = None
            
        node.save()
        
        if 'parents' in data:
            node.parent_skills.set(data['parents'])
            
        return JsonResponse({'success': True, 'id': node.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@csrf_exempt
def api_delete_skill_node(request):
    """API: 刪除技能節點"""
    if request.method != 'POST' or not has_whitelist_permission(request.user, 'MANAGER'):
        return JsonResponse({'success': False}, status=403)
    try:
        data = json.loads(request.body)
        SkillNode.objects.filter(id=data.get('id')).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    # 簡易層級分佈邏輯... (如前段所示)
    return JsonResponse({'success': True})


# ==================== 任務碎片與導向 ====================

@login_required
def course_study(request, course_id):
    """課程學習頁面"""
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'EngineerRPG/course_study.html', {'profile': profile, 'course': course})


@login_required
def course_exam(request, course_id):
    """課程測驗"""
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    questions = course.questions.all()
    return render(request, 'EngineerRPG/course_exam.html', {
        'profile': profile, 
        'course': course, 
        'questions': questions
    })


@login_required
def submit_course_exam(request, course_id):
    """提交課程測驗"""
    if request.method == 'POST':
        # 結算邏輯...
        messages.success(request, '課程測驗已提交')
        return redirect('engineer_rpg:skill_tree')
    return redirect('engineer_rpg:dashboard')


@login_required
def create_question(request):
    """建立新題目"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'): return redirect('engineer_rpg:dashboard')
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '題目建立成功')
            return redirect('engineer_rpg:question_management')
    else:
        form = QuestionForm()
    return render(request, 'EngineerRPG/management/question_form.html', {'profile': profile, 'form': form})


@login_required
def edit_question(request, question_id):
    """編輯題目"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'): return redirect('engineer_rpg:dashboard')
    question = get_object_or_404(Question, id=question_id)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, '題目更新成功')
            return redirect('engineer_rpg:question_management')
    else:
        form = QuestionForm(instance=question)
    return render(request, 'EngineerRPG/management/question_form.html', {'profile': profile, 'form': form, 'question': question})


@login_required
def import_questions_view(request):
    """批量匯入題目"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'): return redirect('engineer_rpg:dashboard')
    if request.method == 'POST':
        form = QuestionImportForm(request.POST, request.FILES)
        if form.is_valid():
            # 匯入邏輯...
            messages.success(request, '題目匯入完成')
            return redirect('engineer_rpg:question_management')
    else:
        form = QuestionImportForm()
    return render(request, 'EngineerRPG/management/import_questions.html', {'profile': profile, 'form': form})


@login_required
def download_template(request, format='csv'):
    """下載匯入範本"""
    # 範本生成邏輯...
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_template.csv"'
    return response

# ==================== 其他導向視圖 ====================

@login_required
def start_daily_trial_task(request, task_id):
    """額外碎片：每日任務入口補償"""
    return redirect('engineer_rpg:start_daily_trial', task_id=task_id)


# ==================== 臨時佔位符視圖（待實現） ====================
# 以下是暫時的佔位符函數，用於避免 AttributeError

@login_required
def manage_skill_tree(request):
    """主管技能樹管理"""
    return redirect('engineer_rpg:skill_tree_editor')


@login_required
def manage_questions(request):
    """主管題目管理"""
    return redirect('engineer_rpg:question_management')


@login_required
def guild_announcement_list(request):
    """公告列表"""
    profile = get_or_create_user_profile(request.user)
    announcements = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-is_pinned', '-created_at')
    page_obj = Paginator(announcements, 20).get_page(request.GET.get('page'))
    is_manager = profile.role in ('OFFICER', 'MANAGER', 'ADMIN')
    return render(request, 'EngineerRPG/guild_announcement_list.html', {
        'profile': profile,
        'page_obj': page_obj,
        'is_manager': is_manager,
    })


@login_required
def guild_announcement_edit(request, post_id):
    """編輯公會公告"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ('OFFICER', 'MANAGER', 'ADMIN'):
        return redirect('engineer_rpg:guild_dashboard')
    post = get_object_or_404(GuildPost, id=post_id, category='ANNOUNCEMENT')
    if request.method == 'POST':
        post.title = request.POST.get('title', post.title)
        post.content = request.POST.get('content', post.content)
        post.save()
        messages.success(request, '公告已更新')
        return redirect('engineer_rpg:guild_announcement_list')
    return render(request, 'EngineerRPG/guild_announcement_edit.html', {
        'profile': profile,
        'post': post,
    })


@login_required
def guild_announcement_delete(request, post_id):
    """刪除公會公告"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ('OFFICER', 'MANAGER', 'ADMIN'):
        return redirect('engineer_rpg:guild_dashboard')
    post = get_object_or_404(GuildPost, id=post_id, category='ANNOUNCEMENT')
    if request.method == 'POST':
        post.delete()
        messages.success(request, '公告已刪除')
    return redirect('engineer_rpg:guild_announcement_list')


@login_required
def create_user(request):
    """創建使用者"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:user_management')


@login_required
def edit_user(request, user_id):
    """編輯使用者"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:user_management')


@login_required
def delete_user(request, user_id):
    """刪除使用者"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:user_management')


@login_required
def delete_question(request, question_id):
    """刪除題目"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:question_management')


@login_required
def course_management(request):
    """課程管理"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:admin_dashboard')


@login_required
def create_course(request):
    """創建課程"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:course_management')


@login_required
def edit_course(request, course_id):
    """編輯課程"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:course_management')


@login_required
def delete_course(request, course_id):
    """刪除課程"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:course_management')


@login_required
def create_dungeon(request):
    """創建地下城"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:dungeon_management')


@login_required
def edit_dungeon(request, dungeon_id):
    """編輯地下城"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:dungeon_management')


@login_required
def team_management(request):
    """隊伍管理"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:admin_dashboard')


@login_required
def create_team(request):
    """創建隊伍"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:team_management')


@login_required
def edit_team(request, team_id):
    """編輯隊伍"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:team_management')


@login_required
def delete_team(request, team_id):
    """刪除隊伍"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:team_management')


@login_required
def manage_team_members(request, team_id):
    """管理隊伍成員"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:team_detail', team_id=team_id)


@login_required
def team_member_detail(request, team_id, member_id):
    """隊伍成員詳情"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:team_detail', team_id=team_id)


@login_required
def member_profile_detail(request, member_id):
    """成員詳細資料"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:dashboard')


# API 視圖
@login_required
@csrf_exempt
def api_user_stats(request):
    """API: 使用者統計資料"""
    profile = get_or_create_user_profile(request.user)
    return JsonResponse({
        'level': profile.level,
        'experience': profile.experience,
        'hp': profile.get_total_hp(),
        'mp': profile.get_total_mp()
    })


@login_required
@csrf_exempt
def api_skill_tree_data(request):
    """API: 技能樹資料"""
    return JsonResponse({'skills': []})


@login_required
@csrf_exempt
def api_skill_editor_data(request):
    """API: 技能編輯器資料"""
    return JsonResponse({'skills': []})


@login_required
@csrf_exempt
def api_manage_skill_course(request):
    """API: 管理技能課程"""
    return JsonResponse({'success': False, 'message': '功能開發中'})


@login_required
@csrf_exempt
def api_auto_distribute_xp(request):
    """API: 自動分配經驗值"""
    return JsonResponse({'success': False, 'message': '功能開發中'})


# ==================== 管理者白名單管理 ====================

@login_required
def admin_whitelist_management(request):
    """管理者白名單管理（僅 superuser）
    
    允許 superuser 管理其他使用者的管理員角色
    """
    if not request.user.is_superuser:
        messages.error(request, '權限不足：僅系統超級管理員可以訪問此功能')
        return redirect('engineer_rpg:dashboard')
    
    from .models import AdminWhitelist
    
    profile = get_or_create_user_profile(request.user)
    whitelist = AdminWhitelist.objects.all().select_related('user', 'granted_by', 'user__rpg_profile')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            user_id = request.POST.get('user_id')
            role = request.POST.get('role')
            notes = request.POST.get('notes', '')
            
            try:
                user = User.objects.get(id=user_id)
                
                # 防止將 superuser 加入白名單（他們已經是 ADMIN）
                if user.is_superuser:
                    messages.warning(request, f'{user.username} 已經是系統超級管理員，無需加入白名單')
                else:
                    whitelist_entry, created = AdminWhitelist.objects.update_or_create(
                        user=user,
                        defaults={
                            'role': role,
                            'granted_by': request.user,
                            'notes': notes
                        }
                    )
                    action_text = '已添加' if created else '已更新'
                    role_display = dict(UserProfile.ROLE_CHOICES).get(role, role)
                    messages.success(request, f'{action_text} {user.username} 為 {role_display}')
                    
            except User.DoesNotExist:
                messages.error(request, '使用者不存在')
            except Exception as e:
                messages.error(request, f'操作失敗：{str(e)}')
        
        elif action == 'remove':
            whitelist_id = request.POST.get('whitelist_id')
            try:
                entry = AdminWhitelist.objects.get(id=whitelist_id)
                user = entry.user
                entry.delete()
                
                # 重置為一般使用者
                try:
                    user.rpg_profile.role = 'ADVENTURER'
                    user.rpg_profile.save(update_fields=['role'])
                except:
                    pass
                    
                messages.success(request, f'已移除 {user.username} 的管理權限，重置為冒險者')
            except AdminWhitelist.DoesNotExist:
                messages.error(request, '白名單項目不存在')
            except Exception as e:
                messages.error(request, f'移除失敗：{str(e)}')
        
        return redirect('engineer_rpg:admin_whitelist_management')
    
    # 可以被加入白名單的使用者（排除已在白名單中的和 superuser）
    available_users = User.objects.exclude(
        admin_whitelist__isnull=False
    ).exclude(
        is_superuser=True
    ).select_related('rpg_profile').order_by('username')
    
    context = {
        'profile': profile,
        'whitelist': whitelist,
        'available_users': available_users,
        'role_choices': UserProfile.ROLE_CHOICES,
    }
    
    return render(request, 'EngineerRPG/admin_whitelist.html', context)


# ==================== Codex ====================

@login_required
def codex_main(request):
    """Codex overview page."""
    profile = get_or_create_user_profile(request.user)
    skill_scope = SkillNode.objects.filter(
        Q(character_class=profile.character_class) | Q(character_class__isnull=True)
    )

    stats = {
        'equipment': {
            'owned': UserEquipment.objects.filter(user_profile=profile).count(),
            'total': Equipment.objects.count(),
        },
        'items': {
            'owned': UserItem.objects.filter(user_profile=profile, quantity__gt=0).count(),
            'total': Item.objects.count(),
        },
        'skills': {
            'completed': UserSkill.objects.filter(
                user_profile=profile,
                skill_node__in=skill_scope,
                status='COMPLETED',
            ).count(),
            'total': skill_scope.count(),
        },
        'achievements': {
            'earned': UserAchievement.objects.filter(user_profile=profile).count(),
            'total': Achievement.objects.count(),
        },
    }

    return render(
        request,
        'EngineerRPG/codex/codex_main.html',
        {'profile': profile, 'stats': stats},
    )


@login_required
def codex_equipment(request):
    """Codex equipment list with filters."""
    profile = get_or_create_user_profile(request.user)

    selected_type = request.GET.get('type', 'all')
    selected_rarity = request.GET.get('rarity', 'all')
    selected_tier = request.GET.get('tier', 'all')
    selected_obtain = request.GET.get('obtain', 'all')

    equipment_qs = Equipment.objects.all()
    if selected_type != 'all':
        equipment_qs = equipment_qs.filter(equipment_type=selected_type)
    if selected_rarity != 'all':
        equipment_qs = equipment_qs.filter(rarity=selected_rarity)
    if selected_tier != 'all':
        try:
            equipment_qs = equipment_qs.filter(tier=int(selected_tier))
        except (TypeError, ValueError):
            selected_tier = 'all'
    if selected_obtain != 'all':
        equipment_qs = equipment_qs.filter(obtain_method=selected_obtain)

    equipment_qs = equipment_qs.select_related('required_skill').order_by(
        'tier', 'equipment_type', 'name'
    )

    user_equipment_map = {
        ue.equipment_id: ue
        for ue in UserEquipment.objects.filter(
            user_profile=profile,
            equipment__in=equipment_qs,
        ).select_related('equipment')
    }

    equipment_list = []
    for equipment in equipment_qs:
        user_equipment = user_equipment_map.get(equipment.id)
        equipment_list.append({
            'equipment': equipment,
            'owned': user_equipment is not None,
            'user_equipment': user_equipment,
        })

    context = {
        'profile': profile,
        'equipment_list': equipment_list,
        'owned': UserEquipment.objects.filter(user_profile=profile).count(),
        'total': Equipment.objects.count(),
        'type_choices': Equipment.EQUIPMENT_TYPE_CHOICES,
        'rarity_choices': Equipment.RARITY_CHOICES,
        'tier_choices': Equipment._meta.get_field('tier').choices,
        'obtain_choices': Equipment.OBTAIN_METHOD_CHOICES,
        'filters': {
            'type': selected_type,
            'rarity': selected_rarity,
            'tier': selected_tier,
            'obtain': selected_obtain,
        },
    }
    return render(request, 'EngineerRPG/codex/codex_equipment.html', context)


@login_required
def codex_equipment_detail(request, equipment_id):
    """Codex equipment detail page."""
    profile = get_or_create_user_profile(request.user)
    equipment = get_object_or_404(
        Equipment.objects.select_related('required_skill'),
        id=equipment_id,
    )
    user_equipment = UserEquipment.objects.filter(
        user_profile=profile,
        equipment=equipment,
    ).first()

    trial_filter = Q(equipment_reward=equipment)
    if equipment.obtain_trial_id:
        trial_filter |= Q(id=equipment.obtain_trial_id)
    related_trials = Trial.objects.filter(trial_filter, is_active=True).select_related(
        'category'
    ).order_by('required_level', 'title').distinct()

    return render(request, 'EngineerRPG/codex/codex_equipment_detail.html', {
        'profile': profile,
        'equipment': equipment,
        'owned': user_equipment is not None,
        'user_equipment': user_equipment,
        'related_trials': related_trials,
    })


@login_required
def codex_items(request):
    """Codex item list with filters."""
    profile = get_or_create_user_profile(request.user)

    selected_type = request.GET.get('type', 'all')
    selected_rarity = request.GET.get('rarity', 'all')
    selected_effect = request.GET.get('effect', 'all')

    item_qs = Item.objects.all()
    if selected_type != 'all':
        item_qs = item_qs.filter(item_type=selected_type)
    if selected_rarity != 'all':
        item_qs = item_qs.filter(rarity=selected_rarity)
    if selected_effect != 'all':
        item_qs = item_qs.filter(effect_type=selected_effect)

    item_qs = item_qs.order_by('rarity', 'name')

    user_item_map = {
        ui.item_id: ui
        for ui in UserItem.objects.filter(
            user_profile=profile,
            quantity__gt=0,
            item__in=item_qs,
        ).select_related('item')
    }

    item_list = []
    for item in item_qs:
        user_item = user_item_map.get(item.id)
        item_list.append({
            'item': item,
            'owned': user_item is not None,
            'quantity': user_item.quantity if user_item else 0,
        })

    context = {
        'profile': profile,
        'item_list': item_list,
        'owned': UserItem.objects.filter(user_profile=profile, quantity__gt=0).count(),
        'total': Item.objects.count(),
        'type_choices': Item.ITEM_TYPE_CHOICES,
        'rarity_choices': Item.RARITY_CHOICES,
        'effect_choices': Item.EFFECT_TYPE_CHOICES,
        'filters': {
            'type': selected_type,
            'rarity': selected_rarity,
            'effect': selected_effect,
        },
    }
    return render(request, 'EngineerRPG/codex/codex_items.html', context)


@login_required
def codex_item_detail(request, item_id):
    """Codex item detail page."""
    profile = get_or_create_user_profile(request.user)
    item = get_object_or_404(Item, id=item_id)
    user_item = UserItem.objects.filter(
        user_profile=profile,
        item=item,
        quantity__gt=0,
    ).first()

    related_trials = Trial.objects.filter(
        item_reward=item,
        is_active=True,
    ).select_related('category').order_by('required_level', 'title')

    return render(request, 'EngineerRPG/codex/codex_item_detail.html', {
        'profile': profile,
        'item': item,
        'owned': user_item is not None,
        'quantity': user_item.quantity if user_item else 0,
        'related_trials': related_trials,
    })


@login_required
def codex_skills(request):
    """Codex skill list with status and filters."""
    profile = get_or_create_user_profile(request.user)

    selected_type = request.GET.get('type', 'all')
    selected_class = request.GET.get('class', 'all')

    base_qs = SkillNode.objects.filter(
        Q(character_class=profile.character_class) | Q(character_class__isnull=True)
    ).select_related('character_class').prefetch_related('parent_skills')

    filtered_qs = base_qs
    if selected_type != 'all':
        filtered_qs = filtered_qs.filter(node_type=selected_type)
    if selected_class != 'all':
        filtered_qs = filtered_qs.filter(character_class__code=selected_class)

    user_skill_map = {
        us.skill_node_id: us
        for us in UserSkill.objects.filter(
            user_profile=profile,
            skill_node__in=filtered_qs,
        ).select_related('skill_node')
    }

    skill_list = []
    for skill in filtered_qs.order_by('min_level', 'node_type', 'name'):
        user_skill = user_skill_map.get(skill.id)
        unlocked = check_skill_unlocked(profile, skill)
        if user_skill:
            status = user_skill.status
            if status == 'LOCKED' and unlocked:
                status = 'AVAILABLE'
            progress = user_skill.progress
        else:
            status = 'AVAILABLE' if unlocked else 'LOCKED'
            progress = 0

        skill_list.append({
            'skill': skill,
            'status': status,
            'progress': progress,
        })

    class_choices = list(
        CharacterClass.objects.order_by('id').values_list('code', 'name')
    )

    context = {
        'profile': profile,
        'skill_list': skill_list,
        'completed': UserSkill.objects.filter(
            user_profile=profile,
            skill_node__in=base_qs,
            status='COMPLETED',
        ).count(),
        'total': base_qs.count(),
        'type_choices': SkillNode.NODE_TYPE_CHOICES,
        'class_choices': class_choices,
        'filters': {
            'type': selected_type,
            'class': selected_class,
        },
    }
    return render(request, 'EngineerRPG/codex/codex_skills.html', context)


@login_required
def codex_obtain_guide(request):
    """Codex obtain guide grouped by source."""
    profile = get_or_create_user_profile(request.user)

    equipment_by_method = {}
    for code, name in Equipment.OBTAIN_METHOD_CHOICES:
        equipment_list = list(
            Equipment.objects.filter(obtain_method=code, is_obtainable=True).order_by(
                'tier', 'rarity', 'name'
            )
        )
        if equipment_list:
            equipment_by_method[code] = {'name': name, 'items': equipment_list}

    items_by_method = {}
    for code, name in Item.OBTAIN_METHOD_CHOICES:
        item_list = list(
            Item.objects.filter(obtain_method=code, is_obtainable=True).order_by(
                'rarity', 'name'
            )
        )
        if item_list:
            items_by_method[code] = {'name': name, 'items': item_list}

    trials_with_rewards = Trial.objects.filter(
        is_active=True
    ).filter(
        Q(equipment_reward__isnull=False) | Q(item_reward__isnull=False)
    ).select_related(
        'category', 'equipment_reward', 'item_reward'
    ).order_by(
        'required_level', 'trial_type', 'title'
    )

    return render(request, 'EngineerRPG/codex/codex_obtain_guide.html', {
        'profile': profile,
        'equipment_by_method': equipment_by_method,
        'items_by_method': items_by_method,
        'trials_with_rewards': trials_with_rewards,
    })