from django.shortcuts import render, redirect, get_object_or_404



from django.contrib.auth.decorators import login_required



from django.views.decorators.csrf import csrf_exempt



from django.contrib.auth import login, authenticate, logout



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















from .forms import (



    QuestionForm, QuestionImportForm, SkillNodeForm, CourseForm, UserLoginForm,



    UserRegistrationForm, UserProfileEditForm



)







# ==================== 頛?賢? ====================







def get_or_create_user_profile(user):



    """Get or create user profile"""


    try:



        return user.rpg_profile



    except UserProfile.DoesNotExist:



        # 憒?瘝?瑼?嚗??身摰???



        return None











def check_skill_unlocked(user_profile, skill_node):



    """Check if skill is unlocked"""


    # 瑼Ｘ蝑??



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



    return True  # 瘝??蔭??踝??湔閫??























# ==================== 閮餃????====================







def user_register(request):



    """User Registration"""



    if request.user.is_authenticated:



        return redirect('engineer_rpg:dashboard')



    



    if request.method == 'POST':



        form = UserRegistrationForm(request.POST)



        if form.is_valid():



            user = form.save()



            # ??隤?敺垢



            # ??隤?敺垢 - ?Ⅱ?? ModelBackend 隞仿????蝡航?蝒?



            user.backend = 'django.contrib.auth.backends.ModelBackend'



            login(request, user)



            messages.success(request, 'Operation successful')




            return redirect('engineer_rpg:dashboard')



    else:



        form = UserRegistrationForm()



    



    context = {



        'form': form,



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











# ==================== 擐???銵冽 ====================







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



    



    # 瘥?舀



    today = timezone.now().date()



    daily_trials = Trial.objects.filter(is_daily=True, is_active=True, refresh_date=today)



    



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



                # 撽???蝣?



                if not user.check_password(old_password):



                    form.add_error('old_password', '??蝣潔?甇?Ⅱ')



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



                # 憒??????豢??身?剖?"嚗vatar_index ??> 0



                avatar_index = form.cleaned_data.get('avatar_index')



                if avatar_index and int(avatar_index) > 0:



                    profile.avatar_index = int(avatar_index)



                    # Comment

                    # ?ㄐ?豢?撠?avatar_image 閮剔 None嚗誑靘?get_avatar_url ?芸?雿輻 index



                    profile.avatar_image = None 



                    



                # 憒????單??嚗?閬? (?芸?蝝?擃?



                if form.cleaned_data.get('avatar_image'):



                    profile.avatar_image = form.cleaned_data['avatar_image']



                    profile.avatar_index = 0 # ?蔭蝝Ｗ?



                



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



    



    # 摨?? JSON 靘?蝡臭蝙??



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



    



    # 瑼Ｘ?臬閫??



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



        



        # ?脣?蝬???



        profile.experience += skill.exp_reward



        



        # 瑼Ｘ?臬??



        while profile.experience >= profile.experience_to_next_level() and profile.level < 100:



            profile.experience -= profile.experience_to_next_level()



            profile.level += 1



            messages.success(request, 'Operation successful')




        



        profile.save()



        



        messages.success(request, 'Operation successful')




    



    return redirect('engineer_rpg:skill_tree')











# ==================== ?蝟餌絞 ====================







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



    



    # ?脣?隞???乩遙??



    from .models import DailyTrialTask, DailyTrialProgress



    from .utils import generate_daily_tasks



    



    daily_tasks = DailyTrialTask.objects.filter(date=today, is_active=True).order_by('task_number')



    



    # 憒?隞瘝?隞餃?嚗????



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



        



        task_progress_list.append({



            'task': task,



            'progress': progress,



            'question_count': task.questions.count(),



        })



    



    # 閮?頝?瑟????



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



    }



    



    return render(request, 'EngineerRPG/daily_trial.html', context)











@login_required



