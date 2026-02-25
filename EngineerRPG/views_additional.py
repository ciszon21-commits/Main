# Additional view functions for URLs

@login_required
def start_daily_trial(request, task_id):
    """Start daily trial"""
    profile = get_or_create_user_profile(request.user)
    
    from .models import DailyTrialTask, DailyTrialProgress
    task = get_object_or_404(DailyTrialTask, id=task_id)
    
    # Create or get progress
    progress, created = DailyTrialProgress.objects.get_or_create(
        user_profile=profile,
        daily_task=task,
        defaults={
            'initial_hp': profile.get_total_hp(),
            'current_hp': profile.get_total_hp(),
            'initial_mp': profile.get_total_mp(),
            'current_mp': profile.get_total_mp(),
        }
    )
    
    # Get questions
    questions = list(task.trial.questions.all())
    random.shuffle(questions)
    selected_questions = questions[:task.trial.question_count]
    
    # Store in session
    request.session['daily_task_id'] = task.id
    request.session['questions'] = [q.id for q in selected_questions]
    request.session['current_index'] = 0
    
    current_question = selected_questions[0]
    user_items = UserItem.objects.filter(user_profile=profile, quantity__gt=0).select_related('item')
    
    context = {
        'profile': profile,
        'trial': task.trial,
        'daily_task': task,
        'question': current_question,
        'current_index': 0,
        'total_questions': len(selected_questions),
        'base_hp': 3,
        'initial_hp': progress.current_hp,
        'initial_mp': progress.current_mp,
        'heart_range': range(1, max(progress.initial_hp, 5) + 1),
        'is_daily_task': True,
        'user_items': user_items,
    }
    
    return render(request, 'EngineerRPG/trial_exam.html', context)


@login_required
def dungeon_list(request):
    """Dungeon list"""
    profile = get_or_create_user_profile(request.user)
    
    categories = QuestionCategory.objects.all()
    dungeons = Trial.objects.filter(trial_type='DUNGEON', is_active=True)
    
    context = {
        'profile': profile,
        'categories': categories,
        'dungeons': dungeons,
    }
    
    return render(request, 'EngineerRPG/dungeon_list.html', context)


@login_required
def trial_detail(request, trial_id):
    """Trial detail"""
    profile = get_or_create_user_profile(request.user)
    trial = get_object_or_404(Trial, id=trial_id)
    
    context = {
        'profile': profile,
        'trial': trial,
    }
    
    return render(request, 'EngineerRPG/trial_detail.html', context)


@login_required
def submit_answer(request, trial_id):
    """Submit answer (alias for submit_trial)"""
    return submit_trial(request, trial_id)


@login_required
def trial_record_detail(request, record_id):
    """Trial record detail (alias for trial_result)"""
    return trial_result(request, record_id)


@login_required
def apply_promotion(request):
    """Apply for promotion"""
    profile = get_or_create_user_profile(request.user)
    
    if request.method == 'POST':
        target_role = request.POST.get('target_role')
        
        PromotionRequest.objects.create(
            user_profile=profile,
            target_role=target_role,
            status='PENDING'
        )
        
        messages.success(request, 'Promotion request submitted!')
        return redirect('engineer_rpg:dashboard')
    
    return render(request, 'EngineerRPG/apply_promotion.html', {'profile': profile})


@login_required
def promotion_trial(request, request_id):
    """Promotion trial"""
    profile = get_or_create_user_profile(request.user)
    promo_request = get_object_or_404(PromotionRequest, id=request_id, user_profile=profile)
    
    context = {
        'profile': profile,
        'promo_request': promo_request,
    }
    
    return render(request, 'EngineerRPG/promotion_trial.html', context)


@login_required
def leaderboard(request):
    """Leaderboard"""
    profile = get_or_create_user_profile(request.user)
    
    top_users = UserProfile.objects.all().order_by('-experience')[:100]
    
    context = {
        'profile': profile,
        'top_users': top_users,
    }
    
    return render(request, 'EngineerRPG/leaderboard.html', context)


@login_required
def manager_dashboard(request):
    """Manager dashboard"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/manager_dashboard.html', context)


@login_required
def promotion_requests(request):
    """Promotion requests list"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    requests_list = PromotionRequest.objects.filter(status='PENDING').order_by('-created_at')
    
    context = {
        'profile': profile,
        'requests': requests_list,
    }
    
    return render(request, 'EngineerRPG/promotion_requests.html', context)


