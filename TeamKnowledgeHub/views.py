from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
import json

from .models import KnowledgeTeam, KnowledgeTeamMember, Topic, Category, KnowledgeItem, ItemComment, ItemAttachment, CommentAttachment
from .forms import KnowledgeTeamForm, TopicForm, CategoryForm, KnowledgeItemForm, ItemCommentForm


# ===== Helper Functions =====

def check_team_member(user, team):
    """檢查使用者是否為團隊成員"""
    return team.is_member(user) or team.is_creator(user)


def check_team_creator(user, team):
    """檢查使用者是否為團隊建立者"""
    return team.is_creator(user)


# ===== Team Views =====

@login_required
def team_list(request):
    """團隊列表頁面 - 顯示使用者所屬的團隊"""
    # 使用 Q 物件合併查詢條件
    teams = KnowledgeTeam.objects.filter(
        Q(members__user=request.user) | Q(created_by=request.user)
    ).distinct().order_by('-created_at')
    
    return render(request, 'TeamKnowledgeHub/team_list.html', {
        'teams': teams,
    })


@login_required
def team_detail(request, pk):
    """團隊詳情頁面 - 只有成員可以看到內容"""
    team = get_object_or_404(KnowledgeTeam, pk=pk)
    
    # 檢查權限
    if not check_team_member(request.user, team):
        messages.error(request, '您不是此團隊的成員，無法查看內容。')
        return redirect('knowledge:team_list')
    
    topics = team.topics.prefetch_related('items', 'categories', 'categories__items').all()
    
    # ===== Dashboard Statistics =====
    from django.db.models import Count, Q
    
    # 1. 各主題項目統計 (以主題為單位，避免分類過多導致圖表混亂)
    category_metrics = []
    
    for topic in topics:
        item_count = topic.items.count()
        if item_count > 0:
            category_metrics.append({
                'name': topic.name,
                'count': item_count
            })

    # 2. 成員貢獻統計 (Top 10)
    member_stats = User.objects.filter(
        Q(knowledge_team_memberships__team=team) | Q(created_knowledge_teams=team)
    ).distinct().annotate(
        post_count=Count('created_knowledge_items', filter=Q(created_knowledge_items__topic__team=team)),
        comment_count=Count('knowledge_comments', filter=Q(knowledge_comments__item__topic__team=team)),
        file_count=Count('uploaded_item_attachments', filter=Q(uploaded_item_attachments__item__topic__team=team, uploaded_item_attachments__is_deleted=False))
    ).filter(
        Q(post_count__gt=0) | Q(comment_count__gt=0) | Q(file_count__gt=0)
    ).order_by('-post_count', '-comment_count')[:10]
    
    # 3. 本周活動統計 (Weekly Activity)
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)
    weekly_activity = []
    
    # Pre-fetch items created in range to avoid N+1 queries in loop (though simple count is fast)
    # Better: Aggregate locally in python or use TruncDate (but sqlite/mysql support varies)
    # Simple loop approach is fine for 7 iterations
    for i in range(7):
        date = seven_days_ago + timedelta(days=i)
        count = KnowledgeItem.objects.filter(
            topic__team=team,
            created_at__date=date
        ).count()
        weekly_activity.append({
            'date': date.strftime('%m/%d'),
            'count': count
        })
    
    return render(request, 'TeamKnowledgeHub/team_detail.html', {
        'team': team,
        'topics': topics,
        'is_creator': team.is_creator(request.user),
        # Statistics Data
        'category_metrics': json.dumps(category_metrics),
        'member_stats': member_stats, 
        'member_stats_json': json.dumps([{
            'name': m.get_full_name() or m.username,
            'posts': m.post_count,
            'comments': m.comment_count,
            'files': m.file_count
        } for m in member_stats]),
        'weekly_activity_json': json.dumps(weekly_activity),
    })


@login_required
def team_search(request, pk):
    """團隊內搜尋功能"""
    team = get_object_or_404(KnowledgeTeam, pk=pk)
    
    # 檢查權限
    if not check_team_member(request.user, team):
        messages.error(request, '您不是此團隊的成員，無法查看內容。')
        return redirect('knowledge:team_list')
    
    query = request.GET.get('q', '').strip()
    results = []
    
    if query and len(query) >= 2:
        # 搜尋標題、內容和留言
        results = KnowledgeItem.objects.filter(
            topic__team=team
        ).filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(comments__content__icontains=query)
        ).distinct().select_related('topic', 'category', 'created_by').order_by('-updated_at')[:50]
    
    return render(request, 'TeamKnowledgeHub/team_search.html', {
        'team': team,
        'query': query,
        'results': results,
        'result_count': len(results),
    })


