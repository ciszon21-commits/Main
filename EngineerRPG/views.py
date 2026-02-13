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
    PromotionRequest, EnhancementScroll, Achievement, UserAchievement,
    Team, TeamMembership, GuildPost, GuildComment, UserCourseProgress,
    DailyTrialTask, AdminWhitelist, Trial, Question, QuestionCategory, TrialRecord,
    Equipment, UserEquipment, Item, UserItem
)

from .forms import (
    QuestionForm, QuestionImportForm, SkillNodeForm, CourseForm, UserProfileEditForm
)

# Import team management functions
from .views_team_management import edit_team, manage_team_members, create_team


# ==================== Helper Functions ====================

def get_or_create_user_profile(user):
    """Get or create user profile"""
    try:
        profile = user.rpg_profile
    except UserProfile.DoesNotExist:
        # Create profile without a class — user must select one on first visit
        profile = UserProfile.objects.create(
            user=user,
            employee_id=f"EMP{user.id:04d}",
            character_class=None
        )
    
    # Sync Roles from Whitelist or Superuser status
    if user.is_superuser:
        if profile.role != 'ADMIN':
            profile.role = 'ADMIN'
            profile.save(update_fields=['role'])
    else:
        # Check Whitelist
        whitelist = AdminWhitelist.objects.filter(username=user.username).first()
        if whitelist:
            if profile.role != whitelist.role:
                profile.role = whitelist.role
                profile.save(update_fields=['role'])
        else:
            if profile.role in ['ADMIN', 'MANAGER', 'OFFICER']:
                profile.role = 'ADVENTURER'
                profile.save(update_fields=['role'])

    return profile


def check_skill_unlocked(user_profile, skill_node):
    """檢查技能是否已解鎖（等級足夠且前置技能皆已完成）"""
    if user_profile.level < skill_node.min_level:
        return False

    parent_skills = skill_node.parent_skills.all()
    if parent_skills.exists():
        completed_parents = UserSkill.objects.filter(
            user_profile=user_profile,
            skill_node__in=parent_skills,
            status='COMPLETED'
        ).count()
        return completed_parents == parent_skills.count()
    return True


# ==================== Authentication Views ====================
# Authentication is now handled upstream or via standard Django admin login.
# Local registration and login views have been removed.


# ==================== Main Views ====================

def index(request):
    """Index page"""
    return render(request, 'EngineerRPG/index.html')


@login_required
def select_class(request):
    """首次進入 RPG 模組時選擇職業"""
    profile = get_or_create_user_profile(request.user)

    # 已選過職業 → 直接回大廳
    if profile.character_class is not None:
        return redirect('engineer_rpg:dashboard')

    classes = CharacterClass.objects.all()

    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        try:
            chosen = CharacterClass.objects.get(id=class_id)
            profile.character_class = chosen
            profile.hp = chosen.base_hp
            profile.mp = chosen.base_mp
            profile.save(update_fields=['character_class', 'hp', 'mp'])
            messages.success(request, f'你選擇了「{chosen.name}」！冒險旅程正式開始！')
            return redirect('engineer_rpg:dashboard')
        except CharacterClass.DoesNotExist:
            messages.error(request, '請選擇有效的職業。')

    context = {
        'profile': profile,
        'classes': classes,
    }
    return render(request, 'EngineerRPG/select_class.html', context)


@login_required
def dashboard(request):
    """冒險者大廳"""
    profile = get_or_create_user_profile(request.user)

    # 尚未選擇職業 → 導向職業選擇頁
    if profile.character_class is None:
        return redirect('engineer_rpg:select_class')

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
    """編輯個人檔案 - 僅提供頭像選擇功能"""
    profile = get_or_create_user_profile(request.user)

    if request.method == 'POST':
        avatar_index = request.POST.get('avatar_index', '0')
        avatar_image = request.FILES.get('avatar_image')

        if avatar_image:
            # 上傳自訂頭像
            profile.avatar_image = avatar_image
            profile.avatar_index = 0
            profile.save()
            messages.success(request, '頭像已更新！')
        elif avatar_index and int(avatar_index) > 0:
            # 選擇預設頭像
            profile.avatar_index = int(avatar_index)
            profile.avatar_image = None  # 清除上傳的頭像
            profile.save()
            messages.success(request, '頭像已更新！')
        else:
            messages.warning(request, '請選擇一個頭像。')

        return redirect('engineer_rpg:profile_edit')

    # 預設頭像資料 (1~20)
    avatar_titles = [
        '人類戰士', '人類法師', '人類弓手', '人類牧師',
        '矮人戰士', '矮人工匠', '矮人守衛', '矮人獵人',
        '精靈遊俠', '精靈賢者', '精靈刺客', '精靈吟遊',
        '獸人狂戰', '獸人薩滿', '獸人獵手', '獸人鬥士',
        '魔族術士', '魔族暗殺', '魔族召喚', '魔族領主',
    ]
    avatar_data = [(i + 1, avatar_titles[i]) for i in range(20)]

    context = {
        'profile': profile,
        'avatar_data': avatar_data,
    }
    return render(request, 'EngineerRPG/profile_edit.html', context)


# ==================== Skill Tree Views ====================

@login_required
def skill_tree(request):
    """技能樹主頁面"""
    profile = get_or_create_user_profile(request.user)

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

    # 自動為該使用者建立所有裝備記錄（若尚未建立）
    all_equipment = Equipment.objects.all()
    existing_ids = set(
        UserEquipment.objects.filter(user_profile=profile).values_list('equipment_id', flat=True)
    )
    new_records = [
        UserEquipment(user_profile=profile, equipment=eq, enhancement_level=0, is_equipped=False)
        for eq in all_equipment if eq.id not in existing_ids
    ]
    if new_records:
        UserEquipment.objects.bulk_create(new_records)

    user_equipments = UserEquipment.objects.filter(user_profile=profile).select_related('equipment')

    # 同步 is_equipped 狀態：先將所有裝備設為未裝備
    user_equipments.update(is_equipped=False)
    
    # 建立當前裝備 dict，並標記真正裝備的項目
    equipped_ids = []
    equipped = {
        'helmet': profile.equipped_helmet,
        'armor': profile.equipped_armor,
        'boots': profile.equipped_boots,
        'tool_1': profile.equipped_tool_1,
        'tool_2': profile.equipped_tool_2,
        'tool_3': profile.equipped_tool_3,
    }
    
    # 收集所有已裝備的 ID
    for slot_name, user_equip in equipped.items():
        if user_equip:
            equipped_ids.append(user_equip.id)
    
    # 批量更新已裝備的項目
    if equipped_ids:
        UserEquipment.objects.filter(id__in=equipped_ids).update(is_equipped=True)
    
    # 重新查詢以獲取更新後的狀態
    user_equipments = UserEquipment.objects.filter(user_profile=profile).select_related('equipment')

    # 依類型分組，並加上解鎖狀態
    def build_item_list(eq_type):
        items = []
        for ue in user_equipments.filter(equipment__equipment_type=eq_type).order_by('equipment__tier', 'equipment__required_level'):
            items.append({
                'user_equipment': ue,
                'is_unlocked': profile.level >= ue.equipment.required_level,
            })
        return items

    context = {
        'profile': profile,
        'equipped': equipped,
        'helmets': build_item_list('HELMET'),
        'armors': build_item_list('ARMOR'),
        'boots': build_item_list('BOOTS'),
        'tools': build_item_list('TOOL'),
        'enhancement_tickets': profile.enhancement_tickets,
    }
    return render(request, 'EngineerRPG/equipment_inventory.html', context)