def trial_detail(request, trial_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # 瑼Ｘ?臬蝚血?璇辣



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



    



    # ?冽??賢?憿



    all_questions = list(trial.questions.filter(is_active=True))



    selected_questions = random.sample(all_questions, min(trial.question_count, len(all_questions)))



    



    # ?脣???session



    request.session['trial_id'] = trial.id



    request.session['trial_questions'] = [q.id for q in selected_questions]



    request.session['trial_start_time'] = timezone.now().isoformat()



    request.session['trial_answers'] = {}



    request.session['current_question_index'] = 0  # ?啣?嚗???桃揣撘?



    



    



    # ????HP/MP



    # ?箇? HP ?箏???3嚗????憭?蝞?



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



        'question': current_question,  # ?寧?桅?



        'current_index': 0,



        'total_questions': len(selected_questions),



        'base_hp': base_hp,  # ?箇? HP (3)



        'initial_hp': total_hp,  # 蝮?HP (?怨?????



        'initial_mp': initial_mp,



        'heart_range': range(1, max(total_hp, 5) + 1),  # ?????賊?



        'user_items': UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item'),



    }



    



    return render(request, 'EngineerRPG/trial_exam.html', context)











@login_required



def start_daily_trial(request, task_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    from .models import DailyTrialTask, DailyTrialProgress



    from .utils import get_or_create_daily_progress



    



    # ?脣?瘥隞餃?



    daily_task = get_object_or_404(DailyTrialTask, id=task_id)



    



    # 瑼Ｘ?臬?箔??乩遙??



    today = timezone.now().date()



    if daily_task.date != today:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:daily_trial_list')



    



    # Comment

    progress = get_or_create_daily_progress(profile, daily_task)



    



    # 憒?撌脣???銝???



    if progress.is_completed:



        messages.warning(request, 'Warning')




        return redirect('engineer_rpg:daily_trial_list')



    



    # 憒? HP 甇賊嚗??賜匱蝥?



    if progress.current_hp <= 0:



        messages.error(request, 'HP exhausted, trial failed')



        return redirect('engineer_rpg:daily_trial_list')



    



    # ?脣?隞餃?????



    questions = list(daily_task.questions.all())



    



    # 瑼Ｘ?臬????



    if not questions:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:daily_trial_list')



    



    # ?脣???session



    request.session['daily_task_id'] = daily_task.id



    request.session['trial_questions'] = [q.id for q in questions]



    request.session['trial_start_time'] = timezone.now().isoformat()



    request.session['current_question_index'] = 0



    



    # Comment

    if not progress.started_at:



        progress.started_at = timezone.now()



        progress.save()



    



    # Comment

    current_question = questions[0] if questions else None



    



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



    }



    



    return render(request, 'EngineerRPG/trial_exam.html', context)











@login_required