@login_required
def team_create(request):
    """建立新團隊"""
    if request.method == 'POST':
        form = KnowledgeTeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.created_by = request.user
            team.save()
            
            # 將建立者加入團隊成員
            KnowledgeTeamMember.objects.create(
                team=team,
                user=request.user,
                role='creator'
            )
            
            messages.success(request, f'團隊「{team.name}」已建立成功！')
            return redirect('knowledge:team_detail', pk=team.pk)
    else:
        form = KnowledgeTeamForm()
    
    return render(request, 'TeamKnowledgeHub/team_form.html', {
        'form': form,
        'title': '建立新團隊',
    })


@login_required
def team_update(request, pk):
    """編輯團隊 - 只有建立者可以編輯"""
    team = get_object_or_404(KnowledgeTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        messages.error(request, '只有團隊建立者可以編輯團隊資訊。')
        return redirect('knowledge:team_detail', pk=pk)
    
    if request.method == 'POST':
        form = KnowledgeTeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, '團隊資訊已更新！')
            return redirect('knowledge:team_detail', pk=pk)
    else:
        form = KnowledgeTeamForm(instance=team)
    
    return render(request, 'TeamKnowledgeHub/team_form.html', {
        'form': form,
        'team': team,
        'title': '編輯團隊',
    })


@login_required
def team_members(request, pk):
    """管理團隊成員"""
    team = get_object_or_404(KnowledgeTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        messages.error(request, '只有團隊建立者可以管理成員。')
        return redirect('knowledge:team_detail', pk=pk)
    
    members = team.members.select_related('user').all()
    
    return render(request, 'TeamKnowledgeHub/team_members.html', {
        'team': team,
        'members': members,
    })


@login_required
def search_users(request):
    """搜尋使用者 API"""
    query = request.GET.get('q', '').strip()
    team_id = request.GET.get('team_id')
    
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )
    
    # 如果有指定團隊，排除已是成員的使用者
    if team_id:
        try:
            team = KnowledgeTeam.objects.get(pk=team_id)
            existing_member_ids = team.members.values_list('user_id', flat=True)
            users = users.exclude(id__in=existing_member_ids)
        except KnowledgeTeam.DoesNotExist:
            pass
    
    # 在所有篩選完成後才進行切片
    users = users[:10]
    
    users_data = [{
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
    } for user in users]
    
    return JsonResponse({'users': users_data})