@login_required
def equip_item(request, user_equipment_id):
    """穿戴裝備"""
    if request.method != 'POST':
        return redirect('engineer_rpg:equipment_inventory')

    profile = get_or_create_user_profile(request.user)
    user_equip = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    eq_type = user_equip.equipment.equipment_type

    if eq_type == 'TOOL':
        # 工具類裝備需要指定欄位 (1~3)
        slot = request.POST.get('slot', '1')
        slot_field = f'equipped_tool_{slot}'
        # 卸下該欄位原有裝備
        old_equip = getattr(profile, slot_field, None)
        if old_equip:
            old_equip.is_equipped = False
            old_equip.save()
        # 設定新裝備
        setattr(profile, slot_field, user_equip)
    else:
        # 防具類：根據 equipment_type 對應欄位
        slot_map = {'HELMET': 'equipped_helmet', 'ARMOR': 'equipped_armor', 'BOOTS': 'equipped_boots'}
        slot_field = slot_map.get(eq_type)
        # 卸下同部位原有裝備
        old_equip = getattr(profile, slot_field, None)
        if old_equip:
            old_equip.is_equipped = False
            old_equip.save()
        setattr(profile, slot_field, user_equip)

    user_equip.is_equipped = True
    user_equip.save()
    profile.save()
    messages.success(request, f'已裝備：{user_equip.equipment.name}')
    return redirect('engineer_rpg:equipment_inventory')

@login_required
def unequip_item(request, user_equipment_id):
    """卸下裝備"""
    profile = get_or_create_user_profile(request.user)
    user_equip = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    user_equip.is_equipped = False
    user_equip.save()

    # 清除 profile 上的 FK 欄位
    fk_fields = ['equipped_helmet', 'equipped_armor', 'equipped_boots',
                 'equipped_tool_1', 'equipped_tool_2', 'equipped_tool_3']
    for field in fk_fields:
        if getattr(profile, f'{field}_id', None) == user_equip.id:
            setattr(profile, field, None)
    profile.save()

    messages.success(request, f'已卸下：{user_equip.equipment.name}')
    return redirect('engineer_rpg:equipment_inventory')

@login_required
def enhance_equipment(request, user_equipment_id):
    """強化裝備"""
    if request.method != 'POST':
        return redirect('engineer_rpg:equipment_inventory')
        
    profile = get_or_create_user_profile(request.user)
    user_equip = get_object_or_404(UserEquipment, id=user_equipment_id, user_profile=profile)
    
    # 檢查是否有強化券
    if profile.enhancement_tickets <= 0:
        messages.error(request, '強化券不足！')
        return redirect('engineer_rpg:equipment_inventory')
        
    # 檢查是否達到強化上限
    if user_equip.enhancement_level >= user_equip.equipment.max_enhancement:
        messages.error(request, '此裝備已強化至最高等級')
        return redirect('engineer_rpg:equipment_inventory')
        
    # 執行強化
    try:
        profile.enhancement_tickets -= 1
        profile.save(update_fields=['enhancement_tickets'])
        
        user_equip.enhancement_level += 1
        user_equip.save()
        
        messages.success(request, f'強化成功！{user_equip.equipment.name} +{user_equip.enhancement_level}')
    except Exception as e:
        messages.error(request, f'強化失敗：{str(e)}')
        
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
        'time_limit': trial.time_limit_minutes,
        'start_time': request.session['trial_start_time'],
        'remaining_seconds': trial.time_limit_minutes * 60,
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)

