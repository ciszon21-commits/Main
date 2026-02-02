from django.db.models import Sum
# -*- coding: utf-8 -*-
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



    Team, TeamMembership, GuildPost, GuildComment, UserCourseProgress



)















from .forms import (



    QuestionForm, QuestionImportForm, SkillNodeForm, CourseForm, UserLoginForm,



    UserRegistrationForm, UserProfileEditForm



)

# Import team management functions
from .views_team_management import edit_team, manage_team_members, create_team







# ==================== 頛����?賢? ====================







def get_or_create_user_profile(user):



    """Get or create user profile"""


    try:



        return user.rpg_profile



    except UserProfile.DoesNotExist:



        # 憒��?瘝��?瑼��?嚗��??�閮剖���???



        return None











def check_skill_unlocked(user_profile, skill_node):



    """Check if skill is unlocked"""


    # 瑼Ｘ�亦���??����



    if user_profile.level < skill_node.min_level:



        return False







    # Comment

    parent_skills = skill_node.parent_skills.all()



    if parent_skills.exists():



        completed_parents = UserSkill.objects.filter(



            user_profile=user_profile,



            skill_node__in=parent_skills,



            status='COMPLETED'



        ).count()



        return completed_parents == parent_skills.count()



    return True  # 瘝��??�蝵�?�?踝??湔�亥�??























# ==================== 閮餃??����??====================







def user_register(request):



    """User Registration"""



    if request.user.is_authenticated:



        return redirect('engineer_rpg:dashboard')



    



    if request.method == 'POST':



        form = UserRegistrationForm(request.POST)



        if form.is_valid():



            user = form.save()



            # ?��?隤��?敺�蝡�



            # ?��?隤��?敺�蝡� - ?�蝣�?��? ModelBackend 隞仿��?��??��?蝡航?蝒?



            user.backend = 'django.contrib.auth.backends.ModelBackend'



            login(request, user)



            messages.success(request, 'Operation successful')




            return redirect('engineer_rpg:dashboard')



    else:



        form = UserRegistrationForm()



    



    # Calculate XP Budgets
    root_xp_current = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    core_xp_current = SkillNode.objects.filter(node_type='CORE', character_class__code=selected_class_code).aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    
    context = {
        'profile': profile,
        'skills': skills,
        'courses': courses,
        'classes': classes,
        'selected_class': selected_class_code,
        # Budget Info
        'root_xp_current': root_xp_current,
        'root_xp_limit': 4500,
        'core_xp_current': core_xp_current,
        'core_xp_limit': 118000,
    }



    



    return render(request, 'EngineerRPG/register.html', context)











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



                messages.success(request, f'Welcome, {user.username}!')



                return redirect('engineer_rpg:dashboard')



            else:



                messages.error(request, 'Username or email already exists')



    else:



        form = UserLoginForm()



    



    context = {



        'form': form,



    }



    



    return render(request, 'EngineerRPG/login.html', context)











def user_logout(request):



    """User Logout"""



    logout(request)



    messages.success(request, 'Operation successful')




    return redirect('engineer_rpg:index')











# ==================== 擐��??��?銵冽�� ====================







def index(request):



    """Function docstring"""


    return render(request, 'EngineerRPG/index.html')











@login_required



def dashboard(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:setup_profile')



    



    # Get user profile



    total_skills = UserSkill.objects.filter(user_profile=profile).count()



    completed_skills = UserSkill.objects.filter(user_profile=profile, status='COMPLETED').count()



    



    # Comment

    recent_trials = TrialRecord.objects.filter(user_profile=profile).order_by('-completed_at')[:5]



    



    # 瘥����?舀��



    today = timezone.now().date()
    
    # Use DailyTrialTask to get today's generated dungeons
    from .models import DailyTrialTask
    from .utils import generate_daily_tasks
    
    daily_tasks_query = DailyTrialTask.objects.filter(date=today).order_by('task_number')
    if not daily_tasks_query.exists():
        daily_tasks_query = generate_daily_tasks(date=today)
        
    # Extract trials from tasks to maintain template compatibility
    daily_trials = [task.trial for task in daily_tasks_query]



    



    # Comment

    exp_to_next = profile.experience_to_next_level()



    exp_progress = (profile.experience / exp_to_next * 100) if exp_to_next > 0 else 0



    



    # Comment

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



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:setup_profile')







    if request.method == 'POST':



        form = UserProfileEditForm(request.POST, request.FILES)



        if form.is_valid():



            # Update User



            user = request.user



            user.username = form.cleaned_data['username']



            if form.cleaned_data['email']:



                user.email = form.cleaned_data['email']



            



            # Handle password change



            new_password = form.cleaned_data.get('new_password')



            old_password = form.cleaned_data.get('old_password')



            



            if new_password:



                # 撽��??��?蝣?



                if not user.check_password(old_password):



                    form.add_error('old_password', '?��?蝣潔?甇?Ⅱ')



                else:



                    user.set_password(new_password)



                    user.save()



                    from django.contrib.auth import update_session_auth_hash



                    update_session_auth_hash(request, user)  # Keep user logged in



            else:



                user.save()







            if not form.errors:



                # Update Profile



                profile.employee_id = form.cleaned_data['employee_id']



                



                # Handle Avatar



                # 憒��??��????豢??�閮�?剖?"嚗�avatar_index ??> 0



                avatar_index = form.cleaned_data.get('avatar_index')



                if avatar_index and int(avatar_index) > 0:



                    profile.avatar_index = int(avatar_index)



                    # Comment

                    # ?�鋆�?豢?撠?avatar_image 閮剔�� None嚗�隞乩�?get_avatar_url ?芸?雿輻�� index



                    profile.avatar_image = None 



                    



                # 憒��??��??單��?��?嚗��?閬��? (?芸?蝝��?擃?



                if form.cleaned_data.get('avatar_image'):



                    profile.avatar_image = form.cleaned_data['avatar_image']



                    profile.avatar_index = 0 # ?�蝵桃揣�?



                



                profile.save()







                messages.success(request, 'Profile updated successfully')



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
        'avatar_data': [
            (1, '人類戰士'), (2, '人類法師'), (3, '人類盜賊'), (4, '人類牧師'),
            (5, '矮人戰士'), (6, '矮人工匠'), (7, '矮人礦工'), (8, '矮人酒保'),
            (9, '精靈弓手'), (10, '精靈德魯伊'), (11, '精靈吟遊詩人'), (12, '精靈舞者'),
            (13, '獸人戰士'), (14, '獸人薩滿'), (15, '獸人獵人'), (16, '獸人鐵匠'),
            (17, '魔族術士'), (18, '魔族刺客'), (19, '魔族死靈法師'), (20, '魔族血騎士'),
        ],
        'default_avatars': range(1, 21)
    }



    return render(request, 'EngineerRPG/profile_edit.html', context)











# Comment





@login_required