@login_required
def add_member(request, pk):
    """新增團隊成員"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '請使用 POST 方法'}, status=405)
    
    team = get_object_or_404(KnowledgeTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊建立者可以新增成員'}, status=403)
    
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': '請選擇使用者'}, status=400)
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': '使用者不存在'}, status=404)
    
    if team.members.filter(user=user).exists():
        return JsonResponse({'success': False, 'error': '該使用者已是團隊成員'}, status=400)
    
    KnowledgeTeamMember.objects.create(
        team=team,
        user=user,
        role='member'
    )
    
    return JsonResponse({
        'success': True,
        'member': {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
        }
    })


@login_required
def remove_member(request, pk, user_id):
    """移除團隊成員"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '請使用 POST 方法'}, status=405)
    
    team = get_object_or_404(KnowledgeTeam, pk=pk)
    
    if not check_team_creator(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊建立者可以移除成員'}, status=403)
    
    # 不能移除建立者
    if team.created_by_id == user_id:
        return JsonResponse({'success': False, 'error': '無法移除團隊建立者'}, status=400)
    
    try:
        member = KnowledgeTeamMember.objects.get(team=team, user_id=user_id)
        member.delete()
        return JsonResponse({'success': True})
    except KnowledgeTeamMember.DoesNotExist:
        return JsonResponse({'success': False, 'error': '成員不存在'}, status=404)


# ===== Topic Views =====

@login_required
def topic_create(request, team_pk):
    """建立新主題"""
    team = get_object_or_404(KnowledgeTeam, pk=team_pk)
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以建立主題。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.team = team
            topic.save()
            messages.success(request, f'主題「{topic.name}」已建立成功！')
            return redirect('knowledge:team_detail', pk=team_pk)
    else:
        # 自動設定排序
        max_order = team.topics.count()
        form = TopicForm(initial={'order': max_order})
    
    return render(request, 'TeamKnowledgeHub/topic_form.html', {
        'form': form,
        'team': team,
        'title': '建立新主題',
    })


@login_required
def topic_update(request, pk):
    """編輯主題"""
    topic = get_object_or_404(Topic, pk=pk)
    team = topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以編輯主題。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            messages.success(request, '主題已更新！')
            return redirect('knowledge:team_detail', pk=team.pk)
    else:
        form = TopicForm(instance=topic)
    
    return render(request, 'TeamKnowledgeHub/topic_form.html', {
        'form': form,
        'team': team,
        'topic': topic,
        'title': '編輯主題',
    })


@login_required
def topic_delete(request, pk):
    """刪除主題"""
    topic = get_object_or_404(Topic, pk=pk)
    team = topic.team
    
    if not check_team_creator(request.user, team):
        messages.error(request, '只有團隊建立者可以刪除主題。')
        return redirect('knowledge:team_detail', pk=team.pk)
    
    if request.method == 'POST':
        topic_name = topic.name
        topic.delete()
        messages.success(request, f'主題「{topic_name}」已刪除！')
        return redirect('knowledge:team_detail', pk=team.pk)
    
    return render(request, 'TeamKnowledgeHub/confirm_delete.html', {
        'object': topic,
        'object_type': '主題',
        'back_url': f"/knowledge/team/{team.pk}/",
    })


# ===== Category Views =====

@login_required
def category_create(request, topic_pk):
    """建立新分類"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    team = topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以建立分類。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.topic = topic
            category.save()
            messages.success(request, f'分類「{category.name}」已建立成功！')
            return redirect('knowledge:category_manage', topic_pk=topic.pk)
    else:
        max_order = topic.categories.count()
        form = CategoryForm(initial={'order': max_order})
    
    return render(request, 'TeamKnowledgeHub/category_form.html', {
        'form': form,
        'team': team,
        'topic': topic,
        'title': '建立新分類',
    })


@login_required
def category_update(request, pk):
    """編輯分類"""
    category = get_object_or_404(Category, pk=pk)
    topic = category.topic
    team = topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以編輯分類。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, '分類已更新！')
            return redirect('knowledge:team_detail', pk=team.pk)
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'TeamKnowledgeHub/category_form.html', {
        'form': form,
        'team': team,
        'topic': topic,
        'category': category,
        'title': '編輯分類',
    })


@login_required
def category_delete(request, pk):
    """刪除分類"""
    category = get_object_or_404(Category, pk=pk)
    topic = category.topic
    team = topic.team
    
    if not check_team_creator(request.user, team):
        messages.error(request, '只有團隊建立者可以刪除分類。')
        return redirect('knowledge:team_detail', pk=team.pk)
    
    if request.method == 'POST':
        category_name = category.name
        # 將分類下的項目移到未分類
        category.items.update(category=None)
        category.delete()
        messages.success(request, f'分類「{category_name}」已刪除！項目已移至未分類。')
        return redirect('knowledge:team_detail', pk=team.pk)
    
    return render(request, 'TeamKnowledgeHub/confirm_delete.html', {
        'object': category,
        'object_type': '分類',
        'back_url': f"/knowledge/team/{team.pk}/",
    })


@login_required
def move_item(request):
    """移動項目到不同分類 (AJAX API)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '請使用 POST 方法'}, status=405)
    
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        category_id = data.get('category_id')  # None means uncategorized
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': '請求格式錯誤'}, status=400)
    
    if not item_id:
        return JsonResponse({'success': False, 'error': '請指定項目'}, status=400)
    
    item = get_object_or_404(KnowledgeItem, pk=item_id)
    team = item.topic.team
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以移動項目'}, status=403)
    
    if category_id:
        category = get_object_or_404(Category, pk=category_id)
        # 確保分類屬於同一主題
        if category.topic != item.topic:
            return JsonResponse({'success': False, 'error': '分類必須屬於同一主題'}, status=400)
        item.category = category
    else:
        item.category = None
    
    item.save()
    
    return JsonResponse({
        'success': True,
        'message': f'項目已移動至「{item.category.name if item.category else "未分類"}」'
    })


@login_required
def category_manage(request, topic_pk):
    """分類管理頁面"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    team = topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以管理分類。')
        return redirect('knowledge:team_list')
    
    categories = topic.categories.prefetch_related('items').all()
    uncategorized_items = topic.get_uncategorized_items()
    
    return render(request, 'TeamKnowledgeHub/category_manage.html', {
        'team': team,
        'topic': topic,
        'categories': categories,
        'uncategorized_items': uncategorized_items,
    })


# ===== Knowledge Item Views =====

@login_required
def item_create(request, topic_pk, category_pk=None):
    """建立新知識項目"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    team = topic.team
    
    # 取得分類（如果有指定）
    category = None
    if category_pk:
        category = get_object_or_404(Category, pk=category_pk)
        # 確保分類屬於該主題
        if category.topic != topic:
            messages.error(request, '分類不屬於此主題。')
            return redirect('knowledge:team_detail', pk=team.pk)
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以建立項目。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = KnowledgeItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.topic = topic
            item.category = category  # 自動歸類
            item.created_by = request.user
            item.save()
            messages.success(request, f'項目「{item.title}」已建立成功！')
            return redirect('knowledge:item_detail', pk=item.pk)
    else:
        form = KnowledgeItemForm()
    
    return render(request, 'TeamKnowledgeHub/item_form.html', {
        'form': form,
        'topic': topic,
        'team': team,
        'category': category,
        'title': '建立新項目',
    })


