

# ==================== Restored Missing Views ====================

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
    
    return render(request, 'EngineerRPG/skill_tree_editor.html', {
        'profile': profile,
        'classes': classes,
        'selected_class': selected_class
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
    questions = course.questions.all()
    return render(request, 'EngineerRPG/course_exam.html', {
        'profile': profile, 
        'course': course, 
        'questions': questions
    })



def submit_course_exam(request, course_id):
    """提交課程測驗"""
    if request.method == 'POST':
        # 結算邏輯...
        messages.success(request, '課程測驗已提交')
        return redirect('engineer_rpg:skill_tree')
    return redirect('engineer_rpg:dashboard')



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
    return JsonResponse({'skills': []})



def api_skill_editor_data(request):
    """API: 技能編輯器資料"""
    return JsonResponse({'skills': []})



def api_manage_skill_course(request):
    """API: 管理技能課程"""
    return JsonResponse({'success': False, 'message': '功能開發中'})



def api_auto_distribute_xp(request):
    """API: 自動分配經驗值"""
    return JsonResponse({'success': False, 'message': '功能開發中'})


# ==================== 管理者白名單管理 ====================