def submit_answer(request, trial_id):



    """Submit Answer"""



    if request.method != 'POST':



        return JsonResponse({'error': 'Invalid request method'}, status=400)



    



    profile = get_or_create_user_profile(request.user)



    trial = get_object_or_404(Trial, id=trial_id)



    



    # ?脣??嗅?憿



    question_ids = request.session.get('trial_questions', [])



    current_index = request.session.get('current_question_index', 0)



    



    if current_index >= len(question_ids):



        return JsonResponse({'error': 'No more questions'}, status=400)



    



    question = get_object_or_404(Question, id=question_ids[current_index])



    



    # Get user answer



    user_answer = request.POST.get('answer', '')



    



    # ?斗撠



    correct_answer = question.correct_answer



    is_correct = False



    



    if question.question_type == 'MULTIPLE':



        user_answer_list = request.POST.getlist('answer')



        is_correct = set(user_answer_list) == set(correct_answer)



    else:



        is_correct = user_answer == str(correct_answer)



    



    # ?湔 Session 銝剔?蝑?閮?



    trial_answers = request.session.get('trial_answers', {})



    trial_answers[str(question.id)] = {



        'user_answer': user_answer,



        'is_correct': is_correct,



    }



    request.session['trial_answers'] = trial_answers



    



    # 瑼Ｘ?臬?箸??乩遙??



    daily_task_id = request.session.get('daily_task_id')



    if daily_task_id:



        # 瘥隞餃?嚗??DailyTrialProgress



        from .models import DailyTrialTask, DailyTrialProgress



        try:



            daily_task = DailyTrialTask.objects.get(id=daily_task_id)



            progress = DailyTrialProgress.objects.get(



                user_profile=profile,



                daily_task=daily_task



            )



            



            # ?? HP嚗????荔?



            if not is_correct:



                damage = 10
                if question.difficulty == 'C': damage = 5
                elif question.difficulty in ['A', 'S']: damage = 15
                progress.current_hp = max(0, progress.current_hp - damage)



                progress.save()



            



            current_hp = progress.current_hp



            



            # ?湔蝑?閮?



            if not progress.answers:



                progress.answers = {}



            progress.answers[str(question.id)] = {



                'user_answer': user_answer,



                'is_correct': is_correct,



            }



            progress.save()



            



        except (DailyTrialTask.DoesNotExist, DailyTrialProgress.DoesNotExist):



            # If database fails, use session



            current_hp = request.session.get('trial_hp', 3)



            if not is_correct:



                damage = 10
                if question.difficulty == 'C': damage = 5
                elif question.difficulty in ['A', 'S']: damage = 15
                current_hp = max(0, current_hp - damage)



                request.session['trial_hp'] = current_hp



    else:



        # Comment

        current_hp = request.session.get('trial_hp', 3)



        if not is_correct:



            damage = 10
            if question.difficulty == 'C': damage = 5
            elif question.difficulty in ['A', 'S']: damage = 15
            current_hp = max(0, current_hp - damage)



            request.session['trial_hp'] = current_hp



    



    # ?斗?臬 Game Over



    is_game_over = current_hp <= 0



    



    # 餈? JSON ??



    response_data = {



        'is_correct': is_correct,



        'correct_answer': correct_answer,



        'explanation': question.explanation,



        'remaining_hp': current_hp,



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



    



    # ?脣?憿?”



    question_ids = request.session.get('trial_questions', [])



    current_index = request.session.get('current_question_index', 0)



    



    # 憓?蝝Ｗ?



    next_index = current_index + 1



    



    # 瑼Ｘ?臬??銝?憿?



    if next_index >= len(question_ids):



        # 瘝?銝?憿?嚗???蝞???



        return redirect('engineer_rpg:finish_trial', trial_id=trial_id)



    



    # ?湔蝝Ｗ?



    request.session['current_question_index'] = next_index



    



    # ?脣?銝?憿?



    next_question_obj = get_object_or_404(Question, id=question_ids[next_index])



    



    # 瑼Ｘ?臬?箸??乩遙??



    daily_task_id = request.session.get('daily_task_id')



    if daily_task_id:



        # 瘥隞餃?嚗? DailyTrialProgress ?脣? HP/MP



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



    



    base_hp = 3



    



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



    



    # ?脣?蝑?



    question_ids = request.session.get('trial_questions', [])



    questions = Question.objects.filter(id__in=question_ids)



    



    # 閮??



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



    



    # 閮???



    start_time = timezone.datetime.fromisoformat(request.session.get('trial_start_time'))



    time_spent = (timezone.now() - start_time).total_seconds()



    



    # 閮????HP



    # ?脣??? HP (憒?瘝?閮???閮剔 3)



    initial_hp = request.session.get('trial_hp', 3)



    wrong_answers = total_count - correct_count



    remaining_hp = max(0, initial_hp - wrong_answers)



    



    score = int((correct_count / total_count) * 100)



    



    # ??璇辣嚗???>= 60 銝?HP > 0



    is_passed = score >= 60 and remaining_hp > 0



    



    # 瑼Ｘ?臬?箏銝?????



    is_dungeon_repeat = False



    if trial.trial_type == 'DUNGEON':



        # Comment

        if TrialRecord.objects.filter(user_profile=profile, trial=trial, is_passed=True).exists():



            is_dungeon_repeat = True



            



    # 閮?蝬???



    exp_reward = trial.exp_reward



    if is_dungeon_repeat:



        exp_reward = max(1, int(exp_reward * 0.01))  # ? 1% 蝬???



            



    # 撱箇?閮?



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



    



    # 瑼Ｘ?臬?箸??乩遙??



    daily_task_id = request.session.get('daily_task_id')



    if daily_task_id:



        from .models import DailyTrialTask, DailyTrialProgress



        try:



            daily_task = DailyTrialTask.objects.get(id=daily_task_id)



            progress = DailyTrialProgress.objects.get(



                user_profile=profile,



                daily_task=daily_task



            )



            



            # 璅??箏歇摰?



            progress.is_completed = True



            progress.is_passed = is_passed



            progress.completed_at = timezone.now()



            progress.save()



            



            # ? TrialRecord ??DailyTrialTask



            record.daily_task = daily_task



            record.save()



            



        except (DailyTrialTask.DoesNotExist, DailyTrialProgress.DoesNotExist):



            pass



    



    # 憒???嚗策鈭???



    if is_passed:



        profile.experience += exp_reward



        



        # 瑼Ｘ??



        while profile.experience >= profile.experience_to_next_level():



            profile.experience -= profile.experience_to_next_level()



            profile.level += 1



            



            # Comment

            # Fixed garbled f-string




            



            # MP 瘥???



            msg_parts.append('?憭?MP +20')



            



            # HP 瘥?10 蝝???



            if profile.level % 10 == 0:



                msg_parts.append('?憭?HP +1')



                



            messages.success(request, 'Operation successful')



        



        profile.update_stats()  # 蝣箔?撅祆扳??



        



        # ?寞??璈嚗??????銝?嚗??銝?嚗?



        if not is_dungeon_repeat:



            # ??



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




            



            # 撘瑕??瑁遘?嚗??蝝?璇臬?憓?嚗?



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




    



    # 皜 session



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











# ==================== ??蝟餌絞 ====================







@login_required



def apply_promotion(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    # 瑼Ｘ?臬??撖拇?隢?



    pending_request = PromotionRequest.objects.filter(



        applicant=profile,



        status='PENDING'



    ).first()



    



    if pending_request:



        messages.warning(request, 'Warning')




        return redirect('engineer_rpg:dashboard')



    



    # Comment

    required_skills = SkillNode.objects.filter(



        character_class=profile.character_class,



        node_type='CORE'



    )



    completed_skills = UserSkill.objects.filter(



        user_profile=profile,



        skill_node__in=required_skills,



        status='COMPLETED'



    ).count()



    



    if completed_skills < required_skills.count():



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:skill_tree')



    



    # 撱箇????唾?



    target_level = profile.level + 1



    promotion_request = PromotionRequest.objects.create(



        applicant=profile,



        current_level=profile.level,



        target_level=target_level,



        status='PENDING'



    )



    



    messages.success(request, 'Operation successful')




    return redirect('engineer_rpg:dashboard')











@login_required



def promotion_trial(request, request_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    promotion_request = get_object_or_404(PromotionRequest, id=request_id, applicant=profile)



    



    # ?ㄐ?臭誑閮剛??寞????岫??



    # Comment

    return redirect('engineer_rpg:daily_trial_list')











# ==================== ??璁?====================







@login_required



def leaderboard(request):



    """Trial Attempts"""



    profile = get_or_create_user_profile(request.user)



    



    # 蝑???



    level_ranking = UserProfile.objects.all().order_by('-level', '-experience')[:50]



    



    # 閰衣???嚗?梧?



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











# ==================== 銝餌恣隞 ====================







@login_required



def manager_dashboard(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    # 敺祟?貊隢?



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



    



    # ??



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



def approve_request(request, request_id):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role not in ['MANAGER', 'ADMIN']:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    promotion_request = get_object_or_404(PromotionRequest, id=request_id)



    



    if promotion_request.status == 'PENDING':



        promotion_request.status = 'APPROVED'



        promotion_request.reviewer = request.user



        promotion_request.reviewed_at = timezone.now()



        promotion_request.save()



        



        # ?湔?唾?鈭箇?蝝?



        applicant = promotion_request.applicant



        applicant.level = promotion_request.target_level



        applicant.save()



        



        messages.success(request, 'Operation successful')




    



    return redirect('engineer_rpg:manager_dashboard')











@login_required



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



    



    # 蝯梯?鞈?



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



    """Create User"""



    # TODO: User creation logic?



    pass











@login_required



def edit_user(request, user_id):



    """Edit User"""



    # TODO: User editing logic?



    pass











@login_required



def question_management(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    



    if profile.role != 'ADMIN':



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:dashboard')



    



    # 蝭拚



    category_id = request.GET.get('category')



    search_query = request.GET.get('q')



    



    questions = Question.objects.all().order_by('-created_at')



    



    if category_id:



        questions = questions.filter(category_id=category_id)



    



    if search_query:



        questions = questions.filter(content__icontains=search_query)



    



    # ??



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











@login_required



def create_question(request):



    """Function docstring"""


    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return redirect('engineer_rpg:dashboard')



        



    if request.method == 'POST':



        # 蝪∪撖虫?嚗?蝥?寧 Form



        content = request.POST.get('content')



        q_type = request.POST.get('question_type')



        category_id = request.POST.get('category')



        difficulty = request.POST.get('difficulty')



        



        # ???賊???獢?



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











# ==================== ???銝?蝞∠? ====================







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



    



    # ?芸???????



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



        item_reward_id = request.POST.get('equipment_reward')  # ?垢甈??迂?急?靽? equipment_reward



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



    questions = Question.objects.filter(is_active=True) # ?臭誑?芸???AJAX 頛



    items = Item.objects.all()  # ?脣??????



    context = {



        'profile': profile, 



        'categories': categories,



        'questions': questions,



        'equipments': items  # ?箔??詨捆璅⊥嚗? equipments 霈??



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



        'equipments': items, # ?詨捆璅⊥



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



    



    context = {



        'profile': profile,



        'skills': skills,



        'courses': courses,



        'classes': classes,



        'selected_class': selected_class_code,



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



        



    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return JsonResponse({'error': 'Permission denied'}, status=403)



        



    try:



        data = json.loads(request.body)



        node_id = data.get('id')



        



        if node_id:



            # Update



            node = SkillNode.objects.get(id=node_id)



        else:



            # Create



            node = SkillNode()



            # Default pos



            node.position_x = 100



            node.position_y = 100



            



        node.name = data.get('name')



        node.description = data.get('description', '')



        node.node_type = data.get('type')



        



        # Handle class specific logic



        if node.node_type == 'ROOT':



            node.character_class = None



        else:



            class_code = data.get('class_code')



            if class_code:



                node.character_class = CharacterClass.objects.get(code=class_code)



                



        node.save()



        



        # Handle prerequisites (parents) with validation



        if 'parents' in data:



            parent_ids = data['parents']



            if parent_ids is not None:



                # Validate parent skills



                parent_skills = SkillNode.objects.filter(id__in=parent_ids)



                



                # 1. Check type restrictions



                node_type = node.node_type



                for parent in parent_skills:



                    if node_type == 'ROOT':



                        # ROOT can only have ROOT parents



                        if parent.node_type != 'ROOT':



                            return JsonResponse({'error': 'Parent node must be ROOT'}, status=400)





                    elif node_type == 'CORE':



                        # CORE can only have ROOT or CORE parents



                        if parent.node_type not in ['ROOT', 'CORE']:



                            return JsonResponse({'error': 'Invalid parent for CORE node'}, status=400)





                    # ADVANCED can have any type, no restriction



                



                # 2. Check for circular dependencies



                def would_create_cycle(node_id, new_parent_ids):



                    """Function docstring"""


                    # 撱箇??嗅???鞈游?嚗???喳?靽格??暺?



                    def get_all_ancestors(skill_id, visited=None):



                        """Function docstring"""


                        if visited is None:



                            visited = set()



                        



                        if skill_id in visited:



                            return visited



                        



                        visited.add(skill_id)



                        



                        # Comment

                        if skill_id == node_id:



                            # Comment

                            parent_ids = new_parent_ids



                        else:



                            # Comment

                            parent_ids = list(SkillNode.objects.get(id=skill_id).parent_skills.values_list('id', flat=True))



                        



                        for parent_id in parent_ids:



                            if parent_id in visited:



                                # 瑼Ｘ葫?啣儐?堆?



                                return None  # 餈? None 銵函內?儐??



                            ancestors = get_all_ancestors(parent_id, visited.copy())



                            if ancestors is None:



                                return None  # ?單敺芰瑼Ｘ葫蝯?



                            visited.update(ancestors)



                        



                        return visited



                    



                    # 瑼Ｘ?臬?耦?儐??



                    result = get_all_ancestors(node_id)



                    return result is None  # None 銵函內?儐??



                



                # Comment

                parent_ids = [p.id for p in parent_skills]



                



                # 蝪∪瑼Ｘ嚗?暺??賢??芸楛閮剔?蔭



                if node.id in parent_ids:



                        return JsonResponse({'error': 'Cannot set parent to itself or duplicate'}, status=400)





                



                # Comment

                if would_create_cycle(node.id, parent_ids):



                        return JsonResponse({'error': 'Cycle detected'}, status=400)




                



                # All validations passed, set parents



                node.parent_skills.set(parent_skills)



        















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



    """Function docstring"""


    if request.method != 'POST':



        return JsonResponse({'error': 'Method not allowed'}, status=405)



        



    profile = get_or_create_user_profile(request.user)



    if profile.role != 'ADMIN':



        return JsonResponse({'error': 'Permission denied'}, status=403)



        



    try:



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



        



        # ?惜蝝?蝯?



        levels = {}



        for skill_id, level in skill_levels.items():



            if level not in levels:



                levels[level] = []



            levels[level].append(skill_id)



        



        # ??摨扳?



        Y_SPACING = 200  # 撅斤???



        X_SPACING = 150  # ?惜蝝??賡?頝?



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











# ==================== ??蝞∠? ====================







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



    



    # ?脣??梢?閮?



    hot_posts = GuildPost.objects.filter(is_pinned=False).order_by('-views', '-created_at')[:5]



    



    # Comment

    teams = Team.objects.all().prefetch_related(



        'current_members__user',



        'current_members__character_class'



    )



    



    # ?脣??⊿?隡??∴??芰???



    free_members = UserProfile.objects.filter(



        current_team__isnull=True



    ).select_related('user', 'character_class')



    



    # 瑼Ｘ?臬?箇恣?嚗?潮＊蝷箇恣?葉敹???



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

    # ?蕪??



    if category != 'ALL':



        posts = posts.filter(category=category)



    



    # 蝵桅??????蝡?



    pinned_posts = posts.filter(is_pinned=True)



    normal_posts = posts.filter(is_pinned=False)



    



    # ??



    from django.core.paginator import Paginator



    paginator = Paginator(normal_posts, 20)  # 瘥? 20 蝭?



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



    



    # ?舀?? URL ????



    initial_category = request.GET.get('category')



    



    if request.method == 'POST':



        title = request.POST.get('title')



        content = request.POST.get('content')



        category = request.POST.get('category')



        



        # 甈?瑼Ｘ嚗?恣??臭誑?澆??



        if category == 'ANNOUNCEMENT' and profile.role not in ['OFFICER', 'MANAGER', 'ADMIN']:



            messages.error(request, 'Only officers can post announcements')



            return redirect('engineer_rpg:guild_exchange_list')



            



        if title and content and category:



            post = GuildPost.objects.create(



                author=profile,



                title=title,



                content=content,  # 瘜冽?嚗??蝙??CKEditor ?閬?閮?HTML



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
            messages.success(request, '公告發布成功')
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
            messages.success(request, '公告更新成功')
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



    



    # 憓??汗??



    post.views += 1



    post.save()



    



    # ????



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



    



    # ?脣???”?摮貊?蝯梯?嚗??恍??瘀?



    members = list(team.current_members.all().select_related('user', 'character_class'))



    



    # 撠??瑕??交??∪?銵剁?憒????profile嚗?



    try:



        leader_profile = UserProfile.objects.select_related('user', 'character_class').get(user=team.leader)



        # 瑼Ｘ??臬撌脩??冽??∪?銵其葉嚗??銴?



        if leader_profile not in members:



            members.insert(0, leader_profile)  # 撠??瑟?典?銵冽??



    except UserProfile.DoesNotExist:



        pass  # 憒??瘝? profile嚗歲??



    



    member_stats = []



    for member in members:



        # Comment

        total_skills = SkillNode.objects.filter(character_class=member.character_class).count()



        completed_skills = UserSkill.objects.filter(



            user_profile=member,



            status='COMPLETED'



        ).count()



        skill_completion = (completed_skills / total_skills * 100) if total_skills > 0 else 0



        



        # Comment

        recent_trials = TrialRecord.objects.filter(



            user_profile=member



        ).order_by('-completed_at')[:5]



        



        # 閮?閰衣?蝯梯?



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



    



    context = {



        'profile': profile,



        'team': team,



        'member_stats': member_stats,



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



    



    # 蝣箄?閰脫??∪惇?潭迨??



    if member.current_team != team:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    # Comment

    skills = UserSkill.objects.filter(user_profile=member).select_related('skill_node')



    



    # ?脣?閰衣?閮?



    trial_records = TrialRecord.objects.filter(



        user_profile=member



    ).select_related('trial').order_by('-completed_at')



    



    # ??



    paginator = Paginator(trial_records, 10)



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    context = {



        'profile': profile,



        'team': team,



        'member': member,



        'skills': skills,



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



    



    # ?脣?閰衣?閮?



    trial_records = TrialRecord.objects.filter(



        user_profile=member



    ).select_related('trial').order_by('-completed_at')



    



    # ??



    paginator = Paginator(trial_records, 10)



    page_number = request.GET.get('page')



    page_obj = paginator.get_page(page_number)



    



    context = {



        'profile': profile,



        'team': member.current_team,  # ?航??None



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



    



    # 瑼Ｘ甈?嚗???瑕隞亦恣??



    if team.leader != request.user:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    # ?脣??嗅??



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



    



    # 瑼Ｘ甈?



    if team.leader != request.user:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    member_id = request.POST.get('member_id')



    if not member_id:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_manage_members', team_id=team_id)



    



    try:



        member_profile = UserProfile.objects.get(id=member_id)



        



        # 瑼Ｘ?臬撌脫???



        if member_profile.current_team:



            messages.error(request, 'An error occurred')




            return redirect('engineer_rpg:team_manage_members', team_id=team_id)



        



        # ?湔 UserProfile



        member_profile.current_team = team



        member_profile.save()



        



        # ?萄遣 TeamMembership 閮?



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



    



    # 瑼Ｘ甈?



    if team.leader != request.user:



        messages.error(request, 'An error occurred')




        return redirect('engineer_rpg:team_detail', team_id=team_id)



    



    try:



        member_profile = UserProfile.objects.get(id=member_id)



        



        # 瑼Ｘ?臬?冽迨??銝?



        if member_profile.current_team != team:



            messages.error(request, 'An error occurred')




            return redirect('engineer_rpg:team_manage_members', team_id=team_id)



        



        # ?湔 UserProfile



        member_profile.current_team = None



        member_profile.save()



        



        # ?湔 TeamMembership 閮?



        from django.utils import timezone



        membership = TeamMembership.objects.filter(



            user_profile=member_profile,



            team=team,



            is_current=True



        ).first()



        



        if membership:



            membership.is_current = False



            membership.left_at = timezone.now()



            membership.leave_reason = '?蝘駁'



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



    



    # ?脣?銝血?憿???



    user_items = UserItem.objects.filter(user_profile=profile).select_related('item').order_by('item__item_type', 'item__rarity')



    



    # ????蝯?



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





        



        # 皜??賊?



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
def manage_team_members(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

@login_required
def create_team(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

@login_required
def delete_team(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

@login_required
def team_management(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

@login_required
def edit_team(request, *args, **kwargs):
    # Placeholder restored automatically
    return JsonResponse({'status': 'success', 'message': 'Function restored as placeholder'}, status=200)

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