@login_required
def item_detail(request, pk):
    """知識項目詳情頁面"""
    item = get_object_or_404(KnowledgeItem, pk=pk)
    team = item.topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '您不是此團隊的成員，無法查看內容。')
        return redirect('knowledge:team_list')
    
    comments = item.comments.select_related('author').all()
    comment_form = ItemCommentForm()
    topics = team.topics.prefetch_related('items', 'categories', 'categories__items').all()
    
    # 處理搜尋上下文（從搜尋頁面來的）
    search_query = request.GET.get('q', '').strip()
    search_results = []
    
    if search_query and len(search_query) >= 2:
        search_results = KnowledgeItem.objects.filter(
            topic__team=team
        ).filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(comments__content__icontains=search_query)
        ).distinct().select_related('topic', 'category').order_by('-updated_at')[:20]
    
    # Get active (non-deleted) attachments
    attachments = item.attachments.filter(is_deleted=False).select_related('uploaded_by')
    
    return render(request, 'TeamKnowledgeHub/item_detail.html', {
        'item': item,
        'topic': item.topic,
        'team': team,
        'topics': topics,
        'comments': comments,
        'comment_form': comment_form,
        'is_creator': item.created_by == request.user,
        'is_team_creator': team.is_creator(request.user),
        'search_query': search_query,
        'search_results': search_results,
        'attachments': attachments,
    })


@login_required
def item_update(request, pk):
    """編輯知識項目"""
    item = get_object_or_404(KnowledgeItem, pk=pk)
    team = item.topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以編輯項目。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = KnowledgeItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, '項目已更新！')
            return redirect('knowledge:item_detail', pk=pk)
    else:
        form = KnowledgeItemForm(instance=item)
    
    return render(request, 'TeamKnowledgeHub/item_form.html', {
        'form': form,
        'item': item,
        'topic': item.topic,
        'team': team,
        'title': '編輯項目',
    })


@login_required
def item_delete(request, pk):
    """刪除知識項目"""
    item = get_object_or_404(KnowledgeItem, pk=pk)
    team = item.topic.team
    
    # 只有建立者或團隊建立者可以刪除
    if item.created_by != request.user and not check_team_creator(request.user, team):
        messages.error(request, '您沒有權限刪除此項目。')
        return redirect('knowledge:item_detail', pk=pk)
    
    if request.method == 'POST':
        topic_pk = item.topic.pk
        item_title = item.title
        item.delete()
        messages.success(request, f'項目「{item_title}」已刪除！')
        return redirect('knowledge:team_detail', pk=team.pk)
    
    return render(request, 'TeamKnowledgeHub/confirm_delete.html', {
        'object': item,
        'object_type': '項目',
        'back_url': f"/knowledge/item/{pk}/",
    })


# ===== Comment Views =====

@login_required
def add_comment(request, item_pk):
    """新增留言"""
    if request.method != 'POST':
        return redirect('knowledge:item_detail', pk=item_pk)
    
    item = get_object_or_404(KnowledgeItem, pk=item_pk)
    team = item.topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以留言。')
        return redirect('knowledge:team_list')
    
    form = ItemCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.item = item
        comment.author = request.user
        comment.save()
        messages.success(request, '留言已發表！')
    
    return redirect('knowledge:item_detail', pk=item_pk)


@login_required
def delete_comment(request, pk):
    """刪除留言"""
    comment = get_object_or_404(ItemComment, pk=pk)
    item_pk = comment.item.pk
    team = comment.item.topic.team
    
    # 只有作者或團隊建立者可以刪除
    if comment.author != request.user and not check_team_creator(request.user, team):
        messages.error(request, '您沒有權限刪除此留言。')
        return redirect('knowledge:item_detail', pk=item_pk)
    
    if request.method == 'POST':
        comment.delete()
        messages.success(request, '留言已刪除！')
    
    return redirect('knowledge:item_detail', pk=item_pk)