@login_required
def review_request(request, request_id):
    """Review promotion request"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    promo_request = get_object_or_404(PromotionRequest, id=request_id)
    
    context = {
        'profile': profile,
        'promo_request': promo_request,
    }
    
    return render(request, 'EngineerRPG/review_request.html', context)


@login_required
def approve_request(request, request_id):
    """Approve promotion request"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    promo_request = get_object_or_404(PromotionRequest, id=request_id)
    promo_request.status = 'APPROVED'
    promo_request.reviewed_by = profile
    promo_request.reviewed_at = timezone.now()
    promo_request.save()
    
    # Update user role
    promo_request.user_profile.role = promo_request.target_role
    promo_request.user_profile.save()
    
    messages.success(request, 'Request approved!')
    return redirect('engineer_rpg:promotion_requests')


@login_required
def reject_request(request, request_id):
    """Reject promotion request"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    promo_request = get_object_or_404(PromotionRequest, id=request_id)
    promo_request.status = 'REJECTED'
    promo_request.reviewed_by = profile
    promo_request.reviewed_at = timezone.now()
    promo_request.save()
    
    messages.success(request, 'Request rejected!')
    return redirect('engineer_rpg:promotion_requests')


@login_required
def user_management(request):
    """User management"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    users = UserProfile.objects.all().select_related('user', 'character_class')
    
    context = {
        'profile': profile,
        'users': users,
    }
    
    return render(request, 'EngineerRPG/user_management.html', context)


@login_required
def create_user(request):
    """Create user"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        # Handle user creation
        username = request.POST.get('username')
        password = request.POST.get('password')
        employee_id = request.POST.get('employee_id')
        character_class_id = request.POST.get('character_class')
        
        from django.contrib.auth.models import User
        user = User.objects.create_user(username=username, password=password)
        
        character_class = CharacterClass.objects.get(id=character_class_id)
        UserProfile.objects.create(
            user=user,
            employee_id=employee_id,
            character_class=character_class
        )
        
        messages.success(request, 'User created!')
        return redirect('engineer_rpg:user_management')
    
    character_classes = CharacterClass.objects.all()
    
    context = {
        'profile': profile,
        'character_classes': character_classes,
    }
    
    return render(request, 'EngineerRPG/create_user.html', context)


@login_required
def edit_user(request, user_id):
    """Edit user"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    user_profile = get_object_or_404(UserProfile, id=user_id)
    
    if request.method == 'POST':
        # Handle user edit
        user_profile.employee_id = request.POST.get('employee_id')
        user_profile.level = int(request.POST.get('level', user_profile.level))
        user_profile.experience = int(request.POST.get('experience', user_profile.experience))
        user_profile.save()
        
        messages.success(request, 'User updated!')
        return redirect('engineer_rpg:user_management')
    
    context = {
        'profile': profile,
        'user_profile': user_profile,
    }
    
    return render(request, 'EngineerRPG/edit_user.html', context)


@login_required
def question_management(request):
    """Question management"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    questions = Question.objects.all().order_by('-created_at')
    
    context = {
        'profile': profile,
        'questions': questions,
    }
    
    return render(request, 'EngineerRPG/question_management.html', context)


@login_required
def create_question(request):
    """Create question"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        # Handle question creation
        content = request.POST.get('content')
        question_type = request.POST.get('question_type')
        correct_answer = request.POST.get('correct_answer')
        difficulty = request.POST.get('difficulty')
        
        question = Question.objects.create(
            content=content,
            question_type=question_type,
            correct_answer=correct_answer,
            difficulty=difficulty
        )
        
        # Handle options
        if question_type == 'MULTIPLE_CHOICE':
            options = {
                'A': request.POST.get('option_a'),
                'B': request.POST.get('option_b'),
                'C': request.POST.get('option_c'),
                'D': request.POST.get('option_d'),
            }
            question.options = options
            question.save()
        
        messages.success(request, 'Question created!')
        return redirect('engineer_rpg:question_management')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/create_question.html', context)


@login_required
def edit_question(request, question_id):
    """Edit question"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        # Handle question edit
        question.content = request.POST.get('content')
        question.question_type = request.POST.get('question_type')
        question.correct_answer = request.POST.get('correct_answer')
        question.difficulty = request.POST.get('difficulty')
        
        if question.question_type == 'MULTIPLE_CHOICE':
            options = {
                'A': request.POST.get('option_a'),
                'B': request.POST.get('option_b'),
                'C': request.POST.get('option_c'),
                'D': request.POST.get('option_d'),
            }
            question.options = options
        
        question.save()
        
        messages.success(request, 'Question updated!')
        return redirect('engineer_rpg:question_management')
    
    context = {
        'profile': profile,
        'question': question,
    }
    
    return render(request, 'EngineerRPG/edit_question.html', context)


@login_required
def category_management(request):
    """Category management"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    categories = QuestionCategory.objects.all()
    
    context = {
        'profile': profile,
        'categories': categories,
    }
    
    return render(request, 'EngineerRPG/category_management.html', context)