def skill_tree(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:setup_profile')



    



    # Comment

    skills = SkillNode.objects.filter(



        Q(character_class=profile.character_class) | Q(character_class__isnull=True)



    ).prefetch_related('parent_skills', 'child_skills')



    



    # Comment

    user_skills = UserSkill.objects.filter(user_profile=profile).select_related('skill_node')



    user_skill_dict = {us.skill_node_id: us for us in user_skills}



    



    # Comment

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



    



    # 摨��??���� JSON 靘��?蝡臭蝙??



    skill_tree_json = []



    for item in skill_tree_data:



        skill_tree_json.append({



            'skill': {



                'id': item['skill'].id,



                'name': item['skill'].name,



                'description': item['skill'].description,



                'node_type': item['skill'].node_type,



                'exp_reward': item['skill'].exp_reward,



                'position_x': item['skill'].position_x,



                'position_y': item['skill'].position_y,



                'parent_skills': [p.id for p in item['skill'].parent_skills.all()],



            },



            'user_skill': {



                'progress': item['user_skill'].progress,



                'status': item['user_skill'].status,



            } if item['user_skill'] else None,



            'status': item['status'],



        })



    



    context = {



        'profile': profile,



        'skill_tree_data': skill_tree_data,



        'skill_tree_json': json.dumps(skill_tree_json),



    }



    



    return render(request, 'EngineerRPG/skill_tree.html', context)











@login_required



def skill_detail(request, skill_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    skill = get_object_or_404(SkillNode, id=skill_id)



    



    # Comment

    user_skill, created = UserSkill.objects.get_or_create(



        user_profile=profile,



        skill_node=skill,



        defaults={'status': 'LOCKED'}



    )



    



    # 瑼Ｘ��?臬�西�??



    is_unlocked = check_skill_unlocked(profile, skill)



    if is_unlocked and user_skill.status == 'LOCKED':



        user_skill.status = 'AVAILABLE'



        user_skill.save()



    



    # ?脣??賊?隤脩?



    courses = skill.courses.all()



    



    # Comment

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



    """Function docstring"""


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



        messages.success(request, 'Operation successful')




    



    return redirect('engineer_rpg:skill_detail', skill_id=skill_id)











@login_required



def complete_skill(request, skill_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    skill = get_object_or_404(SkillNode, id=skill_id)



    



    user_skill = get_object_or_404(UserSkill, user_profile=profile, skill_node=skill)



    



    if user_skill.status == 'IN_PROGRESS':



        user_skill.status = 'COMPLETED'



        user_skill.progress = 100



        user_skill.completed_at = timezone.now()



        user_skill.save()



        



        # ?脣?蝬��???



        profile.experience += skill.exp_reward



        



        # 瑼Ｘ��?臬��?��?



        # 瑼Ｘ?臬??
        # Level Cap Logic:
        # Intern -> Cap at 10
        # Assistant -> Cap at 50
        # Engineer -> Cap at 100
        
        while profile.experience >= profile.experience_to_next_level():
            # Check Level Caps
            if profile.rank == 'INTERN' and profile.level >= 10:
                break
            if profile.rank == 'ASSISTANT' and profile.level >= 50:
                break
            if profile.level >= 100:
                break
                
            profile.experience -= profile.experience_to_next_level()
            profile.level += 1
            messages.success(request, f'恭喜升級！等級提升至 {profile.level}！')
            
            # HP/MP growth logic (if any)
            if profile.level % 10 == 0:
                # e.g. bonus
                pass

        # Notification Logic
        if profile.rank == 'ASSISTANT':
             # Check if eligible for Engineer promotion ( > 50% CORE skills)
             req_core = SkillNode.objects.filter(character_class=profile.character_class, node_type='CORE').count()
             done_core = UserSkill.objects.filter(
                 user_profile=profile, 
                 skill_node__character_class=profile.character_class,
                 skill_node__node_type='CORE',
                 status='COMPLETED'
             ).count()
             
             if req_core > 0 and (done_core / req_core) >= 0.5:
                 # Check if recently qualified (e.g. just passed the threshold)
                 # Simpler: just notify every time they complete a skill if they are eligible
                 messages.info(request, '【系統通知】您已完成超過 50% 的職業核心技能，具備晉升「工程師」的資格！請至儀表板申請晉升。')

        profile.save()



        



        messages.success(request, 'Operation successful')




    



    return redirect('engineer_rpg:skill_tree')











# ==================== ?���瑞頂蝯� ====================







@login_required



def use_item(request, user_item_id):



    """Function docstring"""


    if request.method != 'POST':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:item_inventory')



    



    profile = get_or_create_user_profile(request.user)



    user_item = get_object_or_404(UserItem, id=user_item_id, user_profile=profile)



    



    if user_item.quantity < 1:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:item_inventory')



    



    # Comment

    # Comment

    



    messages.info(request, 'Information')




    return redirect('engineer_rpg:item_inventory')











# ==================== 閰衣?蝟餌絞 ====================







@login_required



def training_hub(request):



    """Function docstring"""


    return render(request, 'EngineerRPG/training_hub.html')











@login_required



def daily_trial_list(request):



    """Daily Trial List - Show daily trials"""



    profile = get_or_create_user_profile(request.user)



    



    today = timezone.now().date()



    



    # ?脣?隞����?��??乩遙??



    from .models import DailyTrialTask, DailyTrialProgress



    from .utils import generate_daily_tasks



    



    daily_tasks = DailyTrialTask.objects.filter(date=today, is_active=True).order_by('task_number')



    



    # 憒��?隞���交���?隞餃?嚗����?��???



    if not daily_tasks.exists():



        daily_tasks = generate_daily_tasks(date=today)



    



    # Comment

    task_progress_list = []



    for task in daily_tasks:



        try:



            progress = DailyTrialProgress.objects.get(



                user_profile=profile,



                daily_task=task



            )



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



    



    # 閮��?頝����?瑟��?��???



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



        'today': today,
        'total_completed': sum(1 for item in task_progress_list if item['progress'] and item['progress'].is_completed),
        'total_passed': sum(1 for item in task_progress_list if item['progress'] and item['progress'].is_passed),
        'total_exp_earned': sum(item['task'].trial.exp_reward for item in task_progress_list if item['progress'] and item['progress'].is_passed),
    }



    



    return render(request, 'EngineerRPG/daily_trial.html', context)











@login_required



def trial_detail(request, trial_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # 瑼Ｘ��?臬�衣泵�?璇�隞�



    can_start = profile.level >= trial.required_level



    



    context = {



        'profile': profile,



        'trial': trial,



        'can_start': can_start,



    }



    



    return render(request, 'EngineerRPG/trial_detail.html', context)











@login_required



def start_trial(request, trial_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # ?冽??賢?憿����



    all_questions = list(trial.questions.filter(is_active=True))



    selected_questions = random.sample(all_questions, min(trial.question_count, len(all_questions)))



    



    # ?脣???session



    request.session['trial_id'] = trial.id



    request.session['trial_questions'] = [q.id for q in selected_questions]



    request.session['trial_start_time'] = timezone.now().isoformat()



    request.session['trial_answers'] = {}



    request.session['current_question_index'] = 0  # ?啣?嚗����?��??桃揣撘?



    



    



    # ?��???HP/MP



    # ?箇? HP ?箏???3嚗��??��??���血���?蝞?



    base_hp = profile.get_total_hp()



    total_hp = base_hp



    initial_mp = profile.get_total_mp()



    



    request.session['trial_hp'] = total_hp



    request.session['trial_mp'] = initial_mp



    



    # Comment

    current_question = selected_questions[0] if selected_questions else None



    



    context = {



        'profile': profile,



        'trial': trial,



        'question': current_question,  # ?寧��?桅?



        'current_index': 0,



        'total_questions': len(selected_questions),



        'base_hp': base_hp,  # ?箇? HP (3)



        'initial_hp': total_hp,  # 蝮?HP (?怨??��???



        'initial_mp': initial_mp,



        'heart_range': range(1, max(total_hp, 5) + 1),  # ?��??��??賊?



        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),



    }



    



    return render(request, 'EngineerRPG/trial_exam.html', context)











@login_required



def start_daily_trial(request, task_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    from .models import DailyTrialTask, DailyTrialProgress



    from .utils import get_or_create_daily_progress



    



    # ?脣?瘥���乩遙�?



    daily_task = get_object_or_404(DailyTrialTask, id=task_id)



    



    # 瑼Ｘ��?臬��?箔??乩遙??



    today = timezone.now().date()



    if daily_task.date != today:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:daily_trial_list')



    



    # Comment

    progress = get_or_create_daily_progress(profile, daily_task)



    



    # 憒��?撌脣??��?銝����?����?��?



    if progress.is_completed:



        messages.warning(request, 'Warning')




        return redirect('engineer_rpg:daily_trial_list')



    



    # 憒��? HP 甇賊�塚���??賜匱蝥?



    if progress.current_hp <= 0:



        messages.error(request, 'HP exhausted, trial failed')



        return redirect('engineer_rpg:daily_trial_list')



    



    # ?脣?隞餃??��???



    questions = list(daily_task.questions.all())



    



    # 瑼Ｘ��?臬��?��???



    if not questions:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:daily_trial_list')



    



    # ?脣???session



    # 初始化 Session
    request.session['daily_task_id'] = daily_task.id
    request.session['trial_questions'] = [q.id for q in questions]
    request.session['trial_start_time'] = timezone.now().isoformat()
    
    # 檢查是否已有進度
    if progress.started_at and not progress.is_completed:
        # 恢復進度
        current_index = progress.current_question_index
        request.session['current_question_index'] = current_index
        
        # 如果不是第一題，直接跳轉到 next_question 處理渲染
        if current_index > 0:
            return redirect('engineer_rpg:next_question', trial_id=daily_task.trial.id)
    else:
        # 新的開始
        request.session['current_question_index'] = 0
        current_index = 0

    if not progress.started_at:
        progress.started_at = timezone.now()
        progress.save()

    current_question = questions[current_index] if questions else None



    
    
    # 計算剩餘時間
    if progress.started_at:
        from datetime import timedelta
        elapsed = (timezone.now() - progress.started_at).total_seconds()
        time_limit_seconds = daily_task.trial.time_limit_minutes * 60
        remaining_seconds = max(0, int(time_limit_seconds - elapsed))
    else:
        remaining_seconds = daily_task.trial.time_limit_minutes * 60

    # 獲取裝備賦予的技能
    available_skills = set()
    for slot in [profile.equipped_tool_1, profile.equipped_tool_2, profile.equipped_tool_3, profile.equipped_tool_4, profile.equipped_tool_5]:
        if slot and slot.equipment.skill_effect:
            available_skills.add(slot.equipment.skill_effect)



    context = {



        'profile': profile,



        'trial': daily_task.trial,



        'daily_task': daily_task,



        'question': current_question,



        'current_index': 0,



        'total_questions': len(questions),



        'base_hp': profile.get_total_hp(),



        'initial_hp': progress.current_hp,



        'initial_mp': progress.current_mp,



        'heart_range': range(1, max(progress.initial_hp, 5) + 1),



        'is_daily_task': True,



        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),
        'remaining_seconds': remaining_seconds,
        'available_skills': available_skills,



    }



    



    return render(request, 'EngineerRPG/trial_exam.html', context)











@login_required



def submit_answer(request, trial_id):



    """Submit Answer"""



    if request.method != 'POST':



        return JsonResponse({'error': 'Invalid request method'}, status=400)



    



    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # ?脣??嗅?憿����



    question_ids = request.session.get('trial_questions', [])



    current_index = request.session.get('current_question_index', 0)



    



    if current_index >= len(question_ids):



        return JsonResponse({'error': 'No more questions'}, status=400)



    



    question = get_object_or_404(Question, id=question_ids[current_index])



    



    # Get user answer



    user_answer = request.POST.get('answer', '')



    # 獲取當前 MP（從前端傳來）



    current_mp = int(request.POST.get('current_mp', 100))



    # 初始化 HP 傷害值



    hp_damage = 0



    



    # ?斗�瑕�����



    correct_answer = question.correct_answer



    is_correct = False



    



    if question.question_type == 'MULTIPLE':



        user_answer_list = request.POST.getlist('answer')



        is_correct = set(user_answer_list) == set(correct_answer)



    else:



        is_correct = user_answer == str(correct_answer)



    



    # ?湔�� Session 銝剔?蝑��?閮��?



    trial_answers = request.session.get('trial_answers', {})



    trial_answers[str(question.id)] = {



        'user_answer': user_answer,



        'is_correct': is_correct,



    }



    request.session['trial_answers'] = trial_answers



    



    # 瑼Ｘ��?臬��?箸??乩遙??



    daily_task_id = request.session.get('daily_task_id')



    if daily_task_id:



        # 瘥���乩遙�?嚗����??DailyTrialProgress



        from .models import DailyTrialTask, DailyTrialProgress



        try:



            daily_task = DailyTrialTask.objects.get(id=daily_task_id)



            progress = DailyTrialProgress.objects.get(



                user_profile=profile,



                daily_task=daily_task



            )



            



            # ??�� HP嚗��??��??荔?



            if not is_correct:



                damage = 10
                if question.difficulty == 'C': damage = 5
                elif question.difficulty in ['A', 'S']: damage = 15
                hp_damage = damage
                progress.current_hp = max(0, progress.current_hp - damage)



            



            # 更新 MP（從前端同步）



            progress.current_mp = current_mp



            



            current_hp = progress.current_hp



            



            # ?湔�啁���?閮��?



            # 更新答題記錄
            if not progress.answers:
                progress.answers = {}
            
            progress.answers[str(question.id)] = {
                'user_answer': user_answer,
                'is_correct': is_correct,
            }
            
            # 重要：在答案提交成功後，更新進度索引，這樣下一題 (next_question) 才會渲染新題目
            # 只有當前未結束時才增加
            if progress.current_hp > 0:
                 progress.current_question_index = current_index + 1
                 request.session['current_question_index'] = current_index + 1
            
            progress.save()



            



        except (DailyTrialTask.DoesNotExist, DailyTrialProgress.DoesNotExist):



            # If database fails, use session



            current_hp = request.session.get('trial_hp', 3)



            if not is_correct:



                damage = 10
                if question.difficulty == 'C': damage = 5
                elif question.difficulty in ['A', 'S']: damage = 15
                hp_damage = damage
                current_hp = max(0, current_hp - damage)



                request.session['trial_hp'] = current_hp



            # 更新 MP 到 session



            request.session['trial_mp'] = current_mp



    else:



        # Comment

        current_hp = request.session.get('trial_hp', 3)



        if not is_correct:



            damage = 10
            if question.difficulty == 'C': damage = 5
            elif question.difficulty in ['A', 'S']: damage = 15
            hp_damage = damage
            current_hp = max(0, current_hp - damage)



            request.session['trial_hp'] = current_hp



        # 更新 MP 到 session



        request.session['trial_mp'] = current_mp



    



    # ?斗��?臬�� Game Over



    is_game_over = current_hp <= 0



    



    # 餈��? JSON ?��?



    response_data = {



        'is_correct': is_correct,



        'correct_answer': correct_answer,



        'explanation': question.explanation,



        'remaining_hp': current_hp,



        'hp_damage': hp_damage,



        'is_game_over': is_game_over,



        'current_index': current_index,



        'total_questions': len(question_ids),



    }



    



    return JsonResponse(response_data)











@login_required



def next_question(request, trial_id):



    """Next Question"""



    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # ?脣?憿����?�銵�



    question_ids = request.session.get('trial_questions', [])



    current_index = request.session.get('current_question_index', 0)



    



    # 憓��?蝝Ｗ?



    # 檢查請求方法：只有 POST 才處理答案並推進題目
    if request.method == 'POST':
         # 處理答案邏輯 (原有的代碼邏輯需要移入這裡)
         # ...
         # 假設處理成功，索引遞增
         next_index = current_index + 1
         request.session['current_question_index'] = next_index
         
         # 同步更新資料庫
         try:
             daily_task = DailyTrialTask.objects.get(id=daily_task_id)
             progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task=daily_task)
             progress.current_question_index = next_index
             progress.save(update_fields=['current_question_index'])
         except Exception:
             pass
    else:
        # GET 請求（或是 F5 刷新）：停留在當前題目
        next_index = current_index
        # 不要遞增索引



    



    # 瑼Ｘ��?臬��?��?銝��?憿?



    if next_index >= len(question_ids):
        # 所有題目已完成，進行結算
        daily_task_id = request.session.get('daily_task_id')
        
        if daily_task_id:
            # 每日試煉：在當前頁面顯示結算
            from .models import DailyTrialTask, DailyTrialProgress
            try:
                daily_task = DailyTrialTask.objects.get(id=daily_task_id)
                progress = DailyTrialProgress.objects.get(user_profile=profile, daily_task=daily_task)
                
                # 標記為完成
                progress.is_completed = True
                progress.completed_at = timezone.now()
                
                # 判斷是否通過（HP > 0）
                progress.is_passed = progress.current_hp > 0
                progress.save()
                
                # 發放經驗值獎勵（僅通過時）
                if progress.is_passed:
                    exp_reward = daily_task.trial.exp_reward
                    profile.experience += exp_reward
                    
                    # 檢查升級
                    while profile.experience >= profile.experience_to_next_level() and profile.level < 100:
                        profile.experience -= profile.experience_to_next_level()
                        profile.level += 1
                    
                    profile.save()
                else:
                    exp_reward = 0
                
                # 計算統計數據
                correct_count = sum(1 for ans in progress.answers.values() if ans.get('is_correct', False))
                total_count = len(question_ids)
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                
                # 渲染結算頁面
                context = {
                    'profile': profile,
                    'trial': daily_task.trial,
                    'daily_task': daily_task,
                    'is_completed': True,
                    'is_passed': progress.is_passed,
                    'final_hp': progress.current_hp,
                    'initial_hp': progress.initial_hp,
                    'correct_count': correct_count,
                    'total_count': total_count,
                    'accuracy': accuracy,
                    'exp_reward': exp_reward,
                    'is_daily_task': True,
                }
                
                return render(request, 'EngineerRPG/trial_exam.html', context)
                
            except Exception as e:
                messages.error(request, f'結算時發生錯誤: {e}')
                return redirect('engineer_rpg:daily_trial_list')
        
        # 一般試煉：跳轉到提交頁面
        return redirect('engineer_rpg:submit_trial', trial_id=trial_id)



    



    # ?湔�啁揣�?



    request.session['current_question_index'] = next_index



    



    # ?脣?銝��?憿?



    next_question_obj = get_object_or_404(Question, id=question_ids[next_index])



    



    # 瑼Ｘ��?臬��?箸??乩遙??



    daily_task_id = request.session.get('daily_task_id')



    if daily_task_id:



        # 瘥���乩遙�?嚗��? DailyTrialProgress ?脣? HP/MP



        from .models import DailyTrialTask, DailyTrialProgress



        try:



            daily_task = DailyTrialTask.objects.get(id=daily_task_id)



            progress = DailyTrialProgress.objects.get(



                user_profile=profile,



                daily_task=daily_task



            )



            current_hp = progress.current_hp



            current_mp = progress.current_mp



            total_hp = progress.initial_hp



            is_daily_task = True



        except (DailyTrialTask.DoesNotExist, DailyTrialProgress.DoesNotExist):



            # Fallback to session



            current_hp = request.session.get('trial_hp', 3)



            current_mp = request.session.get('trial_mp', 100)



            total_hp = profile.get_total_hp()



            is_daily_task = False



    else:



        # Comment

        current_hp = request.session.get('trial_hp', 3)



        current_mp = request.session.get('trial_mp', 100)



        total_hp = profile.get_total_hp()



        is_daily_task = False



    



    base_hp = total_hp



    
    
    
    
    # 計算剩餘時間
    if progress.started_at:
        from datetime import timedelta
        elapsed = (timezone.now() - progress.started_at).total_seconds()
        time_limit_seconds = daily_task.trial.time_limit_minutes * 60
        remaining_seconds = max(0, int(time_limit_seconds - elapsed))
    else:
        remaining_seconds = daily_task.trial.time_limit_minutes * 60

    # 獲取裝備賦予的技能
    available_skills = set()
    for slot in [profile.equipped_tool_1, profile.equipped_tool_2, profile.equipped_tool_3, profile.equipped_tool_4, profile.equipped_tool_5]:
        if slot and slot.equipment.skill_effect:
            available_skills.add(slot.equipment.skill_effect)



    context = {



        'profile': profile,



        'trial': trial,



        'question': next_question_obj,



        'current_index': next_index,



        'total_questions': len(question_ids),



        'initial_hp': current_hp,



        'initial_mp': current_mp,



        'base_hp': base_hp,



        'heart_range': range(1, max(total_hp, 5) + 1),



        'is_daily_task': is_daily_task,



        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),
        'remaining_seconds': remaining_seconds,
        'available_skills': available_skills,



    }



    



    return render(request, 'EngineerRPG/trial_exam.html', context)











@login_required



def dungeon_list(request):



    """Submit Trial"""



    profile = get_or_create_user_profile(request.user)



    



    # Comment

    categories = QuestionCategory.objects.all().prefetch_related(



        Prefetch('dungeons', 



                 queryset=Trial.objects.filter(trial_type='DUNGEON', is_active=True).order_by('required_level'),



                 to_attr='active_dungeons')



    )



    



    # Comment

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



def submit_trial(request, trial_id):



    """Function docstring"""


    if request.method != 'POST':



        return redirect('engineer_rpg:trial_detail', trial_id=trial_id)



    



    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # ?脣?蝑��?



    question_ids = request.session.get('trial_questions', [])



    questions = Question.objects.filter(id__in=question_ids)



    



    # 閮��??����



    correct_count = 0



    total_count = len(questions)



    answer_details = {}



    



    for question in questions:



        user_answer = request.POST.get(f'question_{question.id}')



        correct_answer = question.correct_answer



        



        is_correct = False



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



    



    # 閮��??��?



    start_time = timezone.datetime.fromisoformat(request.session.get('trial_start_time'))



    time_spent = (timezone.now() - start_time).total_seconds()



    



    # 閮��??����??HP



    # ?脣??��? HP (憒��?瘝��?閮��??��?閮剔�� 3)



    initial_hp = request.session.get('trial_hp', 3)



    wrong_answers = total_count - correct_count



    remaining_hp = max(0, initial_hp - wrong_answers)



    



    score = int((correct_count / total_count) * 100)



    



    # ?��?璇�隞塚���???>= 60 銝?HP > 0



    is_passed = score >= 60 and remaining_hp > 0



    



    # 瑼Ｘ��?臬��?箏�唬���??��??��?



    is_dungeon_repeat = False



    if trial.trial_type == 'DUNGEON':



        # Comment

        if TrialRecord.objects.filter(user_profile=profile, trial=trial, is_passed=True).exists():



            is_dungeon_repeat = True



            



    # 閮��?蝬��???



    exp_reward = trial.exp_reward



    if is_dungeon_repeat:



        exp_reward = max(1, int(exp_reward * 0.01))  # ?���� 1% 蝬��???



            



    # 撱箇?閮��?



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



    



    # 瑼Ｘ��?臬��?箸??乩遙??



    daily_task_id = request.session.get('daily_task_id')



    if daily_task_id:



        from .models import DailyTrialTask, DailyTrialProgress



        try:



            daily_task = DailyTrialTask.objects.get(id=daily_task_id)



            progress = DailyTrialProgress.objects.get(



                user_profile=profile,



                daily_task=daily_task



            )



            



            # 璅��??箏歇摰��?



            progress.is_completed = True



            progress.is_passed = is_passed



            progress.completed_at = timezone.now()



            progress.save()



            



            # ?���� TrialRecord ??DailyTrialTask



            record.daily_task = daily_task



            record.save()



            



        except (DailyTrialTask.DoesNotExist, DailyTrialProgress.DoesNotExist):



            pass



    



    # 憒��??��?嚗�蝯虫���???



    if is_passed:



        profile.experience += exp_reward



        



        # 瑼Ｘ��?��?



        while profile.experience >= profile.experience_to_next_level():



            profile.experience -= profile.experience_to_next_level()



            profile.level += 1



            



            # Comment

            # Fixed garbled f-string




            



            # MP 瘥��??��?



            msg_parts.append('?�憭?MP +20')



            



            # HP 瘥?10 蝝��???



            if profile.level % 10 == 0:



                msg_parts.append('?�憭?HP +1')



                



            messages.success(request, 'Operation successful')



        



        profile.update_stats()  # 蝣箔?撅祆�扳��??



        



        # ?寞??���菜����塚���??��??��??���唬���?嚗��??���唬���?嚗?



        if not is_dungeon_repeat:



            # ?����?����



            if trial.item_reward:



                # Comment

                user_item, created = UserItem.objects.get_or_create(



                    user_profile=profile,



                    item=trial.item_reward,



                    defaults={'quantity': 0}



                )



                user_item.quantity += 1



                user_item.save()



                



                record.item_gained = trial.item_reward



                record.save()



                messages.success(request, 'Operation successful')




            



            # 撘瑕??瑁遘?���蛛�����?��?蝝��?璇臬?憓��?嚗?



            min_scrolls = 1



            max_scrolls = 3



            



            if profile.level >= 50:



                min_scrolls, max_scrolls = 4, 6



            elif profile.level >= 25:



                min_scrolls, max_scrolls = 3, 5



            elif profile.level >= 10:



                min_scrolls, max_scrolls = 2, 4



                



            scroll_count = random.randint(min_scrolls, max_scrolls)



            scroll, created = EnhancementScroll.objects.get_or_create(user_profile=profile)



            scroll.quantity += scroll_count



            scroll.save()



            messages.success(request, f'?脣?撘瑕??瑁遘 x{scroll_count}')



        elif is_dungeon_repeat:



            messages.info(request, 'Information')




    



    # 皜���� session



    for key in ['trial_id', 'trial_questions', 'trial_start_time', 'trial_answers', 'daily_task_id']:



        request.session.pop(key, None)



    



    return redirect('engineer_rpg:trial_record_detail', record_id=record.id)











@login_required



def trial_record_detail(request, record_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    record = get_object_or_404(TrialRecord, id=record_id, user_profile=profile)



    



    context = {



        'profile': profile,



        'record': record,



    }



    



    return render(request, 'EngineerRPG/trial_record.html', context)











# ==================== ?��?蝟餌絞 ====================







@login_required



@login_required
def apply_promotion(request):
    """申請晉升"""
    profile = get_or_create_user_profile(request.user)
    
    # Check for pending request
    pending_request = PromotionRequest.objects.filter(
        applicant=profile,
        status='PENDING'
    ).first()
    
    if pending_request:
        messages.warning(request, '您已有審核中的晉升申請，請耐心等候。')
        return redirect('engineer_rpg:dashboard')
    
    # 決定目標職銜與檢查條件
    current_rank = profile.rank
    target_rank = None
    
    if current_rank == 'INTERN':
        # 實習生 -> 助理工程師
        # 條件：共同必修 (ROOT) 技能 100% 完成
        required_root = SkillNode.objects.filter(node_type='ROOT')
        completed_root = UserSkill.objects.filter(
            user_profile=profile,
            skill_node__in=required_root,
            status='COMPLETED'
        ).count()
        
        if completed_root < required_root.count():
            messages.error(request, '申請失敗：需完成所有「共同必修」技能才可申請成為助理工程師。')
            return redirect('engineer_rpg:skill_tree')
            
        target_rank = 'ASSISTANT'
        
    elif current_rank == 'ASSISTANT':
        # 助理工程師 -> 工程師
        # 條件：職業核心 (CORE) 技能完成度 > 50%
        required_core = SkillNode.objects.filter(
            character_class=profile.character_class,
            node_type='CORE'
        )
        completed_core = UserSkill.objects.filter(
            user_profile=profile,
            skill_node__in=required_core,
            status='COMPLETED'
        ).count()
        
        total_core = required_core.count()
        if total_core > 0 and (completed_core / total_core) < 0.5:
            messages.error(request, '申請失敗：需完成 50% 以上「職業核心」技能才可申請成為工程師。')
            return redirect('engineer_rpg:skill_tree')
            
        target_rank = 'ENGINEER'

    elif current_rank == 'ENGINEER':
        messages.info(request, '您已是正式工程師，無需再申請基礎晉升。')
        return redirect('engineer_rpg:dashboard')
        
    else:
        messages.error(request, '未知的職銜狀態。')
        return redirect('engineer_rpg:dashboard')

    # 建立晉升申請
    target_level = profile.level + 1
    
    promotion_request = PromotionRequest.objects.create(
        applicant=profile,
        current_level=profile.level,
        target_level=target_level,
        status='PENDING'
    )
    
    # 我們可以將 target_rank 存入備註或日誌，或者依據 level 推算 (暫不更動模型)
    # 但為了讓審核者知道，我們可以 update 申請單的備註? 
    # PromotionRequest 有 review_comment，但那是審核者寫的。
    # 暫時依賴 approve_request 裡的邏輯重判。
    
    messages.success(request, f'已成功送出晉升申請！')
    return redirect('engineer_rpg:dashboard')


@login_required



def promotion_trial(request, request_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    promotion_request = get_object_or_404(PromotionRequest, id=request_id, applicant=profile)



    



    # ?�鋆�?臭誑閮剛??寞??��??�閰�??



    # Comment

    return redirect('engineer_rpg:daily_trial_list')











# ==================== ?��?璁?====================







@login_required



def leaderboard(request):



    """Trial Attempts"""



    profile = get_or_create_user_profile(request.user)



    



    # 蝑��??��?



    level_ranking = UserProfile.objects.all().order_by('-level', '-experience')[:50]



    



    # 閰衣??��?嚗����?梧?



    from datetime import timedelta



    week_ago = timezone.now() - timedelta(days=7)



    trial_ranking = UserProfile.objects.annotate(



        trial_count=Count('trial_records', filter=Q(trial_records__completed_at__gte=week_ago))



    ).order_by('-trial_count')[:50]



    



    # Count user trial attempts



    passed_trials_count = TrialRecord.objects.filter(user_profile=profile, is_passed=True).count()



    



    context = {



        'profile': profile,



        'level_ranking': level_ranking,



        'trial_ranking': trial_ranking,



        'passed_trials_count': passed_trials_count,



    }



    



    return render(request, 'EngineerRPG/leaderboard.html', context)











# ==================== 銝餌恣隞���� ====================







@login_required



def manager_dashboard(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    # 敺�撖�?貊�唾�?



    pending_requests = PromotionRequest.objects.filter(status='PENDING').order_by('-applied_at')



    



    context = {



        'profile': profile,



        'pending_requests': pending_requests,



    }



    



    return render(request, 'EngineerRPG/manager_dashboard.html', context)











@login_required



def promotion_requests(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    requests = PromotionRequest.objects.all().order_by('-applied_at')



    



    # ?��?



    paginator = Paginator(requests, 20)



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    context = {



        'profile': profile,



        'page_obj': page_obj,



    }



    



    return render(request, 'EngineerRPG/promotion_requests.html', context)











@login_required



def review_request(request, request_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    promotion_request = get_object_or_404(PromotionRequest, id=request_id)



    



    # Comment

    applicant_skills = UserSkill.objects.filter(



        user_profile=promotion_request.applicant



    ).select_related('skill_node')



    



    context = {



        'profile': profile,



        'promotion_request': promotion_request,



        'applicant_skills': applicant_skills,



    }



    



    return render(request, 'EngineerRPG/review_request.html', context)











@login_required



@login_required
def approve_request(request, request_id):
    """核准晉升申請"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, '您沒有權限執行此操作。')
        return redirect('engineer_rpg:dashboard')
    
    promotion_request = get_object_or_404(PromotionRequest, id=request_id)
    
    if promotion_request.status == 'PENDING':
        promotion_request.status = 'APPROVED'
        promotion_request.reviewer = request.user
        promotion_request.reviewed_at = timezone.now()
        promotion_request.save()
        
        # 更新申請人職銜與等級
        applicant = promotion_request.applicant
        
        # 決定新職銜
        if applicant.rank == 'INTERN':
             applicant.rank = 'ASSISTANT'
        elif applicant.rank == 'ASSISTANT':
             applicant.rank = 'ENGINEER'
        
        # 重新計算等級 (釋放累積的經驗值)
        # 原本是直接設為 target_level，現在要根據總經驗值重算
        # Import helper here to avoid circular imports at top level if not handled
        from EngineerRPG.utils.level_system import calculate_level_from_xp
        
        new_level, remaining_xp = calculate_level_from_xp(applicant.level, applicant.experience)
        
        # 如果新等級比 target_level 還低 (不應該發生，因為有基本獎勵)，至少升一級
        if new_level <= applicant.level:
            new_level = applicant.level + 1
            
        applicant.level = new_level
        applicant.experience = remaining_xp
        applicant.save()
        
        messages.success(request, f'已核准 {applicant.user.username} 的晉升申請！新職銜：{applicant.get_rank_display()}，等級提升至 Lv.{applicant.level}。')
        
        # 發送通知給申請人 (TODO: Implement notification system)
        
    return redirect('engineer_rpg:promotion_requests')


def reject_request(request, request_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    promotion_request = get_object_or_404(PromotionRequest, id=request_id)



    



    if promotion_request.status == 'PENDING':



        promotion_request.status = 'REJECTED'



        promotion_request.reviewer = request.user



        promotion_request.reviewed_at = timezone.now()



        



        if request.method == 'POST':



            promotion_request.review_comment = request.POST.get('comment', '')



        



        promotion_request.save()



        



        messages.success(request, 'Operation successful')




    



    return redirect('engineer_rpg:manager_dashboard')











# ==================== 蝞∠??∩???====================







@login_required



def admin_dashboard(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role != 'ADMIN':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    # 蝯梯?鞈��?



    total_users = UserProfile.objects.count()



    total_questions = Question.objects.count()



    total_skills = SkillNode.objects.count()



    total_equipment = Equipment.objects.count()



    total_items = Item.objects.count()



    



    context = {



        'profile': profile,



        'total_users': total_users,



        'total_questions': total_questions,



        'total_skills': total_skills,



        'total_equipment': total_equipment,



        'total_items': total_items,



    }



    



    return render(request, 'EngineerRPG/admin_dashboard.html', context)











@login_required



def user_management(request):



    """User List"""



    profile = get_or_create_user_profile(request.user)



    



    if profile.role != 'ADMIN':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    users = UserProfile.objects.all().select_related('user', 'character_class')



    



    context = {



        'profile': profile,



        'users': users,



    }



    



    return render(request, 'EngineerRPG/user_management.html', context)











@login_required
def create_user(request):
    """創建新使用者"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        character_class_id = request.POST.get('character_class')
        role = request.POST.get('role', 'ADVENTURER')
        email = request.POST.get('email', '').strip()
        
        # 驗證必填欄位
        if not all([username, password, employee_id, character_class_id]):
            messages.error(request, '請填寫所有必填欄位！')
            return redirect('engineer_rpg:create_user')
        
        # 檢查使用者名稱是否已存在
        if User.objects.filter(username=username).exists():
            messages.error(request, f'使用者名稱「{username}」已存在！')
            return redirect('engineer_rpg:create_user')
        
        # 檢查員工編號是否已存在
        if UserProfile.objects.filter(employee_id=employee_id).exists():
            messages.error(request, f'員工編號「{employee_id}」已存在！')
            return redirect('engineer_rpg:create_user')
        
        try:
            # 創建 User
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            
            # 創建 UserProfile
            character_class = CharacterClass.objects.get(id=character_class_id)
            user_profile = UserProfile.objects.create(
                user=user,
                employee_id=employee_id,
                character_class=character_class,
                role=role,
                level=1,
                experience=0
            )
            
            messages.success(request, f'使用者「{username}」創建成功！')
            return redirect('engineer_rpg:user_management')
            
        except Exception as e:
            messages.error(request, f'創建使用者時發生錯誤：{str(e)}')
            # 如果創建失敗，刪除已創建的 User
            try:
                if 'user' in locals():
                    user.delete()
            except:
                pass
            return redirect('engineer_rpg:create_user')
    
    # GET 請求，顯示表單
    character_classes = CharacterClass.objects.all()
    role_choices = UserProfile.ROLE_CHOICES
    
    context = {
        'profile': profile,
        'character_classes': character_classes,
        'role_choices': role_choices,
    }
    return render(request, 'EngineerRPG/user_form.html', context)


@login_required
def edit_user(request, user_id):
    """編輯使用者"""
    profile = get_or_create_user_profile(request.user)
    if not profile or profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, '權限不足！')
        return redirect('engineer_rpg:dashboard')
    
    # 獲取要編輯的使用者
    user_profile = get_object_or_404(UserProfile, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        employee_id = request.POST.get('employee_id', '').strip()
        character_class_id = request.POST.get('character_class')
        role = request.POST.get('role', 'ADVENTURER')
        email = request.POST.get('email', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        # 驗證必填欄位
        if not all([username, employee_id, character_class_id]):
            messages.error(request, '請填寫所有必填欄位！')
            return redirect('engineer_rpg:edit_user', user_id=user_id)
        
        # 檢查使用者名稱是否已被其他使用者使用
        if User.objects.filter(username=username).exclude(id=user_profile.user.id).exists():
            messages.error(request, f'使用者名稱「{username}」已存在！')
            return redirect('engineer_rpg:edit_user', user_id=user_id)
        
        # 檢查員工編號是否已被其他使用者使用
        if UserProfile.objects.filter(employee_id=employee_id).exclude(id=user_profile.id).exists():
            messages.error(request, f'員工編號「{employee_id}」已存在！')
            return redirect('engineer_rpg:edit_user', user_id=user_id)
        
        try:
            # 更新 User
            user_profile.user.username = username
            user_profile.user.email = email
            user_profile.user.is_active = is_active
            
            # 如果提供了新密碼，則更新密碼
            if password:
                user_profile.user.set_password(password)
            
            user_profile.user.save()
            
            # 更新 UserProfile
            character_class = CharacterClass.objects.get(id=character_class_id)
            user_profile.employee_id = employee_id
            user_profile.character_class = character_class
            user_profile.role = role
            user_profile.save()
            
            messages.success(request, f'使用者「{username}」更新成功！')
            return redirect('engineer_rpg:user_management')
            
        except Exception as e:
            messages.error(request, f'更新使用者時發生錯誤：{str(e)}')
            return redirect('engineer_rpg:edit_user', user_id=user_id)
    
    # GET 請求，顯示編輯表單
    character_classes = CharacterClass.objects.all()
    role_choices = UserProfile.ROLE_CHOICES
    
    context = {
        'profile': profile,
        'user_profile': user_profile,
        'character_classes': character_classes,
        'role_choices': role_choices,
        'is_edit': True,
    }
    return render(request, 'EngineerRPG/user_edit_form.html', context)


@login_required
def delete_user(request, user_id):
    """刪除使用者"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '無效的請求方法'})
    
    profile = get_or_create_user_profile(request.user)
    if not profile or profile.role not in ['MANAGER', 'ADMIN']:
        return JsonResponse({'success': False, 'message': '權限不足！'})
    
    # 安全檢查：防止刪除自己的帳號
    if str(user_id) == str(profile.id):
        return JsonResponse({'success': False, 'message': '不能刪除自己的帳號！'})
    
    try:
        user_profile = get_object_or_404(UserProfile, id=user_id)
        username = user_profile.user.username
        
        # 刪除 User（會級聯刪除 UserProfile）
        user_profile.user.delete()
        
        return JsonResponse({
            'success': True, 
            'message': f'使用者「{username}」已成功刪除'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'刪除使用者時發生錯誤：{str(e)}'
        })























@login_required



def question_management(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')

    # 重置今日試煉功能的處理（如果有點擊重置按鈕）
    if request.method == 'POST' and 'reset_trial' in request.POST:
        from .models import DailyTrialProgress
        today = timezone.now().date()
        deleted_count, _ = DailyTrialProgress.objects.filter(
            user_profile=profile,
            daily_task__date=today
        ).delete()
        messages.success(request, f'已重置今日試煉進度 (共刪除 {deleted_count} 筆記錄)')
        return redirect('engineer_rpg:question_management')



    



    # 蝭拚��



    category_id = request.GET.get('category')



    search_query = request.GET.get('q')



    



    questions = Question.objects.all().order_by('-created_at')



    



    if category_id:



        questions = questions.filter(category_id=category_id)



    



    if search_query:



        questions = questions.filter(content__icontains=search_query)



    



    # ?��?



    paginator = Paginator(questions, 20)



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    categories = QuestionCategory.objects.all()
    
    
    context = {
        'profile': profile,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': int(category_id) if category_id else None,
        'search_query': search_query,
    }



    



    return render(request, 'EngineerRPG/management/question_list.html', context)











# -*- coding: utf-8 -*-

@login_required
def course_management(request):
    """Course Management Dashboard"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')

    search_query = request.GET.get('q')
    courses = Course.objects.all().order_by('title')
    
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
        
    paginator = Paginator(courses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'courses': page_obj, 
        'search_query': search_query,
        'page_obj': page_obj,
        'is_paginated': True,
    }
    return render(request, 'EngineerRPG/management/course_list.html', context)


@login_required
def create_course(request):
    """Create a new course"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        content_type = request.POST.get('content_type', 'LINK')
        content_url = request.POST.get('content_url', '')
        content_file = request.FILES.get('content_file')
        
        # Exam settings
        exam_time_limit = request.POST.get('exam_time_limit', 20)
        passing_score = request.POST.get('passing_score', 80)
        question_ids = request.POST.getlist('questions')
        
        try:
            course = Course.objects.create(
                title=title,
                description=description,
                content_type=content_type,
                content_url=content_url,
                content_file=content_file,
                exam_time_limit=int(exam_time_limit),
                passing_score=int(passing_score)
            )
            
            # Add questions to course
            if question_ids:
                questions = Question.objects.filter(id__in=question_ids)
                course.questions.set(questions)
            
            messages.success(request, f'課程「{course.title}」創建成功')
            return redirect('engineer_rpg:course_management')
        except Exception as e:
            messages.error(request, f'創建課程失敗: {e}')
    
    # Get all questions for selection
    questions = Question.objects.all().order_by('category__name', 'content')
    categories = QuestionCategory.objects.all()
    
    context = {
        'profile': profile,
        'questions': questions,
        'categories': categories,
        'mode': 'create',
        'selected_question_ids': [],
    }
    
    return render(request, 'EngineerRPG/management/course_form.html', context)


@login_required
def edit_course(request, course_id):
    """Edit an existing course"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description', '')
        course.content_type = request.POST.get('content_type', 'LINK')
        course.content_url = request.POST.get('content_url', '')
        
        if 'content_file' in request.FILES:
            course.content_file = request.FILES['content_file']
        
        course.exam_time_limit = int(request.POST.get('exam_time_limit', 20))
        course.passing_score = int(request.POST.get('passing_score', 80))
        
        question_ids = request.POST.getlist('questions')
        
        try:
            course.save()
            
            # Update questions
            if question_ids:
                questions = Question.objects.filter(id__in=question_ids)
                course.questions.set(questions)
            else:
                course.questions.clear()
            
            messages.success(request, f'課程「{course.title}」更新成功')
            return redirect('engineer_rpg:course_management')
        except Exception as e:
            messages.error(request, f'更新課程失敗: {e}')
    
    # Get all questions for selection
    questions = Question.objects.all().order_by('category__name', 'content')
    categories = QuestionCategory.objects.all()
    
    context = {
        'profile': profile,
        'course': course,
        'questions': questions,
        'categories': categories,
        'selected_question_ids': list(course.questions.values_list('id', flat=True)),
        'mode': 'edit'
    }
    
    return render(request, 'EngineerRPG/management/course_form.html', context)



@login_required
def delete_course(request, course_id):
    """Delete a course"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_title = course.title
        try:
            course.delete()
            messages.success(request, f'課程「{course_title}」已刪除')
        except Exception as e:
            messages.error(request, f'刪除課程失敗: {e}')
    
    return redirect('engineer_rpg:course_management')


@login_required



def create_question(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    if request.method == 'POST':



        # 蝪∪�桀祕�?嚗��?蝥����?寧�� Form



        content = request.POST.get('content')



        q_type = request.POST.get('question_type')



        category_id = request.POST.get('category')



        difficulty = request.POST.get('difficulty')



        



        # ?��??賊??��?獢?



        options_json = request.POST.get('options')



        answer_json = request.POST.get('correct_answer')



        



        try:



            import json



            options = json.loads(options_json)



            answer = json.loads(answer_json)



            



            question = Question.objects.create(



                content=content,



                question_type=q_type,



                category_id=category_id if category_id else None,



                difficulty=difficulty,



                options=options,



                correct_answer=answer



            )



            messages.success(request, 'Operation successful')




            return redirect('engineer_rpg:question_management')



        except Exception as e:



            messages.error(request, 'An error occurred')




            



    categories = QuestionCategory.objects.all()



    context = {'profile': profile, 'categories': categories}



    return render(request, 'EngineerRPG/management/question_form.html', context)











@login_required



def edit_question(request, question_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    question = get_object_or_404(Question, id=question_id)



    



    if request.method == 'POST':



        question.content = request.POST.get('content')



        question.question_type = request.POST.get('question_type')



        question.category_id = request.POST.get('category') or None



        question.difficulty = request.POST.get('difficulty')



        



        try:



            import json



            question.options = json.loads(request.POST.get('options'))



            question.correct_answer = json.loads(request.POST.get('correct_answer'))



            question.save()



            messages.success(request, 'Operation successful')




            return redirect('engineer_rpg:question_management')



        except Exception as e:



            messages.error(request, 'An error occurred')




            



    categories = QuestionCategory.objects.all()



    import json



    context = {



        'profile': profile, 



        'question': question, 



        'categories': categories,



        'options_json': json.dumps(question.options, ensure_ascii=False),



        'answer_json': json.dumps(question.correct_answer, ensure_ascii=False)



    }



    return render(request, 'EngineerRPG/management/question_form.html', context)











# ==================== ?��??���唬���?蝞∠? ====================







@login_required



def category_management(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    categories = QuestionCategory.objects.all()



    



    if request.method == 'POST':



        if 'create' in request.POST:



            name = request.POST.get('name')



            desc = request.POST.get('description')



            QuestionCategory.objects.create(name=name, description=desc)



            messages.success(request, 'Operation successful')




        elif 'delete' in request.POST:



            cat_id = request.POST.get('category_id')



            QuestionCategory.objects.filter(id=cat_id).delete()



            messages.success(request, 'Operation successful')




        return redirect('engineer_rpg:category_management')



        



    context = {'profile': profile, 'categories': categories}



    return render(request, 'EngineerRPG/management/category_list.html', context)











@login_required



def dungeon_management(request):



    """Dungeon Management"""



    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    dungeons = Trial.objects.filter(trial_type='DUNGEON').order_by('-created_at')



    



    # ?芸??��??��???



    if not Item.objects.exists():



        _seed_default_items()



    



    context = {'profile': profile, 'dungeons': dungeons}



    return render(request, 'EngineerRPG/management/dungeon_list.html', context)











@login_required



def create_dungeon(request):



    """Function docstring"""




    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    if request.method == 'POST':



        title = request.POST.get('title')



        category_id = request.POST.get('category')



        description = request.POST.get('description')



        level_req = request.POST.get('required_level', 1)



        exp_reward = request.POST.get('exp_reward', 200)



        time_limit = request.POST.get('time_limit', 60)



        item_reward_id = request.POST.get('equipment_reward')  # ?�蝡舀���??�蝔�?急?靽��? equipment_reward



        is_active = request.POST.get('is_active') == '1'



        question_ids = request.POST.getlist('questions')



        



        trial = Trial.objects.create(



            title=title,



            description=description,



            trial_type='DUNGEON',



            category_id=category_id,



            required_level=level_req,



            exp_reward=exp_reward,



            item_reward_id=item_reward_id if item_reward_id else None,



            time_limit_minutes=time_limit,



            question_count=20,  # ?箏???20 憿?



            is_active=is_active



        )



        trial.questions.set(question_ids)



        messages.success(request, 'Operation successful')




        return redirect('engineer_rpg:dungeon_management')







    categories = QuestionCategory.objects.all()



    questions = Question.objects.filter(is_active=True) # ?臭誑?芸???AJAX 頛����



    items = Item.objects.all()  # ?脣??�?��???



    context = {



        'profile': profile, 



        'categories': categories,



        'questions': questions,



        'equipments': items  # ?箔??詨捆璅⊥�選�����?���� equipments 霈����??



    }



    return render(request, 'EngineerRPG/management/dungeon_form.html', context)











@login_required



def edit_dungeon(request, dungeon_id):



    """Function docstring"""




    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    dungeon = get_object_or_404(Trial, id=dungeon_id, trial_type='DUNGEON')



    



    # Comment

    is_locked = TrialRecord.objects.filter(trial=dungeon, is_passed=True).exists()



    



    if request.method == 'POST':



        # Comment

        is_active = request.POST.get('is_active') == '1'



        dungeon.is_active = is_active



        



        if is_locked:



            # Comment

            dungeon.save()



            messages.warning(request, 'Warning')




            return redirect('engineer_rpg:dungeon_management')



            



        dungeon.title = request.POST.get('title')



        dungeon.category_id = request.POST.get('category')



        dungeon.description = request.POST.get('description')



        dungeon.required_level = request.POST.get('required_level')



        dungeon.exp_reward = request.POST.get('exp_reward', 200)



        dungeon.time_limit_minutes = request.POST.get('time_limit', 60)



        item_reward_id = request.POST.get('equipment_reward')



        dungeon.item_reward_id = item_reward_id if item_reward_id else None



        



        question_ids = request.POST.getlist('questions')



        dungeon.questions.set(question_ids)



        dungeon.question_count = 20  # ?箏???20 憿?



        dungeon.save()



        



        messages.success(request, 'Operation successful')




        return redirect('engineer_rpg:dungeon_management')







    categories = QuestionCategory.objects.all()



    questions = Question.objects.filter(is_active=True)



    items = Item.objects.all()



    context = {



        'profile': profile, 



        'dungeon': dungeon,



        'categories': categories,



        'questions': questions,



        'equipments': items, # ?詨捆璅⊥��



        'is_locked': is_locked



    }



    return render(request, 'EngineerRPG/management/dungeon_form.html', context)











@login_required



def skill_tree_editor(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role != 'ADMIN':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    # Comment

    classes = CharacterClass.objects.all()



    



    # Comment

    selected_class_code = request.GET.get('class', 'CIVIL')



    



    # Comment

    skills = SkillNode.objects.filter(



        Q(node_type='ROOT') | Q(character_class__code=selected_class_code)



    ).prefetch_related('parent_skills', 'courses').order_by('node_type', 'position_y', 'position_x')



    



    # Comment

    courses = Course.objects.all().prefetch_related('skill_nodes')



    



    # Calculate XP Budgets
    from django.db.models import Sum
    root_xp_current = SkillNode.objects.filter(node_type='ROOT').aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0
    core_xp_current = SkillNode.objects.filter(node_type='CORE', character_class__code=selected_class_code).aggregate(Sum('exp_reward'))['exp_reward__sum'] or 0

    context = {
        'profile': profile,
        'skills': skills,
        'courses': courses,
        'classes': classes,
        'selected_class': selected_class_code,
        # Budget Info
        'root_xp_current': root_xp_current,
        'root_xp_limit': 4500,
        'core_xp_current': core_xp_current,
        'core_xp_limit': 118000,
    }



    



    return render(request, 'EngineerRPG/skill_tree_editor.html', context)











# ==================== API ====================







@login_required



def api_user_stats(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    data = {



        'level': profile.level,



        'experience': profile.experience,



        'hp': profile.hp,



        'mp': profile.mp,



        'total_hp': profile.get_total_hp(),



    }



    



    return JsonResponse(data)











@login_required



def api_skill_tree_data(request):



    """Function docstring"""


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















# Comment





@login_required



def api_skill_editor_data(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return JsonResponse({'error': 'Permission denied'}, status=403)



        



    class_code = request.GET.get('class', 'CIVIL')



    



    # Comment

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



        



    # Comment

    all_courses = Course.objects.all().values('id', 'title', 'content_type')



    



    return JsonResponse({



        'nodes': nodes,



        'courses': list(all_courses)



    })







@login_required



@csrf_exempt



def api_save_skill_layout(request):



    """Function docstring"""


    if request.method != 'POST':



        return JsonResponse({'error': 'Method not allowed'}, status=405)



        



    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return JsonResponse({'error': 'Permission denied'}, status=403)



        



    try:



        data = json.loads(request.body)



        updates = data.get('updates', [])



        



        for item in updates:



            SkillNode.objects.filter(id=item['id']).update(



                position_x=item['x'],



                position_y=item['y']



            )



            



            return JsonResponse({'status': 'success', 'message': 'Operation successful'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)












@login_required



@csrf_exempt



def api_save_skill_node(request):
    """Build Skill Tree"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = get_or_create_user_profile(request.user)
        if not profile or profile.role != 'ADMIN':
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        node_id = data.get('id')
        
        if node_id:
            # Update
            node = SkillNode.objects.get(id=node_id)
        else:
            # Create
            node = SkillNode()
            
        node.name = data.get('name')
        
        # Handle node_type: Ensure it's valid
        node_type = data.get('type') or data.get('node_type')
        if not node_type:
             node.node_type = 'ADVANCED' # Default
        else:
             node.node_type = node_type
             
        node.description = data.get('description', '')
        node.exp_reward = int(data.get('exp_reward', 50))
        
        # Character Class
        class_code = data.get('class_code')
        if class_code:
            try:
                char_class = CharacterClass.objects.get(code=class_code)
                node.character_class = char_class
            except CharacterClass.DoesNotExist:
                pass
                
                # Validate ROOT XP Limit (Lv 10 Cap check)
        # Lv 10 requires ~ 4500 XP (Sum of n*100 for n=1 to 9 is 4500)
        # Actually, let's double check the formula.
        # Lv 1->2: 100
        # ...
        # Lv 9->10: 900
        # Total = 4500.
        MAX_ROOT_XP = 4500
        
        if node.node_type == 'ROOT':
            # Calculate current total ROOT XP (excluding this node if it exists)
            current_root_xp = 0
            root_skills = SkillNode.objects.filter(node_type='ROOT')
            if node.id:
                root_skills = root_skills.exclude(id=node.id)
                
            for s in root_skills:
                current_root_xp += s.exp_reward
                
            new_total = current_root_xp + node.exp_reward
            
            if new_total > MAX_ROOT_XP:
                return JsonResponse({
                    'error': f'共同必修 (ROOT) 總經驗值上限為 {MAX_ROOT_XP} (Lv.10)。目前總計: {new_total}，請調整獎勵值。'
                }, status=400)
        
        MAX_CORE_XP = 118000
        
        if node.node_type == 'CORE':
             current_core_xp = 0
             # Note: node.character_class might not be set yet if it's new and we rely on data.get('class_code')
             # But loop above sets node.character_class.
             
             if not node.character_class:
                 # Try to get from data if not set yet (unlikely given previous logic)
                 pass
                 
             if node.character_class:
                 core_skills = SkillNode.objects.filter(node_type='CORE', character_class=node.character_class)
                 if node.id:
                     core_skills = core_skills.exclude(id=node.id)
                     
                 for s in core_skills:
                     current_core_xp += s.exp_reward
                     
                 new_total = current_core_xp + node.exp_reward
                 
                 if new_total > MAX_CORE_XP:
                     return JsonResponse({
                         'error': f'職業核心 (CORE) 總經驗值上限為 {MAX_CORE_XP} (Lv.50)。目前總計: {new_total}，請調整獎勵值。'
                     }, status=400)
        node.save()
        
        # Handle parent skills
        parent_ids = data.get('parents', [])
        node.parent_skills.clear()
        if parent_ids:
            for pid in parent_ids:
                 try:
                     parent = SkillNode.objects.get(id=pid)
                     node.parent_skills.add(parent)
                 except SkillNode.DoesNotExist:
                     pass
                     
        # Handle courses
        course_ids = data.get('courses', [])
        node.courses.clear()
        if course_ids:
            for cid in course_ids:
                try:
                    course = Course.objects.get(id=cid)
                    node.courses.add(course)
                except Course.DoesNotExist:
                    pass
        
        return JsonResponse({'status': 'success', 'message': 'Saved successfully', 'node': {'id': node.id, 'name': node.name}})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required



@csrf_exempt



def api_delete_skill_node(request):



    """Function docstring"""


    if request.method != 'POST':



        return JsonResponse({'error': 'Method not allowed'}, status=405)



        



    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return JsonResponse({'error': 'Permission denied'}, status=403)



        



    try:



        data = json.loads(request.body)



        node_id = data.get('id')



        SkillNode.objects.get(id=node_id).delete()



        return JsonResponse({'status': 'success', 'message': 'Operation successful'})

    except Exception as e:

        return JsonResponse({'error': str(e)}, status=400)













@login_required



@csrf_exempt



def api_manage_skill_course(request):
    """Manage skill course association"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    try:
        profile = get_or_create_user_profile(request.user)
        if not profile or profile.role != 'ADMIN':
            return JsonResponse({'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)
        node_id = data.get('node_id')
        course_id = data.get('course_id')
        action = data.get('action') # 'add' or 'remove'
        
        node = SkillNode.objects.get(id=node_id)
        course = Course.objects.get(id=course_id)
        
        if action == 'add':
            course.skill_nodes.add(node)
        elif action == 'remove':
            course.skill_nodes.remove(node)
            
        return JsonResponse({'status': 'success', 'message': 'Operation successful'})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)














@login_required



@csrf_exempt



def api_auto_layout_skill_tree(request):



    """Function docstring"""


    if request.method != 'POST':



        return JsonResponse({'error': 'Method not allowed'}, status=405)



        



    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return JsonResponse({'error': 'Permission denied'}, status=403)



        



    try:



        data = json.loads(request.body)



        class_code = data.get('class_code', 'CIVIL')



        



        # Comment

        skills = SkillNode.objects.filter(



            Q(node_type='ROOT') | Q(character_class__code=class_code)



        ).prefetch_related('parent_skills')



        



        # Comment

        skill_map = {skill.id: skill for skill in skills}



        



        # Comment

        skill_levels = {}



        visited = set()



        



        def calculate_level(skill_id):



            """Function docstring"""


            if skill_id in skill_levels:



                return skill_levels[skill_id]



            



            if skill_id in visited:



                # 瑼Ｘ葫?啣儐?唬?鞈?



                return 0



            



            visited.add(skill_id)



            skill = skill_map.get(skill_id)



            if not skill:



                return 0



            



            # Comment

            parent_ids = skill.parent_skills.values_list('id', flat=True)



            if not parent_ids:



                # Comment

                skill_levels[skill_id] = 0



            else:



                # Comment

                parent_levels = [calculate_level(pid) for pid in parent_ids if pid in skill_map]



                if parent_levels:



                    skill_levels[skill_id] = max(parent_levels) + 1



                else:



                    # Comment

                    skill_levels[skill_id] = 0



            



            visited.remove(skill_id)



            return skill_levels[skill_id]



        



        # Comment

        for skill in skills:



            calculate_level(skill.id)



        



        # ?�撅斤���?蝯?



        levels = {}



        for skill_id, level in skill_levels.items():



            if level not in levels:



                levels[level] = []



            levels[level].append(skill_id)



        



        # ?��?摨扳?



        Y_SPACING = 200  # 撅斤??��?



        X_SPACING = 150  # ?�撅斤���??賡?頝?



        X_OFFSET = 100   # 韏瑕? X 摨扳?



        



        updated_count = 0



        for level, skill_ids in levels.items():



            y = level * Y_SPACING



            num_skills = len(skill_ids)



            



            # Comment

            start_x = X_OFFSET



            



            for i, skill_id in enumerate(skill_ids):



                x = start_x + i * X_SPACING



                SkillNode.objects.filter(id=skill_id).update(



                    position_x=x,



                    position_y=y



                )



                updated_count += 1



        



        return JsonResponse({



            'status': 'success',



            'count': updated_count,



            'levels': len(levels),









        })



        



    except Exception as e:



        return JsonResponse({'error': str(e)}, status=400)











@login_required



def create_question_view(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    from .forms import QuestionForm



    



    if request.method == 'POST':



        form = QuestionForm(request.POST)



        if form.is_valid():



            form.save()



            messages.success(request, 'Operation successful')




            return redirect('engineer_rpg:question_management')



    else:



        form = QuestionForm()



    



    return render(request, 'EngineerRPG/create_question.html', {'profile': profile, 'form': form})











@login_required



def import_questions_view(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    from .forms import QuestionImportForm



    from .utils.question_importer import QuestionImporter



    



    if request.method == 'POST':



        form = QuestionImportForm(request.POST, request.FILES)



        if form.is_valid():



            file = form.cleaned_data['file']



            importer = QuestionImporter()



            try:



                result = importer.import_from_file(file)



                if result['success'] > 0:



                    messages.success(request, 'Operation successful')




                if result['skip'] > 0:



                    messages.warning(request, 'Warning')




                if result['errors']:



                    for error in result['errors'][:5]:



                        messages.error(request, error)



                return redirect('engineer_rpg:question_management')



            except Exception as e:



                messages.error(request, 'An error occurred')




    else:



        form = QuestionImportForm()



    



    return render(request, 'EngineerRPG/import_questions.html', {'profile': profile, 'form': form})











@login_required



def download_template(request, format='csv'):



    """Function docstring"""


    from .utils.question_importer import generate_template_csv, generate_template_excel



    



    if format == 'csv':



        response = HttpResponse(generate_template_csv(), content_type='text/csv; charset=utf-8-sig')



        response['Content-Disposition'] = 'attachment; filename="question_template.csv"'



    elif format == 'excel':



        output = generate_template_excel()



        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



        response['Content-Disposition'] = 'attachment; filename="question_template.xlsx"'



    else:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:question_management')



    



    return response











# ==================== ?��?蝞∠? ====================







@login_required



def team_dashboard(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    # Comment

    led_teams = Team.objects.filter(leader=request.user)



    



    # Get user latest record



    current_team = profile.current_team



    



    # Comment

    if led_teams.count() == 1:



        return redirect('engineer_rpg:team_detail', team_id=led_teams.first().id)



    



    # Comment

    if not led_teams.exists() and current_team:



        return redirect('engineer_rpg:team_detail', team_id=current_team.id)



    



    context = {



        'profile': profile,



        'led_teams': led_teams,



        'current_team': current_team,



    }



    



    return render(request, 'EngineerRPG/team_dashboard.html', context)











# Comment





@login_required



def guild_dashboard(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    # Comment

    announcements = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-created_at')[:5]



    



    # ?脣??梢?閮��?



    hot_posts = GuildPost.objects.filter(is_pinned=False).order_by('-views', '-created_at')[:5]



    



    # Comment

    teams = Team.objects.all().prefetch_related(



        'current_members__user',



        'current_members__character_class'



    )



    



    # ?脣??⊿?隡��??∴??芰��?����?��?



    free_members = UserProfile.objects.filter(



        current_team__isnull=True



    ).select_related('user', 'character_class')



    



    # 瑼Ｘ��?臬��?箇恣?���∴�����?潮＊蝷箇恣?�銝剖�����???



    is_manager = profile.role in ['OFFICER', 'MANAGER', 'ADMIN']



    



    context = {



        'profile': profile,



        'announcements': announcements,



        'hot_posts': hot_posts,



        'teams': teams,



        'free_members': free_members,



        'is_manager': is_manager,



    }



    



    return render(request, 'EngineerRPG/guild_dashboard.html', context)











@login_required



def guild_exchange_list(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    """Function docstring"""
    profile = get_or_create_user_profile(request.user)
    category = request.GET.get('category', 'ALL')

    # 獲取所有文章，但排除公告
    posts = GuildPost.objects.exclude(category='ANNOUNCEMENT')

    # ?�瞈�?��?



    if category != 'ALL':



        posts = posts.filter(category=category)



    



    # 蝵桅??��??����?��?蝡?



    pinned_posts = posts.filter(is_pinned=True)



    normal_posts = posts.filter(is_pinned=False)



    



    # ?��?



    from django.core.paginator import Paginator



    paginator = Paginator(normal_posts, 20)  # 瘥��? 20 蝭?



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    context = {



        'profile': profile,



        'pinned_posts': pinned_posts,



        'page_obj': page_obj,



        'current_category': category,



        'categories': [(code, name) for code, name in GuildPost.CATEGORY_CHOICES if code != 'ANNOUNCEMENT'],



    }



    



    return render(request, 'EngineerRPG/guild_exchange_list.html', context)











@login_required



def guild_post_create(request):



    """Function docstring"""




    profile = get_or_create_user_profile(request.user)



    



    # ?舀��?��? URL ?����?����?��?



    initial_category = request.GET.get('category')



    



    if request.method == 'POST':



        title = request.POST.get('title')



        content = request.POST.get('content')



        category = request.POST.get('category')



        



        # 甈��?瑼Ｘ�伐�����?�蝞�?����?臭誑?澆��??



        if category == 'ANNOUNCEMENT' and profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:



            messages.error(request, 'Only officers can post announcements')



            return redirect('engineer_rpg:guild_exchange_list')



            



        if title and content and category:



            post = GuildPost.objects.create(



                author=profile,



                title=title,



                content=content,  # 瘜冽?嚗��??�雿�??CKEditor ?�閬��?閮?HTML



                category=category



            )



            messages.success(request, 'Posted successfully')



            return redirect('engineer_rpg:guild_post_detail', post_id=post.id)



        else:



            messages.error(request, 'Please complete required fields')



            



    context = {



        'profile': profile,



        'categories': [(code, name) for code, name in GuildPost.CATEGORY_CHOICES if code != 'ANNOUNCEMENT'],



        'is_manager': profile.role in ['OFFICER', 'MANAGER', 'ADMIN'],



        'initial_category': initial_category,



    }



    



    return render(request, 'EngineerRPG/guild_post_create.html', context)




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
            messages.success(request, 'Announcement published successfully')
            return redirect('engineer_rpg:guild_dashboard')
        else:
            messages.error(request, '請填寫完整資訊')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/guild_announcement_create.html', context)


@login_required
def guild_announcement_edit(request, post_id):
    """編輯公告（僅限管理員）"""
    
    profile = get_or_create_user_profile(request.user)
    
    # 權限檢查：僅限公會幹部或公會長
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '只有公會幹部或公會長才能編輯公告')
        return redirect('engineer_rpg:guild_dashboard')
    
    # 獲取公告
    try:
        post = GuildPost.objects.get(id=post_id, category='ANNOUNCEMENT')
    except GuildPost.DoesNotExist:
        messages.error(request, '公告不存在')
        return redirect('engineer_rpg:guild_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        if title and content:
            post.title = title
            post.content = content
            post.save()
            messages.success(request, 'Operation successful')
            return redirect('engineer_rpg:guild_post_detail', post_id=post.id)
        else:
            messages.error(request, '請填寫完整資訊')
    
    context = {
        'profile': profile,
        'post': post,
    }
    
    return render(request, 'EngineerRPG/guild_announcement_edit.html', context)


@login_required
def guild_announcement_delete(request, post_id):
    """刪除公告（僅限管理員）"""
    
    profile = get_or_create_user_profile(request.user)
    
    # 權限檢查：僅限公會幹部或公會長
    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:
        messages.error(request, '只有公會幹部或公會長才能刪除公告')
        return redirect('engineer_rpg:guild_dashboard')
    
    # 獲取公告
    try:
        post = GuildPost.objects.get(id=post_id, category='ANNOUNCEMENT')
    except GuildPost.DoesNotExist:
        messages.error(request, '公告不存在')
        return redirect('engineer_rpg:guild_dashboard')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, '公告已刪除')
        return redirect('engineer_rpg:guild_dashboard')
    
    return redirect('engineer_rpg:guild_post_detail', post_id=post.id)


@login_required
def guild_announcement_list(request):
    """公告欄列表頁面"""
    
    profile = get_or_create_user_profile(request.user)
    
    # 獲取所有公告，按創建時間倒序排列
    announcements = GuildPost.objects.filter(category='ANNOUNCEMENT').order_by('-created_at')
    
    # 分頁
    from django.core.paginator import Paginator
    paginator = Paginator(announcements, 20)  # 每頁 20 則公告
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': profile,
        'page_obj': page_obj,
        'is_manager': profile.role in ['OFFICER', 'MANAGER', 'ADMIN'],
    }
    
    return render(request, 'EngineerRPG/guild_announcement_list.html', context)









@login_required



def guild_post_detail(request, post_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    post = get_object_or_404(GuildPost, id=post_id)



    



    # 憓��??�閬�??



    post.views += 1



    post.save()



    



    # ?��??��?



    if request.method == 'POST':



        content = request.POST.get('content')



        if content:



            GuildComment.objects.create(



                post=post,



                author=profile,



                content=content



            )



            messages.success(request, 'Posted successfully')



            return redirect('engineer_rpg:guild_post_detail', post_id=post.id)



    



    context = {



        'profile': profile,



        'post': post,



        'comments': post.comments.select_related('author__user'),



    }



    



    return render(request, 'EngineerRPG/guild_post_detail.html', context)















@login_required



def team_detail(request, team_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    team = get_object_or_404(Team, id=team_id)



    



    # Comment

    is_team_leader = team.leader == request.user



    is_manager = profile.role in ['OFFICER', 'MANAGER', 'ADMIN']



    



    if not (is_team_leader or is_manager):



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:index')



    



    # ?脣??����?�銵�?���嗅飛�?蝯梯?嚗��??恍??瘀?



    members = list(team.current_members.all().select_related('user', 'character_class'))



    



    # 撠��??瑕??交??∪?銵剁?憒��??����??profile嚗?



    try:



        leader_profile = UserProfile.objects.select_related('user', 'character_class').get(user=team.leader)



        # 瑼Ｘ��?����?臬�血歇�??冽??∪?銵其葉嚗����?��?銴��?



        if leader_profile not in members:



            members.insert(0, leader_profile)  # 撠��??瑟��?典?銵冽??����



    except UserProfile.DoesNotExist:



        pass  # 憒��??���瑟���? profile嚗�頝�??



    



    member_stats = []



    for member in members:



        # Comment

        # 計算應有總技能數（包含 ROOT 與該職業專有的技能）
        total_skills = SkillNode.objects.filter(
            Q(character_class=member.character_class) | Q(character_class__isnull=True)
        ).count()



        completed_skills = UserSkill.objects.filter(



            user_profile=member,



            status='COMPLETED'



        ).count()



        skill_completion = (completed_skills / total_skills * 100) if total_skills > 0 else 0



        



        # Comment

        recent_trials = TrialRecord.objects.filter(



            user_profile=member



        ).order_by('-completed_at')[:5]



        



        # 閮��?閰衣?蝯梯?



        trial_stats = TrialRecord.objects.filter(user_profile=member).aggregate(



            total_trials=Count('id'),



            passed_trials=Count('id', filter=Q(is_passed=True)),



            avg_score=Avg('score')



        )



        



        member_stats.append({



            'member': member,



            'skill_completion': round(skill_completion, 1),



            'completed_skills': completed_skills,



            'total_skills': total_skills,



            'recent_trials': recent_trials,



            'trial_stats': trial_stats,



        })



    



    # 計算平均等級
    avg_level = round(sum(m.level for m in members) / len(members), 1) if members else 0

    context = {



        'profile': profile,



        'team': team,



        'member_stats': member_stats,
        'avg_level': avg_level,



    }



    



    return render(request, 'EngineerRPG/team_detail.html', context)











@login_required



def team_member_detail(request, team_id, member_id):



    """Function docstring"""




    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    team = get_object_or_404(Team, id=team_id)



    member = get_object_or_404(UserProfile, id=member_id)



    



    # Comment

    is_team_leader = team.leader == request.user



    is_manager = profile.role in ['OFFICER', 'MANAGER', 'ADMIN']



    



    if not (is_team_leader or is_manager):



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:index')



    



    # 蝣箄?閰脫??∪惇?潭迨?��?



    if member.current_team != team:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    # 獲獲該成員應有的所有技能節點（ROOT + 專屬職業技能）
    applicable_skill_nodes = SkillNode.objects.filter(
        Q(character_class=member.character_class) | Q(character_class__isnull=True)
    )
    
    # 獲取已有的使用者技能記錄
    existing_user_skills = UserSkill.objects.filter(
        user_profile=member,
        skill_node__in=applicable_skill_nodes
    ).select_related('skill_node')
    
    # 建立一個 mapping 方便查找
    user_skill_map = {us.skill_node_id: us for us in existing_user_skills}
    
    # 組合最終要顯示的技能列表（保留 UserSkill 物件的結構）
    display_skills = []
    for node in applicable_skill_nodes:
        if node.id in user_skill_map:
            display_skills.append(user_skill_map[node.id])
        else:
            # 如果還沒有記錄，建立一個虛擬的 UserSkill 物件用於範本顯示
            virtual_skill = UserSkill(
                user_profile=member,
                skill_node=node,
                status='LOCKED',
                progress=0
            )
            display_skills.append(virtual_skill)



    



    # ?脣?閰衣?閮��?



    trial_records = TrialRecord.objects.filter(



        user_profile=member



    ).select_related('trial').order_by('-completed_at')



    



    # ?��?



    paginator = Paginator(trial_records, 10)



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    context = {



        'profile': profile,



        'team': team,



        'member': member,



        'skills': display_skills,



        'page_obj': page_obj,



    }



    



    return render(request, 'EngineerRPG/team_member_detail.html', context)











@login_required



def member_profile_detail(request, member_id):



    """Member Profile Detail"""



    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    # Comment

    if profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:index')



    



    member = get_object_or_404(UserProfile, id=member_id)



    



    # Comment

    skills = UserSkill.objects.filter(user_profile=member).select_related('skill_node')



    



    # ?脣?閰衣?閮��?



    trial_records = TrialRecord.objects.filter(



        user_profile=member



    ).select_related('trial').order_by('-completed_at')



    



    # ?��?



    paginator = Paginator(trial_records, 10)



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    context = {



        'profile': profile,



        'team': member.current_team,  # ?航��??None



        'member': member,



        'skills': skills,



        'page_obj': page_obj,



    }



    



    return render(request, 'EngineerRPG/team_member_detail.html', context)











@login_required



def team_manage_members(request, team_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    team = get_object_or_404(Team, id=team_id)



    



    # 瑼Ｘ�交���?嚗����?��??瑕�臭誑蝞�??



    if team.leader != request.user:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    # ?脣??嗅??����



    current_members = UserProfile.objects.filter(current_team=team).select_related('user', 'character_class')



    



    # Comment

    # Comment

    available_users = UserProfile.objects.filter(



        current_team__isnull=True



    ).exclude(



        user=team.leader



    ).select_related('user', 'character_class')



    



    context = {



        'profile': profile,



        'team': team,



        'current_members': current_members,



        'available_users': available_users,



    }



    



    return render(request, 'EngineerRPG/team_manage_members.html', context)











@login_required



def team_add_member(request, team_id):



    """Function docstring"""


    if request.method != 'POST':



        return redirect('engineer_rpg:team_manage_members', team_id=team_id)



    



    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    team = get_object_or_404(Team, id=team_id)



    



    # 瑼Ｘ�交���?



    if team.leader != request.user:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    member_id = request.POST.get('member_id')



    if not member_id:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_manage_members', team_id=team_id)



    



    try:



        member_profile = UserProfile.objects.get(id=member_id)



        



        # 瑼Ｘ��?臬�血歇�??��?



        if member_profile.current_team:



            messages.error(request, 'An error occurred')




            return redirect('engineer_rpg:team_manage_members', team_id=team_id)



        



        # ?湔�� UserProfile



        member_profile.current_team = team



        member_profile.save()



        



        # ?萄遣 TeamMembership 閮��?



        TeamMembership.objects.create(



            user_profile=member_profile,



            team=team,



            is_current=True



        )



        



        messages.success(request, 'Operation successful')




        



    except UserProfile.DoesNotExist:



        messages.error(request, 'User does not exist')



    



    return redirect('engineer_rpg:team_manage_members', team_id=team_id)











@login_required



def team_remove_member(request, team_id, member_id):



    """Function docstring"""


    if request.method != 'POST':



        return redirect('engineer_rpg:team_manage_members', team_id=team_id)



    



    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    team = get_object_or_404(Team, id=team_id)



    



    # 瑼Ｘ�交���?



    if team.leader != request.user:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    try:



        member_profile = UserProfile.objects.get(id=member_id)



        



        # 瑼Ｘ��?臬��?冽迨?��?銝?



        if member_profile.current_team != team:



            messages.error(request, 'An error occurred')




            return redirect('engineer_rpg:team_manage_members', team_id=team_id)



        



        # ?湔�� UserProfile



        member_profile.current_team = None



        member_profile.save()



        



        # ?湔�� TeamMembership 閮��?



        from django.utils import timezone



        membership = TeamMembership.objects.filter(



            user_profile=member_profile,



            team=team,



            is_current=True



        ).first()



        



        if membership:



            membership.is_current = False



            membership.left_at = timezone.now()



            membership.leave_reason = '?���瑞宏���'



            membership.save()



        



        messages.success(request, 'Operation successful')




        



    except UserProfile.DoesNotExist:



        messages.error(request, 'User does not exist')



    



    return redirect('engineer_rpg:team_manage_members', team_id=team_id)











@login_required



def item_inventory(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if not profile:



        return redirect('engineer_rpg:index')



    



    # ?脣?銝血?憿��???



    user_items = UserItem.objects.filter(user_profile=profile).select_related('item').order_by('item__item_type', 'item__rarity')



    



    # ?��??��?蝯?



    basic_items = user_items.filter(item__item_type='BASIC')



    advanced_items = user_items.filter(item__item_type='ADVANCED')



    rare_items = user_items.filter(item__item_type='RARE')



    



    # 撘瑕??瑁遘?賊?



    scroll, _ = EnhancementScroll.objects.get_or_create(user_profile=profile)



    scroll_count = scroll.quantity



    



    context = {



        'profile': profile,



        'basic_items': basic_items,



        'advanced_items': advanced_items,



        'rare_items': rare_items,



        'scroll_count': scroll_count,



    }



    return render(request, 'EngineerRPG/inventory.html', context)











def _seed_default_items():



    """Seed Default Items"""



    if Item.objects.exists():



        return



        



    items_data = [



        # Basic



        {'name': 'Item', 'item_type': 'BASIC', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        {'name': 'Item', 'item_type': 'BASIC', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        {'name': 'Item', 'item_type': 'BASIC', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        # Advanced



        {'name': 'Item', 'item_type': 'ADVANCED', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        {'name': 'Item', 'item_type': 'ADVANCED', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        {'name': 'Item', 'item_type': 'ADVANCED', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        # Rare



        {'name': 'Item', 'item_type': 'RARE', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        {'name': 'Item', 'item_type': 'RARE', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




        {'name': 'Item', 'item_type': 'RARE', 'effect_type': 'BASIC', 'effect_value': 0, 'rarity': 'COMMON', 'desc': 'Item description'},




    ]



    



    for item in items_data:



        Item.objects.create(



            name=item['name'],



            item_type=item['item_type'],



            effect_type=item['effect_type'],



            effect_value=item['effect_value'],



            rarity=item['rarity'],



            description=item['desc']



        )







@login_required



def api_consume_item(request, user_item_id):



    """Function docstring"""


    if request.method != 'POST':



        return JsonResponse({'error': 'Invalid method'}, status=405)



    



    profile = get_or_create_user_profile(request.user)



    



    try:



        import json



        user_item = UserItem.objects.get(id=user_item_id, user_profile=profile)



        



        if user_item.quantity < 1:



            return JsonResponse({'error': 'Not enough items'}, status=400)





        



        # 皜��??賊?



        user_item.quantity -= 1



        user_item.save()



        



        return JsonResponse({








            'remaining_quantity': user_item.quantity,



            'item_name': user_item.item.name



        })



        



    except UserItem.DoesNotExist:



        return JsonResponse({'error': 'Item not found'}, status=404)






    except Exception as e:



        return JsonResponse({'success': False, 'error': str(e)}, status=500)



from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def equipment_inventory(request):
    """個人裝備欄"""
    profile = get_or_create_user_profile(request.user)
    
    # Get all equipment items
    all_equipment = Equipment.objects.all().order_by('equipment_type', 'tier')
    
    # Get or create UserEquipment for each item
    user_equipment_list = []
    for equipment in all_equipment:
        user_equipment, created = UserEquipment.objects.get_or_create(
            user_profile=profile,
            equipment=equipment,
            defaults={
                'enhancement_level': 0,
                'is_equipped': False,
            }
        )
        
        # Check unlock status
        is_unlocked = profile.level >= equipment.required_level
        if equipment.required_skill:
            is_unlocked = is_unlocked and equipment.required_skill in profile.unlocked_skills.all()
        
        user_equipment_list.append({
            'user_equipment': user_equipment,
            'is_unlocked': is_unlocked,
        })
    
    # Separate by type
    helmets = [item for item in user_equipment_list if item['user_equipment'].equipment.equipment_type == 'HELMET']
    armors = [item for item in user_equipment_list if item['user_equipment'].equipment.equipment_type == 'ARMOR']
    boots = [item for item in user_equipment_list if item['user_equipment'].equipment.equipment_type == 'BOOTS']
    tools = [item for item in user_equipment_list if item['user_equipment'].equipment.equipment_type == 'TOOL']
    
    # Get currently equipped
    equipped = {
        'helmet': profile.equipped_helmet,
        'armor': profile.equipped_armor,
        'boots': profile.equipped_boots,
        'tool_1': profile.equipped_tool_1,
        'tool_2': profile.equipped_tool_2,
        'tool_3': profile.equipped_tool_3,
        'tool_4': profile.equipped_tool_4,
        'tool_5': profile.equipped_tool_5,
    }
    
    context = {
        'profile': profile,
        'helmets': helmets,
        'armors': armors,
        'boots': boots,
        'tools': tools,
        'equipped': equipped,
        'enhancement_tickets': profile.enhancement_tickets,
    }
    
    return render(request, 'EngineerRPG/equipment_inventory.html', context)

@login_required
def manage_questions(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

@login_required
def manage_skill_tree(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

@login_required
def unequip_item(request, user_equipment_id):
    """Unequip an item"""
    profile = get_or_create_user_profile(request.user)
    
    try:
        user_equipment = UserEquipment.objects.get(
            id=user_equipment_id,
            user_profile=profile,
            is_equipped=True
        )
        
        equipment_type = user_equipment.equipment.equipment_type
        
        if equipment_type == 'HELMET':
            profile.equipped_helmet = None
        elif equipment_type == 'ARMOR':
            profile.equipped_armor = None
        elif equipment_type == 'BOOTS':
            profile.equipped_boots = None
        elif equipment_type == 'TOOL':
            for i in range(1, 6):
                slot_field = f'equipped_tool_{i}'
                if getattr(profile, slot_field) == user_equipment:
                    setattr(profile, slot_field, None)
                    break
        
        user_equipment.is_equipped = False
        user_equipment.save()
        
        # Save profile first to update equipped relation
        profile.save()
        profile.update_stats()
        
        messages.success(request, f'Successfully unequipped {user_equipment.equipment.name}!')
        
    except UserEquipment.DoesNotExist:
        messages.error(request, 'Equipment not found or not equipped!')
    
    return redirect('engineer_rpg:equipment_inventory')





@login_required
def delete_team(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

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
def enhance_equipment(request, user_equipment_id):
    """Enhance equipment"""
    profile = get_or_create_user_profile(request.user)
    
    try:
        user_equipment = UserEquipment.objects.get(
            id=user_equipment_id,
            user_profile=profile
        )
        
        if user_equipment.enhancement_level >= user_equipment.equipment.max_enhancement:
            messages.error(request, 'Equipment is at maximum enhancement level!')
            return redirect('engineer_rpg:equipment_inventory')
        
        if profile.enhancement_tickets < 1:
            messages.error(request, 'Not enough enhancement tickets!')
            return redirect('engineer_rpg:equipment_inventory')
        
        profile.enhancement_tickets -= 1
        
        user_equipment.enhancement_level += 1
        user_equipment.save()
        
        if user_equipment.is_equipped:
            profile.update_stats()
        
        profile.save()
        
        messages.success(request, 
            f'Successfully enhanced {user_equipment.equipment.name} to +{user_equipment.enhancement_level}!')
        
    except UserEquipment.DoesNotExist:
        messages.error(request, 'Equipment not found!')
    
    return redirect('engineer_rpg:equipment_inventory')

@login_required
def equip_item(request, user_equipment_id):
    """Equip an item"""
    profile = get_or_create_user_profile(request.user)
    
    try:
        user_equipment = UserEquipment.objects.get(
            id=user_equipment_id,
            user_profile=profile
        )
        
        # Check unlock status
        equipment = user_equipment.equipment
        is_unlocked = profile.level >= equipment.required_level
        if equipment.required_skill:
            is_unlocked = is_unlocked and equipment.required_skill in profile.unlocked_skills.all()
            
        if not is_unlocked:
            messages.error(request, f'Equipment {equipment.name} is locked! Level {equipment.required_level} required.')
            return redirect('engineer_rpg:equipment_inventory')
        
        equipment_type = equipment.equipment_type
        
        # Equip to appropriate slot
        if equipment_type == 'HELMET':
            if profile.equipped_helmet:
                profile.equipped_helmet.is_equipped = False
                profile.equipped_helmet.save()
            profile.equipped_helmet = user_equipment
            
        elif equipment_type == 'ARMOR':
            if profile.equipped_armor:
                profile.equipped_armor.is_equipped = False
                profile.equipped_armor.save()
            profile.equipped_armor = user_equipment
            
        elif equipment_type == 'BOOTS':
            if profile.equipped_boots:
                profile.equipped_boots.is_equipped = False
                profile.equipped_boots.save()
            profile.equipped_boots = user_equipment
            
        elif equipment_type == 'TOOL':
            slot = request.POST.get('slot', '1')
            slot_field = f'equipped_tool_{slot}'
            
            old_tool = getattr(profile, slot_field)
            if old_tool:
                old_tool.is_equipped = False
                old_tool.save()
            
            setattr(profile, slot_field, user_equipment)
        
        user_equipment.is_equipped = True
        user_equipment.save()
        
        # Save profile first to update equipped relation
        profile.save()
        profile.update_stats()
        
        messages.success(request, f'Successfully equipped {user_equipment.equipment.name}!')
        
    except UserEquipment.DoesNotExist:
        messages.error(request, 'Equipment not found!')
    
    return redirect('engineer_rpg:equipment_inventory')


@login_required
def course_study(request, course_id):
    """View course content"""
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    progress, created = UserCourseProgress.objects.get_or_create(user_profile=profile, course=course)
    
    context = {
        'profile': profile,
        'course': course,
        'progress': progress,
    }
    return render(request, 'EngineerRPG/course_study.html', context)


@login_required
def course_exam(request, course_id):
    """Take course exam"""
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    questions = course.questions.all().order_by('?')
    if not questions.exists():
        messages.warning(request, "此課程沒有考試題目，請聯繫管理員。")
        return redirect('engineer_rpg:course_study', course_id=course.id)
    
    # Calculate points per question for display
    total_questions = questions.count()
    points_per_question = round(100 / total_questions, 1) if total_questions > 0 else 0

    context = {
        'profile': profile,
        'course': course,
        'questions': questions,
        'points_per_question': points_per_question,
    }
    return render(request, 'EngineerRPG/course_exam.html', context)


@login_required
def submit_course_exam(request, course_id):
    """Submit course exam"""
    if request.method != 'POST':
        return redirect('engineer_rpg:course_study', course_id=course_id)
        
    profile = get_or_create_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    questions = course.questions.all()
    
    score = 0
    total_questions = questions.count()
    correct_count = 0
    
    incorrect_questions = []
    
    for question in questions:
        user_answer = request.POST.get(f'question_{question.id}')
        
        # Determine if correct (assuming single choice for now based on template)
        is_correct = False
        if user_answer and user_answer == question.correct_answer:
            is_correct = True
            correct_count += 1
            
        if not is_correct:
            # Get readable text
            user_option_text = question.options.get(user_answer, '未作答') if user_answer else '未作答'
            correct_option_text = question.options.get(question.correct_answer, '')
            
            incorrect_questions.append({
                'question': question,
                'user_answer': user_answer,
                'user_option_text': user_option_text,
                'correct_answer': question.correct_answer,
                'correct_option_text': correct_option_text,
            })
            
    if total_questions > 0:
        score = int((correct_count / total_questions) * 100)
    else:
        score = 100 
        
    is_passed = score >= course.passing_score
    
    # Update progress
    progress, _ = UserCourseProgress.objects.get_or_create(user_profile=profile, course=course)
    
    # Update score if higher
    if score > progress.score:
        progress.score = score
        
    if is_passed and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save()
        
        # Check skill completion logic
        for skill in course.skill_nodes.all():
            all_courses = skill.courses.all()
            completed_courses = UserCourseProgress.objects.filter(
                user_profile=profile,
                course__in=all_courses,
                is_completed=True
            ).count()
            
            if all_courses.count() > 0:
                skill_progress_percent = int((completed_courses / all_courses.count()) * 100)
                
                user_skill, _ = UserSkill.objects.get_or_create(user_profile=profile, skill_node=skill)
                user_skill.progress = skill_progress_percent
                
                if skill_progress_percent == 100 and user_skill.status != 'COMPLETED':
                    user_skill.status = 'COMPLETED'
                    user_skill.completed_at = timezone.now()
                    
                    profile.experience += skill.exp_reward
                    profile.save()
                    messages.success(request, f'恭喜！習得技能「{skill.name}」，獲得 {skill.exp_reward} 經驗值！')
                
                user_skill.save()
    else:
        progress.save()
        
    context = {
        'profile': profile,
        'course': course,
        'score': score,
        'is_passed': is_passed,
        'correct_count': correct_count,
        'total_questions': total_questions,
        'passing_score': course.passing_score,
        'incorrect_questions': incorrect_questions,
    }
    return render(request, 'EngineerRPG/course_result.html', context)


@login_required
def api_auto_distribute_xp(request):
    """自動分配剩餘經驗值"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    profile = get_or_create_user_profile(request.user)
    if profile.role != 'ADMIN':
         return JsonResponse({'error': 'Permission denied'}, status=403)
         
    try:
        data = json.loads(request.body)
        dist_type = data.get('type')
        class_code = data.get('class_code')
        
        target_xp = 0
        skills = []
        
        if dist_type == 'ROOT':
            target_xp = 4500
            skills = list(SkillNode.objects.filter(node_type='ROOT'))
        elif dist_type == 'CORE':
            target_xp = 118000
            skills = list(SkillNode.objects.filter(node_type='CORE', character_class__code=class_code))
        else:
            return JsonResponse({'error': 'Invalid type'}, status=400)
            
        if not skills:
            return JsonResponse({'error': 'No skills found'}, status=404)
            
        # Calculate current total
        current_total = sum(s.exp_reward for s in skills)
        gap = target_xp - current_total
        
        if gap <= 0:
            return JsonResponse({'status': 'success', 'message': '已額滿或超標，無需分配'})
            
        # Distribute gap
        count = len(skills)
        base_add = gap // count
        remainder = gap % count
        
        for i, skill in enumerate(skills):
            skill.exp_reward += base_add
            if i < remainder:
                skill.exp_reward += 1
            skill.save()
            
        return JsonResponse({'status': 'success', 'message': f'已將 {gap} XP 分配給 {count} 個技能'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
def delete_question(request, question_id):
    """Delete a question"""
    profile = get_or_create_user_profile(request.user)
    if profile.role not in ['ADMIN', 'MANAGER', 'OFFICER']:
        messages.error(request, '權限不足')
        return redirect('engineer_rpg:question_management')
        
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, '題目已刪除')
        
    return redirect('engineer_rpg:question_management')