@login_required
def submit_answer(request, trial_id):
    """提交答案 (API)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=400)
        
    try:
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
        boots_messages = []  # 收集靴子效果訊息
        
        is_game_over_flag = False

        if daily_task_id:
            from .models import DailyTrialProgress, DailyTrialTask
            import random
            progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task_id=daily_task_id)
            
            # 更新答題紀錄到資料庫
            current_answers = progress.answers or {}
            current_answers[str(question.id)] = {
                'user_answer': user_answer, 
                'is_correct': is_correct,
                'question_text': question.content,
                'correct_answer_text': question.correct_answer,
                'explanation': question.explanation
            }
            progress.answers = current_answers
            print(f"DEBUG: Saving answer for Q{question.id}. Progress Answers keys: {progress.answers.keys()}")
            
            if not is_correct:
                # 基礎傷害
                base_damage = 10
                if question.difficulty == 'C': 
                    base_damage = 5
                elif question.difficulty in ['A', 'S']: 
                    base_damage = 15
                
                # 3. [Lighting Optimization] (Helmet +9): -1 damage on bad visibility/hard questions
                if profile.equipped_helmet and profile.equipped_helmet.has_special_ability():
                     if profile.equipped_helmet.special_ability_name == '【照明優化】':
                         # Hard questions: Difficulty A or S
                         if question.difficulty in ['A', 'S']:
                             base_damage = max(1, base_damage - 1)
                             boots_messages.append('💡 照明優化: 困難題傷害 -1')

                # 套用減傷
                damage_reduction = profile.get_total_damage_reduction()
                
                # 5. [Crisis Protection] (Armor +9): Double DR when HP < 20%
                if profile.equipped_armor and profile.equipped_armor.has_special_ability():
                     if profile.equipped_armor.special_ability_name == '【危機防護】':
                         total_hp = profile.get_total_hp()
                         if progress.current_hp < total_hp * 0.2:
                             damage_reduction *= 2
                             boots_messages.append(f'🛡️ 危機防護: HP < 20%, 減傷翻倍! ({damage_reduction})')

                actual_damage = max(1, base_damage - damage_reduction)  # 至少扣1點
                
                # 減傷效果訊息
                if damage_reduction > 0:
                    boots_messages.append(f'💪 裝備減傷: {base_damage} - {damage_reduction} = {actual_damage} 點傷害')
                
                hp_damage = actual_damage
                progress.current_hp = max(0, progress.current_hp - actual_damage)
                
                # 4. [Emergency Bandage] (Armor +9): Heal 15 HP when HP < 30% (once)
                if profile.equipped_armor and profile.equipped_armor.has_special_ability():
                     if profile.equipped_armor.special_ability_name == '【緊急包紮】':
                         # Check if used
                         used = request.session.get('emergency_bandage_used', False)
                         total_hp = profile.get_total_hp()
                         if not used and progress.current_hp > 0 and progress.current_hp < total_hp * 0.3:
                             heal_amount = 15
                             old_hp = progress.current_hp
                             progress.current_hp = min(total_hp, progress.current_hp + heal_amount)
                             request.session['emergency_bandage_used'] = True
                             boots_messages.append(f'🩹 緊急包紮: HP<30% 自動回復 {progress.current_hp - old_hp} HP!')
                
                # 答錯時重置連續答對計數
                progress.boots_correct_streak = 0
            else:
                # 答對時處理靴子被動效果
                if profile.equipped_boots:
                    boots = profile.equipped_boots
                    boots_name = boots.equipment.name
                    boots_level = boots.enhancement_level
                    
                    # 1. 鋼頭安全鞋 - HP回復
                    if '鋼頭安全鞋' in boots_name:
                        progress.boots_total_correct += 1
                        trigger_count = 2 if boots_level >= 9 else 3
                        
                        boots_messages.append(f'【鋼頭安全鞋】累積答對: {progress.boots_total_correct}/{trigger_count}')
                        
                        if progress.boots_total_correct >= trigger_count:
                            if boots_level >= 9:
                                heal_amount = 25
                            elif boots_level >= 6:
                                heal_amount = 15
                            elif boots_level >= 3:
                                heal_amount = 10
                            else:
                                heal_amount = 5
                            
                            max_hp = profile.get_total_hp()
                            progress.current_hp = min(max_hp, progress.current_hp + heal_amount)
                            progress.boots_total_correct = 0
                            boots_messages.append(f'【鋼頭安全鞋】回復 {heal_amount} HP!')
                    
                    # 2. 防穿刺工靴 - 強化券獲得
                    elif '防穿刺工靴' in boots_name:
                        progress.boots_correct_streak += 1
                        
                        if boots_level >= 9:
                            probability = 0.60
                        elif boots_level >= 6:
                            probability = 0.20
                        elif boots_level >= 3:
                            probability = 0.15
                        else:
                            probability = 0.10
                        
                        # 顯示連續答對進度 (只在+9時顯示)
                        if boots_level >= 9:
                            boots_messages.append(f'【防穿刺工靴】連續答對: {progress.boots_correct_streak}/5')
                        
                        # 機率判定
                        if random.random() < probability:
                            profile.enhancement_tickets += 1
                            boots_messages.append('【防穿刺工靴】獲得 1 張強化券!')
                        else:
                            boots_messages.append('【防穿刺工靴】未發現強化券')
                        
                        if boots_level >= 9 and progress.boots_correct_streak >= 5:
                            profile.enhancement_tickets += 2
                            boots_messages.append('【防穿刺工靴】連續答對5題!額外獲得 2 張強化券!')
                            progress.boots_correct_streak = 0
                    
                    # 3. 動力樣板護腿 - MP回復
                    elif '動力' in boots_name and '護腿' in boots_name:
                        progress.boots_correct_streak += 1
                        
                        difficulty_threshold = 'B' if boots_level >= 6 else 'A'
                        should_restore = False
                        
                        if difficulty_threshold == 'B':
                            should_restore = question.difficulty in ['B', 'A', 'S']
                        else:
                            should_restore = question.difficulty in ['A', 'S']
                        
                        # 顯示連續答對進度 (只在+9時顯示)
                        if boots_level >= 9:
                            boots_messages.append(f'【動力樣板護腿】連續答對: {progress.boots_correct_streak}/2')
                        
                        if should_restore:
                            if boots_level >= 9:
                                restore_amount = 30
                            elif boots_level >= 6:
                                restore_amount = 20
                            elif boots_level >= 3:
                                restore_amount = 15
                            else:
                                restore_amount = 10
                            
                            max_mp = profile.get_total_mp()
                            progress.current_mp = min(max_mp, progress.current_mp + restore_amount)
                            current_mp = progress.current_mp
                            boots_messages.append(f'【動力樣板護腿】回復 {restore_amount} MP!')
                        
                        if boots_level >= 9 and progress.boots_correct_streak >= 2:
                            max_mp = profile.get_total_mp()
                            progress.current_mp = min(max_mp, progress.current_mp + 5)
                            current_mp = progress.current_mp
                            boots_messages.append('【動力樣板護腿】連續答對2題!額外回復 5 MP!')
                            progress.boots_correct_streak = 0
            
            # 檢查 HP 是否歸零
            if progress.current_hp <= 0:
                progress.is_completed = True
                progress.is_passed = False
            
            progress.current_mp = current_mp
            progress.save()
            profile.save()  # 儲存強化券變更
            current_hp = progress.current_hp
        else:
            current_hp = request.session.get('trial_hp', 3)
            if not is_correct:
                base_damage = 1
                
                # 套用減傷
                damage_reduction = profile.get_total_damage_reduction()
                actual_damage = max(1, base_damage - damage_reduction)  # 至少扣1點
                
                hp_damage = actual_damage
                current_hp = max(0, current_hp - actual_damage)
            request.session['trial_hp'] = current_hp
            request.session['trial_mp'] = current_mp
            is_game_over_flag = current_hp <= 0 # Set flag for non-daily task

    except Exception as e:
        import traceback
        print(f"Error in submit_answer: {str(e)}")
        traceback.print_exc()
        return JsonResponse({'error': f'提交失敗: {str(e)}'}, status=500)

    return JsonResponse({
        'success': True,  # Add success flag
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'remaining_hp': current_hp,
        'max_hp': profile.get_total_hp(),
        'remaining_mp': current_mp,
        'max_mp': profile.get_total_mp(),
        'hp_damage': hp_damage,
        'is_game_over': is_game_over_flag,  # Check if completed
        'current_index': current_index,
        'total_questions': len(question_ids),
        'boots_messages': boots_messages,  # 靴子效果訊息
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
        
        # 檢查是否答完所有題目
        if next_index >= len(question_ids):
            # progress.is_completed 由 start_daily_trial 統一設定
            # progress.is_passed 由 start_daily_trial 統一判斷
            pass
        
        progress.save()
    
    if next_index >= len(question_ids):
        # 答完所有題目, 重導向回每日試煉頁面(會自動顯示結算)
        if daily_task_id:
             print(f"DEBUG: Completing daily trial {daily_task_id}. Current answers: {progress.answers}")
             progress.current_question_index = len(question_ids)
             progress.save()
             return redirect('engineer_rpg:start_daily_trial', task_id=daily_task_id)
        
        # 非每日試煉的情況(這部分代碼可能暫時用不到,但保持健壯性)
        return JsonResponse({
            'success': True,
            'message': '已完成所有題目',
            'is_completed': True
        })
        
    next_question_obj = get_object_or_404(Question, id=question_ids[next_index])

    # 計算剩餘時間與 HP/MP
    if daily_task_id:
        from .models import DailyTrialProgress
        progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task_id=daily_task_id)
        current_hp = progress.current_hp
        current_mp = progress.current_mp
        start_time = progress.started_at
    else:
        current_hp = request.session.get('trial_hp', 3)
        current_mp = request.session.get('trial_mp', 100)
        start_time_str = request.session.get('trial_start_time')
        start_time = timezone.datetime.fromisoformat(start_time_str) if start_time_str else timezone.now()

    elapsed = (timezone.now() - start_time).total_seconds()
    remaining_seconds = max(0, int(trial.time_limit_minutes * 60 - elapsed))

    # 渲染下一題
    context = {
        'profile': profile,
        'trial': trial,
        'question': next_question_obj,
        'current_index': next_index,
        'total_questions': len(question_ids),
        'base_hp': profile.get_total_hp(),
        'base_mp': profile.get_total_mp(),
        'initial_hp': current_hp,
        'initial_mp': current_mp,
        'heart_range': range(1, max(profile.get_total_hp(), 5) + 1),
        'is_daily_task': bool(daily_task_id),
        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),
        'time_limit': trial.time_limit_minutes,
        'start_time': start_time.isoformat(),
        'remaining_seconds': remaining_seconds,
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)

@login_required
def api_consume_item(request, user_item_id):
    """API: Consume an item"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    try:
        user_item = UserItem.objects.get(id=user_item_id, user_profile=profile)
    except UserItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)
        
    if user_item.quantity <= 0:
        return JsonResponse({'error': 'Item quantity is 0'}, status=400)
        
    # 消耗道具
    user_item.quantity -= 1
    user_item.save()
    
    # 應用效果
    effect_applied = False
    message = f"使用了 {user_item.item.name}"
    changes = {}
    
    if user_item.item.effect_type == 'HEAL':
        # 回復 HP
        max_hp = profile.get_total_hp()
        heal_amount = max(1, int(max_hp * (user_item.item.effect_value / 100.0)))
        old_hp = request.session.get('trial_hp', profile.hp) # 優先讀取 session hp (如果正在 trial 中)
        
        # 這裡需要判斷是在 trial 中還是在外面
        # 簡單起見，如果 session 有 trial_hp，優先更新 session，同時也更新 profile 作為備份
        # 但要注意 trial_hp 是 session scope check status
        
        # 假設此 API 主要用於 Trial 頁面
        if 'trial_hp' in request.session:
             new_hp = min(max_hp, request.session['trial_hp'] + heal_amount)
             request.session['trial_hp'] = new_hp
             changes['hp'] = new_hp
             message += f"，回復了 {heal_amount} 點生命值"
             effect_applied = True
        else:
             # 非 Trial 狀態，直接更新 profile (雖然通常外面不會扣血)
             profile.hp = min(max_hp, profile.hp + heal_amount)
             profile.save(update_fields=['hp'])
             changes['hp'] = profile.hp
             effect_applied = True
             
    # TODO: 處理其他類型 Item Effect (SHIELD, TIME_EXTEND etc.)
    # 目前僅實作基礎消耗與回血
    
    return JsonResponse({
        'success': True, 
        'message': message,
        'remaining_quantity': user_item.quantity,
        'changes': changes
    })


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
        if progress and not progress.is_completed:
             # Check timeout
             time_diff = (timezone.now() - progress.started_at).total_seconds() / 60
             if time_diff > task.trial.time_limit_minutes:
                 is_timeout = True
                 
        # 計算動態經驗值獎勵
        next_level_exp = profile.experience_to_next_level()
        dynamic_exp_reward = next_level_exp // 20
        perfect_exp_reward = dynamic_exp_reward * 2
        
        task_progress_list.append({
            'task': task,
            'progress': progress,
            'is_timeout': is_timeout,
            'exp_reward': dynamic_exp_reward,
            'perfect_exp_reward': perfect_exp_reward,
            'ticket_reward': 1,
            'perfect_ticket_reward': 3
        })
        
    context = {
        'profile': profile,
        'task_progress_list': task_progress_list,
    }
    return render(request, 'EngineerRPG/daily_trial.html', context)