@login_required
def dungeon_management(request):
    """Dungeon management"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    dungeons = Trial.objects.filter(trial_type='DUNGEON')
    
    context = {
        'profile': profile,
        'dungeons': dungeons,
    }
    
    return render(request, 'EngineerRPG/dungeon_management.html', context)


@login_required
def create_dungeon(request):
    """Create dungeon"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    if request.method == 'POST':
        # Handle dungeon creation
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        
        category = QuestionCategory.objects.get(id=category_id)
        
        trial = Trial.objects.create(
            title=title,
            description=description,
            trial_type='DUNGEON',
            category=category,
            question_count=10,
            time_limit_minutes=30,
            exp_reward=100
        )
        
        messages.success(request, 'Dungeon created!')
        return redirect('engineer_rpg:dungeon_management')
    
    categories = QuestionCategory.objects.all()
    
    context = {
        'profile': profile,
        'categories': categories,
    }
    
    return render(request, 'EngineerRPG/create_dungeon.html', context)


@login_required
def edit_dungeon(request, dungeon_id):
    """Edit dungeon"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    dungeon = get_object_or_404(Trial, id=dungeon_id)
    
    if request.method == 'POST':
        # Handle dungeon edit
        dungeon.title = request.POST.get('title')
        dungeon.description = request.POST.get('description')
        dungeon.save()
        
        messages.success(request, 'Dungeon updated!')
        return redirect('engineer_rpg:dungeon_management')
    
    context = {
        'profile': profile,
        'dungeon': dungeon,
    }
    
    return render(request, 'EngineerRPG/edit_dungeon.html', context)


@login_required
def import_questions_view(request):
    """Import questions"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/import_questions.html', context)


@login_required
def download_template(request, format):
    """Download template"""
    # Return a template file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="question_template.{format}"'
    
    if format == 'csv':
        response.write('content,question_type,correct_answer,difficulty,option_a,option_b,option_c,option_d\n')
    
    return response


@login_required
def skill_tree_editor(request):
    """Skill tree editor"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    character_classes = CharacterClass.objects.all()
    
    context = {
        'profile': profile,
        'character_classes': character_classes,
    }
    
    return render(request, 'EngineerRPG/skill_tree_editor.html', context)


# API Views
@login_required
def api_user_stats(request):
    """API: User stats"""
    profile = get_or_create_user_profile(request.user)
    
    data = {
        'level': profile.level,
        'experience': profile.experience,
        'hp': profile.get_total_hp(),
        'mp': profile.get_total_mp(),
    }
    
    return JsonResponse(data)


@login_required
def api_skill_tree_data(request):
    """API: Skill tree data"""
    profile = get_or_create_user_profile(request.user)
    
    skills = SkillNode.objects.filter(character_class=profile.character_class)
    
    data = {
        'skills': [
            {
                'id': skill.id,
                'name': skill.name,
                'type': skill.skill_type,
                'position_x': skill.position_x,
                'position_y': skill.position_y,
            }
            for skill in skills
        ]
    }
    
    return JsonResponse(data)


@login_required
def api_skill_editor_data(request):
    """API: Skill editor data"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    class_id = request.GET.get('class_id')
    skills = SkillNode.objects.filter(character_class_id=class_id)
    
    data = {
        'skills': [
            {
                'id': skill.id,
                'name': skill.name,
                'type': skill.skill_type,
                'position_x': skill.position_x,
                'position_y': skill.position_y,
            }
            for skill in skills
        ]
    }
    
    return JsonResponse(data)


@login_required
@csrf_exempt
def api_save_skill_layout(request):
    """API: Save skill layout"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        for skill_data in data.get('skills', []):
            skill = SkillNode.objects.get(id=skill_data['id'])
            skill.position_x = skill_data['position_x']
            skill.position_y = skill_data['position_y']
            skill.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@csrf_exempt
def api_save_skill_node(request):
    """API: Save skill node"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        skill_id = data.get('id')
        if skill_id:
            skill = SkillNode.objects.get(id=skill_id)
        else:
            skill = SkillNode()
        
        skill.name = data.get('name')
        skill.skill_type = data.get('type')
        skill.character_class_id = data.get('class_id')
        skill.position_x = data.get('position_x', 0)
        skill.position_y = data.get('position_y', 0)
        skill.save()
        
        return JsonResponse({'success': True, 'id': skill.id})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@csrf_exempt