# ===== Attachment Views =====

@login_required
def upload_item_attachment(request, item_pk):
    """上傳項目附件"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效請求'})
    
    item = get_object_or_404(KnowledgeItem, pk=item_pk)
    team = item.topic.team
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以上傳附件'})
    
    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'success': False, 'error': '未選擇檔案'})
    
    uploaded = []
    for f in files:
        attachment = ItemAttachment.objects.create(
            item=item,
            file=f,
            filename=f.name,
            file_size=f.size,
            uploaded_by=request.user
        )
        uploaded.append({
            'id': attachment.pk,
            'filename': attachment.filename,
            'size': attachment.get_human_size(),
            'icon': attachment.get_file_icon(),
            'url': attachment.file.url
        })
    
    messages.success(request, f'成功上傳 {len(uploaded)} 個檔案！')
    
    # Return JSON for AJAX or redirect for normal form
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'files': uploaded})
    return redirect('knowledge:item_detail', pk=item_pk)


@login_required
def delete_attachment(request, pk):
    """軟刪除項目附件 (標記為已刪除)"""
    attachment = get_object_or_404(ItemAttachment, pk=pk)
    item = attachment.item
    team = item.topic.team
    
    # 只有上傳者或團隊建立者可以刪除
    if attachment.uploaded_by != request.user and not check_team_creator(request.user, team):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': '您沒有權限刪除此附件'})
        messages.error(request, '您沒有權限刪除此附件。')
        return redirect('knowledge:item_detail', pk=item.pk)
    
    if request.method == 'POST':
        from django.utils import timezone
        attachment.is_deleted = True
        attachment.deleted_at = timezone.now()
        attachment.deleted_by = request.user
        attachment.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': '附件已刪除'})
        messages.success(request, '附件已刪除！')
    
    return redirect('knowledge:item_detail', pk=item.pk)


@login_required
def upload_comment_attachment(request, comment_pk):
    """上傳留言附件"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效請求'})
    
    comment = get_object_or_404(ItemComment, pk=comment_pk)
    team = comment.item.topic.team
    
    if not check_team_member(request.user, team):
        return JsonResponse({'success': False, 'error': '只有團隊成員可以上傳附件'})
    
    files = request.FILES.getlist('files')
    if not files:
        return JsonResponse({'success': False, 'error': '未選擇檔案'})
    
    uploaded = []
    for f in files:
        attachment = CommentAttachment.objects.create(
            comment=comment,
            file=f,
            filename=f.name,
            file_size=f.size,
            uploaded_by=request.user
        )
        uploaded.append({
            'id': attachment.pk,
            'filename': attachment.filename,
            'size': attachment.get_human_size(),
            'icon': attachment.get_file_icon(),
            'url': attachment.file.url
        })
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'files': uploaded})
    return redirect('knowledge:item_detail', pk=comment.item.pk)


@login_required
def delete_comment_attachment(request, pk):
    """軟刪除留言附件"""
    attachment = get_object_or_404(CommentAttachment, pk=pk)
    comment = attachment.comment
    team = comment.item.topic.team
    
    if attachment.uploaded_by != request.user and not check_team_creator(request.user, team):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': '您沒有權限刪除此附件'})
        messages.error(request, '您沒有權限刪除此附件。')
        return redirect('knowledge:item_detail', pk=comment.item.pk)
    
    if request.method == 'POST':
        from django.utils import timezone
        attachment.is_deleted = True
        attachment.deleted_at = timezone.now()
        attachment.deleted_by = request.user
        attachment.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': '附件已刪除'})
        messages.success(request, '附件已刪除！')
    
    return redirect('knowledge:item_detail', pk=comment.item.pk)


@login_required
def category_files(request, pk):
    """分類檔案瀏覽"""
    category = get_object_or_404(Category, pk=pk)
    team = category.topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '您不是此團隊的成員。')
        return redirect('knowledge:team_list')
    
    # Get all non-deleted attachments from items in this category
    attachments = ItemAttachment.active.filter(
        item__category=category
    ).select_related('item', 'uploaded_by').order_by('item__title', '-uploaded_at')
    
    # Group by item
    items_with_files = {}
    for att in attachments:
        if att.item.pk not in items_with_files:
            items_with_files[att.item.pk] = {
                'item': att.item,
                'files': []
            }
        items_with_files[att.item.pk]['files'].append(att)
    
    return render(request, 'TeamKnowledgeHub/category_files.html', {
        'category': category,
        'topic': category.topic,
        'team': team,
        'items_with_files': items_with_files.values(),
        'total_files': attachments.count(),
    })