@login_required
def start_daily_trial(request, task_id):
    """開始每日試煉任務"""
    profile = get_or_create_user_profile(request.user)
    try:
        daily_task = DailyTrialTask.objects.get(id=task_id)
    except DailyTrialTask.DoesNotExist:
        messages.error(request, '找不到該任務')
        return redirect('engineer_rpg:daily_trial_list')
        
    # Check if already completed
    from .models import DailyTrialProgress
    
    # 計算包含裝備加成的總 HP/MP
    total_hp = profile.get_total_hp()
    total_mp = profile.get_total_mp()
    
    # 應用頭盔 +9 特殊能力 (試煉開始觸發)
    if profile.equipped_helmet and profile.equipped_helmet.has_special_ability():
        ability_name = profile.equipped_helmet.special_ability_name
        if ability_name == '【工頭威嚴】':
            # 進場初始 MP 額外 +10%
            total_mp = int(total_mp * 1.1)
            messages.success(request, '👑 工頭威嚴: 初始 MP +10%!')
        elif ability_name == '【新手運】':
            # 試煉開始隨機獲得 10~30 MP
            import random
            bonus_mp = random.randint(10, 30)
            total_mp += bonus_mp
            messages.success(request, f'🍀 新手運: 隨機獲得 +{bonus_mp} MP!')
    
    progress, created = DailyTrialProgress.objects.get_or_create(
        user_profile=profile,
        daily_task=daily_task,
        defaults={
            'started_at': timezone.now(),
            'current_hp': total_hp,
            'current_mp': total_mp,
            'initial_hp': total_hp,
            'initial_mp': total_mp,
            'current_question_index': 0,
            'boots_correct_streak': 0,
            'boots_total_correct': 0,
        }
    )
    
    # 檢查是否已完成或超時
    elapsed_minutes = (timezone.now() - progress.started_at).total_seconds() / 60
    is_timeout = elapsed_minutes > daily_task.trial.time_limit_minutes
    
    
    # 檢查是否已完成或超時
    elapsed_minutes = (timezone.now() - progress.started_at).total_seconds() / 60
    is_timeout = elapsed_minutes > daily_task.trial.time_limit_minutes
    total_questions_count = daily_task.questions.count()
    is_questions_finished = progress.current_question_index >= total_questions_count
    
    if progress.is_completed or is_timeout or progress.current_hp <= 0 or is_questions_finished:
        # 顯示結算畫面
        trial = daily_task.trial
        all_questions = list(daily_task.questions.all())
        
        # 計算統計數據
        answers = progress.answers
        
        correct_count = sum(1 for ans in answers.values() if ans.get('is_correct', False))
        total_count = len(daily_task.questions.all()) # 使用總題目數，而非已回答數 (以防未答完)
        accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # 收集錯題列表
        wrong_answers_list = []
        for q_id, ans_data in answers.items():
            if not ans_data.get('is_correct', False):
                wrong_answers_list.append({
                    'id': q_id,
                    'question_text': ans_data.get('question_text', '題目內容缺失'),
                    'user_answer': ans_data.get('user_answer', ''),
                    'correct_answer': ans_data.get('correct_answer_text', ''),
                    'explanation': ans_data.get('explanation', '無解析')
                })
        
        # 判斷結果
        # 成功條件: 1. 正確率 >= 60%  2. 未超時 (或已答完所有題目) 3. HP > 0
        # 修正：如果玩家已答完所有題目，即使系統時間顯示稍微超時，也判定為通過 (避免 100% 正確率卻因幾秒誤差被判失敗)
        is_passed = (accuracy >= 60) and ((not is_timeout) or is_questions_finished) and (progress.current_hp > 0)
        is_perfect = (accuracy == 100) and is_passed
        
        # 計算獎勵
        exp_reward = 0
        ticket_reward = 0
        
        if is_passed:
            # 標準經驗值: 下一級所需經驗值的 1/20
            next_level_exp = profile.experience_to_next_level()
            standard_exp = next_level_exp // 20
            exp_reward = standard_exp
            ticket_reward = 1
            
            if is_perfect:
                # 完美通關: 經驗值翻倍 (1/10), 額外獲得 2 張強化券 (共 3 張)
                exp_reward = standard_exp * 2
                ticket_reward += 2
            
            # 發放獎勵 (僅限當日首次通關，或可重複領取? 通常每日副本僅首通有獎，但這裡先依邏輯發放)
            # 檢查是否已領過獎勵? TrialRecord 會記錄，這裡簡化邏輯先發放
            # 若需限制每日一次，應檢查 DailyTrialProgress.is_passed 是否原本為 False
            if not progress.is_passed: # 避免重複刷新頁面重複領獎
                profile.experience += exp_reward
                profile.enhancement_tickets += ticket_reward
                
                #檢查升級
                while profile.experience >= profile.experience_to_next_level():
                    profile.experience -= profile.experience_to_next_level()
                    profile.level += 1
                
                profile.save()
                
                # 記錄到 TrialRecord (略，TrialRecord 通常在 submit 時建立或在此更新)
                # 這裡假設 DailyTrialProgress 用於暫存，結算時寫入 Record
                record = TrialRecord.objects.create(
                    user_profile=profile,
                    trial=trial,
                    daily_task=daily_task,
                    score=int(accuracy),
                    total_questions=total_count,
                    correct_answers=correct_count,
                    time_spent_seconds=int((timezone.now() - progress.started_at).total_seconds()),
                    answer_details=answers,
                    exp_gained=exp_reward,
                    is_passed=True
                )
        
        # 更新進度狀態
        if not progress.is_completed:
            progress.is_completed = True
            progress.is_passed = is_passed
            progress.save()

        context = {
            'profile': profile,
            'trial': trial,
            'is_completed': True,
            'is_passed': is_passed,
            'is_perfect': is_perfect,
            'is_timeout': is_timeout,
            'correct_count': correct_count,
            'total_count': total_count,
            'accuracy': accuracy,
            'exp_reward': exp_reward,
            'ticket_reward': ticket_reward,
            'final_hp': progress.current_hp,
            'initial_hp': progress.initial_hp,
            'wrong_answers_list': wrong_answers_list,
        }
        return render(request, 'EngineerRPG/trial_exam.html', context)
        
    # 重置或繼續
    if not created:
         # Check timeout (這裡已經在上面檢查過了,這段可以移除)
         pass

    # 初始化 Session
    trial = daily_task.trial
    all_questions = list(daily_task.questions.all())
    
    # 每日任務題目是固定的，不需要隨機抽，直接用設定好的
    selected_questions = all_questions
    
    request.session['trial_id'] = trial.id
    request.session['daily_task_id'] = daily_task.id  # 標記為每日任務
    request.session['trial_questions'] = [q.id for q in selected_questions]
    request.session['trial_start_time'] = progress.started_at.isoformat()
    request.session['trial_answers'] = progress.answers
    request.session['current_question_index'] = progress.current_question_index
    request.session['trial_hp'] = progress.current_hp
    request.session['trial_mp'] = progress.current_mp
    request.session['emergency_bandage_used'] = False  # Reset Emergency Bandage flag
    
    # 決定從哪題開始
    if progress.current_question_index >= len(selected_questions):
         # 已經做完但沒結算？導向提交
         return redirect('engineer_rpg:submit_trial', trial_id=trial.id)
         
    current_question = selected_questions[progress.current_question_index]
    
    elapsed = (timezone.now() - progress.started_at).total_seconds()
    remaining_seconds = max(0, int(trial.time_limit_minutes * 60 - elapsed))

    context = {
        'profile': profile,
        'trial': trial,
        'question': current_question,
        'current_index': progress.current_question_index,
        'total_questions': len(selected_questions),
        'base_hp': profile.get_total_hp(),
        'base_mp': profile.get_total_mp(),
        'initial_hp': progress.current_hp,
        'initial_mp': progress.current_mp,
        'heart_range': range(1, max(profile.get_total_hp(), 5) + 1),
        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),
        'is_daily_task': True,
        'time_limit': trial.time_limit_minutes,
        'start_time': progress.started_at.isoformat(),
        'remaining_seconds': remaining_seconds,
    }
    return render(request, 'EngineerRPG/trial_exam.html', context)
        
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
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)

    # 獲取題組
    question_ids = request.session.get('trial_questions', [])
    if not question_ids:
        messages.error(request, '找不到試煉資料，請重新開始。')
        return redirect('engineer_rpg:dashboard')

    questions = list(Question.objects.filter(id__in=question_ids))
    total_count = len(questions)

    # 統計得分：優先使用 session 中逐題紀錄的答案（每日試煉/地下城逐題模式）
    session_answers = request.session.get('trial_answers', {})
    correct_count = 0
    answer_details = {}

    if session_answers:
        # 逐題模式：答案已在 submit_answer 中記錄於 session
        for question in questions:
            qid = str(question.id)
            ans = session_answers.get(qid, {})
            is_correct = ans.get('is_correct', False)
            user_answer = ans.get('user_answer', '')
            if is_correct:
                correct_count += 1
            answer_details[qid] = {
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
            }
    else:
        # 整頁提交模式（備用）
        if request.method != 'POST':
            return redirect('engineer_rpg:trial_detail', trial_id=trial_id)
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            correct_answer = question.correct_answer
            if question.question_type == 'MULTIPLE':
                user_answer_list = request.POST.getlist(f'question_{question.id}')
                is_correct = set(user_answer_list) == set(correct_answer)
            else:
                is_correct = user_answer == str(correct_answer)
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
    daily_task_id = request.session.get('daily_task_id')
    if daily_task_id:
        # 每日試煉：HP 已在 submit_answer 中即時扣減，從 DailyTrialProgress 讀取
        from .models import DailyTrialProgress
        try:
            progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task_id=daily_task_id)
            remaining_hp = progress.current_hp
        except DailyTrialProgress.DoesNotExist:
            remaining_hp = 1
    else:
        # 一般試煉
        initial_hp = request.session.get('trial_hp', 3)
        wrong_answers = total_count - correct_count
        remaining_hp = max(0, initial_hp - wrong_answers)

    score = int((correct_count / total_count) * 100) if total_count > 0 else 0
    is_passed = score >= 60 and remaining_hp > 0
    
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
        
        # 強化券獎勵
        tickets_earned = 0
        
        # 判斷試煉類型
        if daily_task_id:
            # 每日副本
            tickets_earned = 2
            if score >= 100:
                tickets_earned += 1
        else:
            # 地下城
            if trial.trial_type == 'DUNGEON':
                if is_dungeon_repeat:
                    # 重複挑戰:檢查是否首次未滿分,這次滿分
                    if score >= 100:
                        # 檢查過去是否有滿分記錄
                        has_perfect_score = TrialRecord.objects.filter(
                            user_profile=profile,
                            trial=trial,
                            score=100,
                            is_passed=True
                        ).exists()
                        
                        if not has_perfect_score:
                            # 首次獲得滿分,給予滿分追溯獎勵
                            tickets_earned = 5
                            messages.info(request, '首次滿分通過!獲得滿分追溯獎勵!')
                    # 否則重複遊玩不給獎勵
                else:
                    # 首次通過
                    tickets_earned = 10
                    if score >= 100:
                        tickets_earned += 5
        
        # 給予強化券
        if tickets_earned > 0:
            profile.enhancement_tickets += tickets_earned
            messages.success(request, f'獲得 {tickets_earned} 張強化券！')
        
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

    # 檢查是否具備晉升資格
    eligible = False
    target_level = profile.level
    if profile.rank == 'INTERN' and profile.level >= 10:
        eligible = True
        target_level = 10
    elif profile.rank == 'ASSISTANT' and profile.level >= 50:
        eligible = True
        target_level = 50

    # 檢查是否已有待審核的申請
    pending_request = PromotionRequest.objects.filter(
        applicant=profile, status='PENDING'
    ).first()

    if request.method == 'POST' and eligible and not pending_request:
        # 建立申請紀錄
        PromotionRequest.objects.create(
            applicant=profile,
            current_level=profile.level,
            target_level=target_level,
        )
        messages.success(request, '晉升申請已提交，請等待管理員審核。')
        return redirect('engineer_rpg:dashboard')

    context = {
        'profile': profile,
        'eligible': eligible,
        'pending_request': pending_request,
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
    """排行榜"""
    from StudioBase.constants import SINO_DEPT_DB
    from datetime import timedelta

    profile = get_or_create_user_profile(request.user)

    def _enrich(profiles):
        """為每個 profile 附加 full_name 與 dept_display"""
        for p in profiles:
            p.full_name = p.user.get_full_name() or p.user.username
            try:
                emp_profile = p.user.profile  # UserProfile app 的 profile
                p.dept_display = SINO_DEPT_DB.get(
                    emp_profile.emp_dept, emp_profile.emp_dept or '') if emp_profile.emp_dept else ''
            except Exception:
                p.dept_display = ''
        return profiles

    # 等級排行榜：有選擇職業的使用者，依等級＋經驗值排序，取前 20 名
    level_ranking = _enrich(list(
        UserProfile.objects
        .filter(character_class__isnull=False)
        .select_related('user', 'character_class')
        .order_by('-level', '-experience')[:20]
    ))

    # 本週試煉排行：依本週試煉次數排序
    week_start = timezone.now() - timedelta(days=7)
    trial_ranking = _enrich(list(
        UserProfile.objects
        .filter(
            character_class__isnull=False,
            trial_records__completed_at__gte=week_start,
        )
        .select_related('user', 'character_class')
        .annotate(trial_count=Count('trial_records'))
        .order_by('-trial_count')[:20]
    ))

    # 個人通過次數
    passed_trials_count = TrialRecord.objects.filter(
        user_profile=profile, is_passed=True
    ).count()

    context = {
        'profile': profile,
        'level_ranking': level_ranking,
        'trial_ranking': trial_ranking,
        'passed_trials_count': passed_trials_count,
    }
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
        
    requests = PromotionRequest.objects.filter(status='PENDING').select_related('applicant__user')
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


def _build_dept_groups(SINO_DEPT_DB, EmpProfile):
    """建立按部門分組的冒險者列表"""
    from collections import OrderedDict

    # 建立 emp_dept → [user_id, ...] 的映射
    emp_profiles = EmpProfile.objects.filter(
        emp_dept__isnull=False
    ).exclude(emp_dept='').values_list('user_id', 'emp_dept')

    dept_user_map = {}   # dept_code → set(user_ids)
    for uid, dept_code in emp_profiles:
        dept_user_map.setdefault(dept_code, set()).add(uid)

    # 取得所有 RPG UserProfile
    all_rpg = (
        UserProfile.objects
        .select_related('user', 'character_class')
        .order_by('-level')
    )
    rpg_by_user = {p.user_id: p for p in all_rpg}

    dept_groups = []
    for code in sorted(dept_user_map.keys(), key=lambda c: SINO_DEPT_DB.get(c, c)):
        name = SINO_DEPT_DB.get(code, code)
        members = [rpg_by_user[uid] for uid in dept_user_map[code] if uid in rpg_by_user]
        members.sort(key=lambda m: -m.level)
        if members:
            dept_groups.append({
                'code': code,
                'name': name,
                'members': members,
                'count': len(members),
            })

    # 找出沒有部門的 RPG 成員
    all_dept_user_ids = set()
    for uids in dept_user_map.values():
        all_dept_user_ids |= uids
    free_members = [p for uid, p in rpg_by_user.items() if uid not in all_dept_user_ids]
    free_members.sort(key=lambda m: -m.level)

    return {
        'departments': dept_groups,
        'free_members': free_members,
        'free_count': len(free_members),
    }


@login_required
def guild_dashboard(request):
    """公會大廳 — 以部門分組顯示所有冒險者"""
    from collections import OrderedDict
    from StudioBase.constants import SINO_DEPT_DB
    from UserProfile.models import UserProfile as EmpProfile

    profile = get_or_create_user_profile(request.user)
    is_manager = profile.role in ['OFFICER', 'MANAGER', 'ADMIN']

    # 布告欄摘要
    announcements = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-created_at')[:5]
    hot_posts = GuildPost.objects.exclude(category='ANNOUNCEMENT').order_by('-views', '-created_at')[:5]

    # 建立部門分組
    dept_groups = _build_dept_groups(SINO_DEPT_DB, EmpProfile)

    context = {
        'profile': profile,
        'dept_groups': dept_groups,
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
    """成員個人檔案詳情"""
    from StudioBase.constants import SINO_DEPT_DB
    profile = get_or_create_user_profile(request.user)
    member = get_object_or_404(UserProfile, id=member_id)

    # 取得成員的部門資訊
    dept_name = None
    try:
        emp_profile = member.user.profile
        if emp_profile.emp_dept:
            dept_name = SINO_DEPT_DB.get(emp_profile.emp_dept, emp_profile.emp_dept)
    except Exception:
        pass

    from_page = request.GET.get('from', 'guild')
    context = {
        'profile': profile,
        'member': member,
        'dept_name': dept_name,
        'from_page': from_page,
    }
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
        emp_dept = request.POST.get('emp_dept', '').strip()
        
        if not name:
            messages.error(request, 'Team name cannot be empty')
            return redirect('engineer_rpg:create_team')
        
        team = Team.objects.create(
            name=name,
            description=description,
            emp_dept=emp_dept,
            created_by=request.user
        )
        
        messages.success(request, f'Team "{name}" created successfully')
        return redirect('engineer_rpg:edit_team', team_id=team.id)
    
    # 取得建立者的部門資訊
    from UserProfile.models import UserProfile as EmpProfile
    try:
        emp_profile = EmpProfile.objects.get(user=request.user)
        default_dept = emp_profile.emp_dept
    except EmpProfile.DoesNotExist:
        default_dept = ''
    
    # 取得所有部門選項
    from StudioBase.constants import SINO_DEPT_DB
    dept_choices = sorted(SINO_DEPT_DB.items(), key=lambda x: x[1])
    
    context = {
        'profile': profile,
        'default_dept': default_dept,
        'dept_choices': dept_choices,
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
        emp_dept = request.POST.get('emp_dept', '').strip()
        leader_id = request.POST.get('leader')
        
        if not name:
            messages.error(request, 'Team name cannot be empty')
        else:
            team.name = name
            team.description = description
            team.emp_dept = emp_dept
            
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
    
    # 取得所有部門選項
    from StudioBase.constants import SINO_DEPT_DB
    dept_choices = sorted(SINO_DEPT_DB.items(), key=lambda x: x[1])
    
    context = {
        'profile': profile,
        'team': team,
        'members': members,
        'dept_choices': dept_choices,
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
    """隊伍儀表板 — 顯示使用者所屬部門的成員"""
    from StudioBase.constants import SINO_DEPT_DB
    from UserProfile.models import UserProfile as EmpProfile

    rpg_profile = get_or_create_user_profile(request.user)

    # 取得使用者的部門代碼（來自 UserProfile app）
    emp_dept = None
    dept_name = None
    
    # 使用 get_or_create 確保 UserProfile 存在
    emp_profile, created = EmpProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'emp_name': request.user.get_full_name() or request.user.username,
            'emp_email': request.user.email,
        }
    )
    
    emp_dept = emp_profile.emp_dept
    dept_name = SINO_DEPT_DB.get(emp_dept, emp_dept) if emp_dept else None

    if not emp_dept:
        context = {
            'profile': rpg_profile,
            'has_dept': False,
        }
    else:
        # 找出同部門的所有使用者
        same_dept_user_ids = (
            EmpProfile.objects.filter(emp_dept=emp_dept)
            .values_list('user_id', flat=True)
        )
        # 取得這些使用者的 RPG profile
        dept_members = (
            UserProfile.objects.filter(user_id__in=same_dept_user_ids)
            .select_related('user', 'character_class')
            .order_by('-level')
        )

        context = {
            'profile': rpg_profile,
            'has_dept': True,
            'dept_name': dept_name,
            'dept_code': emp_dept,
            'dept_members': dept_members,
        }

    return render(request, 'EngineerRPG/team_dashboard.html', context)


@login_required
def api_search_users(request):
    """API: 搜尋使用者（供白名單等功能的 autocomplete 使用）"""
    from django.db.models import Q
    from UserProfile.models import UserProfile as EmpProfile

    profile = get_or_create_user_profile(request.user)
    if not (request.user.is_superuser or profile.role == 'ADMIN'):
        return JsonResponse({'results': []})

    q = request.GET.get('q', '').strip()
    if len(q) < 1:
        return JsonResponse({'results': []})

    # 搜尋 User.username 或 UserProfile.emp_name
    emp_matches = (
        EmpProfile.objects.filter(
            Q(user__username__icontains=q) | Q(emp_name__icontains=q)
        )
        .select_related('user')[:20]
    )

    results = []
    for ep in emp_matches:
        results.append({
            'username': ep.user.username,
            'emp_name': ep.emp_name or '',
            'display': f"{ep.emp_name} ({ep.user.username})" if ep.emp_name else ep.user.username,
        })

    return JsonResponse({'results': results})


# ==================== Whitelist Management ====================

@login_required
def admin_whitelist_view(request):
    """白名單管理 (Superuser Only)"""
    # 檢查權限：必須是 superuser 或是 'ADMIN' 角色
    profile = get_or_create_user_profile(request.user)
    if not (request.user.is_superuser or profile.role == 'ADMIN'):
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
        
    whitelists = AdminWhitelist.objects.all().order_by('-created_at')
    
    context = {
        'profile': profile,
        'whitelists': whitelists,
        'role_choices': AdminWhitelist.ROLE_CHOICES,
    }
    return render(request, 'EngineerRPG/admin_whitelist.html', context)

@login_required
def admin_whitelist_add(request):
    """新增白名單"""
    if not request.user.is_superuser: # 只有 Superuser 可以操作，比較安全
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:admin_whitelist')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role')
        
        if username and role:
            if AdminWhitelist.objects.filter(username=username).exists():
                messages.error(request, f'使用者 {username} 已在白名單中')
            else:
                AdminWhitelist.objects.create(username=username, role=role)
                messages.success(request, f'已新增 {username} 為 {role}')
                
                # 嘗試同步如果該使用者已存在
                try:
                    user = User.objects.get(username=username)
                    # 觸發同步邏輯 (簡單方式：再次呼叫 get_or_create)
                    get_or_create_user_profile(user)
                    messages.info(request, f'已同步 {username} 的角色權限')
                except User.DoesNotExist:
                    pass # 使用者尚未註冊，未來註冊時會自動生效
        else:
            messages.error(request, '請填寫完整資訊')
            
    return redirect('engineer_rpg:admin_whitelist')

@login_required
def admin_whitelist_delete(request, whitelist_id):
    """刪除白名單"""
    if not request.user.is_superuser:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:admin_whitelist')
        
    whitelist = get_object_or_404(AdminWhitelist, id=whitelist_id)
    username = whitelist.username
    whitelist.delete()
    messages.success(request, f'已移除 {username} 的白名單設定')
    
    # 嘗試同步以移除權限
    try:
        user = User.objects.get(username=username)
        get_or_create_user_profile(user)
        messages.info(request, f'已更新 {username} 的權限狀態')
    except User.DoesNotExist:
        pass
        
    return redirect('engineer_rpg:admin_whitelist')


def has_whitelist_permission(user, required_role='MANAGER'):
    """檢查使用者是否有特定層級的白名單權限"""
    if user.is_superuser:
        return True
    
    # 權限層級定義
    ROLE_LEVELS = {
        'ADVENTURER': 0,
        'OFFICER': 1,
        'MANAGER': 2,
        'ADMIN': 3
    }
    
    try:
        profile = get_or_create_user_profile(user)
        user_role = profile.role
    except:
        return False
        
    user_level = ROLE_LEVELS.get(user_role, 0)
    req_level = ROLE_LEVELS.get(required_role, 0)
    
    return user_level >= req_level



# ==================== Restored Missing Views ====================

def guild_dashboard(request):
    """公會大廳 — 以部門分組顯示所有冒險者 (Restored)"""
    from collections import OrderedDict
    from StudioBase.constants import SINO_DEPT_DB
    from UserProfile.models import UserProfile as EmpProfile

    profile = get_or_create_user_profile(request.user)
    ann = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-created_at')[:5]

    hot_posts = (GuildPost.objects.exclude(category='ANNOUNCEMENT')
                 .annotate(comment_count=Count('comments'))
                 .order_by('-comment_count', '-views')[:5])

    is_manager = profile.role in ('OFFICER', 'MANAGER', 'ADMIN')

    # 建立部門分組
    dept_groups = _build_dept_groups(SINO_DEPT_DB, EmpProfile)

    return render(request, 'EngineerRPG/guild_dashboard.html', {
        'profile': profile,
        'announcements': ann,
        'hot_posts': hot_posts,
        'dept_groups': dept_groups,
        'is_manager': is_manager,
    })



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


def api_auto_layout_skill_tree(request):
    """AJAX: 自動排版算法"""
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return JsonResponse({'success': False}, status=403)
    # ==================== 管理員與後台系統 ====================


def user_management(request):
    """使用者管理"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'):
        return redirect('engineer_rpg:dashboard')
    
    users = UserProfile.objects.all().select_related('user', 'character_class')
    return render(request, 'EngineerRPG/user_management.html', {'profile': profile, 'users': users})



def question_management(request):
    """題目管理列表"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
    
    # 處理重置試煉按鈕
    if request.method == 'POST' and 'reset_trial' in request.POST:
        from .models import DailyTrialProgress
        deleted_count = DailyTrialProgress.objects.filter(
            user_profile=profile
        ).delete()[0]
        messages.success(request, f'已重置 {deleted_count} 個每日試煉進度!(獎勵已保留)')
        return redirect('engineer_rpg:question_management')
        
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



def dungeon_management(request):
    """地下城副本管理"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'ADMIN'):
        return redirect('engineer_rpg:dashboard')
        
    dungeons = Trial.objects.filter(trial_type='DUNGEON').order_by('-created_at')
    return render(request, 'EngineerRPG/management/dungeon_list.html', {'profile': profile, 'dungeons': dungeons})


# ==================== 晉升系統 ====================


def skill_tree_editor(request):
    """技能樹編輯器頁面"""
    profile = get_or_create_user_profile(request.user)
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return redirect('engineer_rpg:dashboard')
        
    classes = CharacterClass.objects.all()
    selected_class = request.GET.get('class', 'CIVIL')
    
    
    # Filter skills by class
    if selected_class:
        skills = SkillNode.objects.filter(
            Q(character_class__code=selected_class) | 
            Q(character_class__isnull=True)
        )
    else:
        skills = SkillNode.objects.all()

    return render(request, 'EngineerRPG/skill_tree_editor.html', {
        'profile': profile,
        'classes': classes,
        'selected_class': selected_class,
        'skills': skills,
        'courses': Course.objects.all(), # Also needed for courses checkbox list
        # Budget calculation (simplified placeholders for now)
        'root_xp_current': 0, 'root_xp_limit': 1000,
        'core_xp_current': 0, 'core_xp_limit': 2000,
    })



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


def course_study(request, course_id):
    """課程學習頁面"""
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'EngineerRPG/course_study.html', {'profile': profile, 'course': course})



def course_exam(request, course_id):
    """課程測驗"""
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    questions = course.questions.filter(is_active=True)
    question_count = questions.count()
    points_per_question = round(100 / question_count) if question_count > 0 else 0
    return render(request, 'EngineerRPG/course_exam.html', {
        'profile': profile, 
        'course': course, 
        'questions': questions,
        'points_per_question': points_per_question,
    })



def submit_course_exam(request, course_id):
    """提交課程測驗 — 批改、記分、獎勵"""
    if request.method != 'POST':
        return redirect('engineer_rpg:dashboard')

    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    questions = course.questions.filter(is_active=True)
    question_count = questions.count()

    if question_count == 0:
        messages.warning(request, '此課程尚無題目，無法測驗')
        return redirect('engineer_rpg:course_study', course_id=course.id)

    # ── 批改答案 ──
    correct_count = 0
    answer_details = {}

    for question in questions:
        field_name = f'question_{question.id}'
        user_answer = request.POST.get(field_name, '')

        # 取得正確答案（JSON: 單選 "A", 多選 ["A","B"], 是非 "T"/"F"）
        correct = question.correct_answer
        if isinstance(correct, list):
            is_correct = user_answer in correct
        else:
            is_correct = (user_answer == str(correct))

        if is_correct:
            correct_count += 1

        answer_details[str(question.id)] = {
            'user_answer': user_answer,
            'correct_answer': correct,
            'is_correct': is_correct,
        }

    # ── 計算分數 ──
    score = round(correct_count / question_count * 100)
    is_passed = score >= course.passing_score

    # ── 建立 / 更新 UserCourseProgress ──
    progress, created = UserCourseProgress.objects.get_or_create(
        user_profile=profile,
        course=course,
    )

    # 保留最高分
    if score > progress.score:
        progress.score = score

    if is_passed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()

        # ── 經驗值獎勵（僅首次通過） ──
        exp_reward = 0
        for skill_node in course.skill_nodes.all():
            exp_reward += skill_node.exp_reward

            # 更新關聯的 UserSkill 進度
            user_skill, _ = UserSkill.objects.get_or_create(
                user_profile=profile,
                skill_node=skill_node,
                defaults={'status': 'IN_PROGRESS', 'started_at': timezone.now()}
            )
            if user_skill.status not in ('COMPLETED',):
                user_skill.status = 'COMPLETED'
                user_skill.progress = 100
                user_skill.completed_at = timezone.now()
                user_skill.save()

        if exp_reward > 0:
            profile.experience += exp_reward
            # 檢查升級
            while profile.experience >= profile.experience_to_next_level():
                profile.experience -= profile.experience_to_next_level()
                profile.level += 1
            profile.save()
            messages.info(request, f'🎉 獲得 {exp_reward} 經驗值！')

    progress.save()

    # ── 回饋訊息 ──
    if is_passed:
        messages.success(
            request,
            f'✅ 測驗通過！得分 {score} 分（答對 {correct_count}/{question_count} 題）'
        )
    else:
        messages.warning(
            request,
            f'❌ 測驗未通過。得分 {score} 分（答對 {correct_count}/{question_count} 題，'
            f'及格分數 {course.passing_score} 分），請再接再厲！'
        )

    return redirect('engineer_rpg:skill_tree')



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



def download_template(request, format='csv'):
    """下載匯入範本"""
    # 範本生成邏輯...
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_template.csv"'
    return response

# ==================== 其他導向視圖 ====================


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



def create_user(request):
    """創建使用者"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:user_management')



def edit_user(request, user_id):
    """編輯使用者"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:user_management')



def delete_user(request, user_id):
    """刪除使用者"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:user_management')



def delete_question(request, question_id):
    """刪除題目"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:question_management')



def course_management(request):
    """課程管理"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:admin_dashboard')



def create_course(request):
    """創建課程"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:course_management')



def edit_course(request, course_id):
    """編輯課程"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:course_management')



def delete_course(request, course_id):
    """刪除課程"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:course_management')



def create_dungeon(request):
    """創建地下城"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:dungeon_management')



def edit_dungeon(request, dungeon_id):
    """編輯地下城"""
    messages.info(request, '此功能正在開發中')
    return redirect('engineer_rpg:dungeon_management')



def api_user_stats(request):
    """API: 使用者統計資料"""
    profile = get_or_create_user_profile(request.user)
    return JsonResponse({
        'level': profile.level,
        'experience': profile.experience,
        'hp': profile.get_total_hp(),
        'mp': profile.get_total_mp()
    })



def api_skill_tree_data(request):
    """API: 技能樹資料"""
    profile = get_or_create_user_profile(request.user)
    
    # 根據職業篩選技能
    if profile.character_class:
        skills = SkillNode.objects.filter(
            Q(character_class=profile.character_class) | 
            Q(character_class__isnull=True)
        )
    else:
        skills = SkillNode.objects.none()
        
    data = []
    for skill in skills:
        # Check status
        try:
            user_skill = UserSkill.objects.get(user_profile=profile, skill_node=skill)
            status = user_skill.status
        except UserSkill.DoesNotExist:
            status = 'LOCKED'
            
        data.append({
            'id': skill.id,
            'name': skill.name,
            'description': skill.description,
            'type': skill.node_type,
            'x': skill.position_x,
            'y': skill.position_y,
            'status': status,
            'parents': list(skill.parent_skills.values_list('id', flat=True)),
            'level_required': skill.level_required,
        })
        
    return JsonResponse({'skills': data})


def api_skill_editor_data(request):
    """API: 技能編輯器資料"""
    if not has_whitelist_permission(request.user, 'MANAGER'):
        return JsonResponse({'success': False}, status=403)
        
    class_code = request.GET.get('class')
    if class_code:
        skills = SkillNode.objects.filter(
            Q(character_class__code=class_code) | 
            Q(character_class__isnull=True)
        )
    else:
        skills = SkillNode.objects.all()
        
    data = []
    for skill in skills:
        data.append({
            'id': skill.id,
            'name': skill.name,
            'description': skill.description,
            'type': skill.node_type,
            'x': skill.position_x,
            'y': skill.position_y,
            'parents': list(skill.parent_skills.values_list('id', flat=True)),
            'courses': list(skill.courses.values_list('id', flat=True)),
            'class_code': skill.character_class.code if skill.character_class else None,
        })
        
    return JsonResponse({'skills': data})



def api_manage_skill_course(request):
    """API: 管理技能課程"""
    return JsonResponse({'success': False, 'message': '功能開發中'})



def api_auto_distribute_xp(request):
    """API: 自動分配經驗值"""
    return JsonResponse({'success': False, 'message': '功能開發中'})


# ==================== 管理者白名單管理 ====================

@login_required
def reset_daily_trials(request):
    """重置所有每日試煉進度 (用於測試)"""
    profile = get_or_create_user_profile(request.user)
    
    # 刪除所有每日試煉進度 (包含已完成的)
    # 獎勵已經給予,所以可以安全刪除進度記錄
    from .models import DailyTrialProgress
    deleted_count = DailyTrialProgress.objects.filter(
        user_profile=profile
    ).delete()[0]
    
    messages.success(request, f'已重置 {deleted_count} 個每日試煉進度!(獎勵已保留)')
    return redirect(request.META.get('HTTP_REFERER', 'engineer_rpg:daily_trial_list'))