def api_delete_skill_node(request):
    """API: Delete skill node"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        skill_id = data.get('id')
        
        skill = SkillNode.objects.get(id=skill_id)
        skill.delete()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@csrf_exempt
def api_manage_skill_course(request):
    """API: Manage skill course"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Handle course management
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
@csrf_exempt
def api_auto_layout_skill_tree(request):
    """API: Auto layout skill tree"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role != 'ADMIN':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        # Implement auto layout logic
        return JsonResponse({'success': True})
    
    return JsonResponse({'error': 'Invalid method'}, status=405)


# Guild System
@login_required
def guild_dashboard(request):
    """Guild dashboard"""
    profile = get_or_create_user_profile(request.user)
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/guild_dashboard.html', context)


@login_required
def guild_exchange_list(request):
    """Guild exchange list"""
    profile = get_or_create_user_profile(request.user)
    
    posts = GuildPost.objects.all().order_by('-created_at')
    
    context = {
        'profile': profile,
        'posts': posts,
    }
    
    return render(request, 'EngineerRPG/guild_exchange_list.html', context)


@login_required
def guild_post_create(request):
    """Create guild post"""
    profile = get_or_create_user_profile(request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        
        GuildPost.objects.create(
            author=profile,
            title=title,
            content=content
        )
        
        messages.success(request, 'Post created!')
        return redirect('engineer_rpg:guild_exchange_list')
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'EngineerRPG/guild_post_create.html', context)


@login_required
def guild_post_detail(request, post_id):
    """Guild post detail"""
    profile = get_or_create_user_profile(request.user)
    
    post = get_object_or_404(GuildPost, id=post_id)
    comments = GuildComment.objects.filter(post=post).order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        GuildComment.objects.create(
            post=post,
            author=profile,
            content=content
        )
        
        messages.success(request, 'Comment added!')
        return redirect('engineer_rpg:guild_post_detail', post_id=post_id)
    
    context = {
        'profile': profile,
        'post': post,
        'comments': comments,
    }
    
    return render(request, 'EngineerRPG/guild_post_detail.html', context)


# Team System
@login_required
def team_dashboard(request):
    """Team dashboard"""
    profile = get_or_create_user_profile(request.user)
    
    teams = Team.objects.all()
    
    context = {
        'profile': profile,
        'teams': teams,
    }
    
    return render(request, 'EngineerRPG/team_dashboard.html', context)


@login_required
def team_detail(request, team_id):
    """Team detail"""
    profile = get_or_create_user_profile(request.user)
    
    team = get_object_or_404(Team, id=team_id)
    members = TeamMembership.objects.filter(team=team).select_related('member')
    
    context = {
        'profile': profile,
        'team': team,
        'members': members,
    }
    
    return render(request, 'EngineerRPG/team_detail.html', context)


@login_required
def team_member_detail(request, team_id, member_id):
    """Team member detail"""
    profile = get_or_create_user_profile(request.user)
    
    team = get_object_or_404(Team, id=team_id)
    member = get_object_or_404(UserProfile, id=member_id)
    
    context = {
        'profile': profile,
        'team': team,
        'member': member,
    }
    
    return render(request, 'EngineerRPG/team_member_detail.html', context)


@login_required
def team_manage_members(request, team_id):
    """Manage team members"""
    profile = get_or_create_user_profile(request.user)
    
    team = get_object_or_404(Team, id=team_id)
    
    if team.leader != profile and profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:team_detail', team_id=team_id)
    
    members = TeamMembership.objects.filter(team=team).select_related('member')
    
    context = {
        'profile': profile,
        'team': team,
        'members': members,
    }
    
    return render(request, 'EngineerRPG/team_manage_members.html', context)


@login_required
def team_add_member(request, team_id):
    """Add team member"""
    profile = get_or_create_user_profile(request.user)
    
    team = get_object_or_404(Team, id=team_id)
    
    if team.leader != profile and profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:team_detail', team_id=team_id)
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        member = UserProfile.objects.get(id=member_id)
        
        TeamMembership.objects.create(
            team=team,
            member=member,
            role='MEMBER'
        )
        
        messages.success(request, 'Member added!')
        return redirect('engineer_rpg:team_manage_members', team_id=team_id)
    
    all_users = UserProfile.objects.all()
    
    context = {
        'profile': profile,
        'team': team,
        'all_users': all_users,
    }
    
    return render(request, 'EngineerRPG/team_add_member.html', context)


@login_required
def team_remove_member(request, team_id, member_id):
    """Remove team member"""
    profile = get_or_create_user_profile(request.user)
    
    team = get_object_or_404(Team, id=team_id)
    
    if team.leader != profile and profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:team_detail', team_id=team_id)
    
    membership = TeamMembership.objects.get(team=team, member_id=member_id)
    membership.delete()
    
    messages.success(request, 'Member removed!')
    return redirect('engineer_rpg:team_manage_members', team_id=team_id)


@login_required
def member_profile_detail(request, member_id):
    """Member profile detail"""
    profile = get_or_create_user_profile(request.user)
    
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Access denied!')
        return redirect('engineer_rpg:dashboard')
    
    member = get_object_or_404(UserProfile, id=member_id)
    
    context = {
        'profile': profile,
        'member': member,
    }
    
    return render(request, 'EngineerRPG/member_profile_detail.html', context)
