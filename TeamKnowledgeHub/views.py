from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import KnowledgeTeam, KnowledgeTeamMember, Topic, KnowledgeItem, ItemComment
from .forms import KnowledgeTeamForm, TopicForm, KnowledgeItemForm, ItemCommentForm


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
    
    topics = team.topics.prefetch_related('items').all()
    
    return render(request, 'TeamKnowledgeHub/team_detail.html', {
        'team': team,
        'topics': topics,
        'is_creator': team.is_creator(request.user),
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
    )[:10]
    
    # 如果有指定團隊，排除已是成員的使用者
    if team_id:
        try:
            team = KnowledgeTeam.objects.get(pk=team_id)
            existing_member_ids = team.members.values_list('user_id', flat=True)
            users = users.exclude(id__in=existing_member_ids)
        except KnowledgeTeam.DoesNotExist:
            pass
    
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


# ===== Knowledge Item Views =====

@login_required
def item_create(request, topic_pk):
    """建立新知識項目"""
    topic = get_object_or_404(Topic, pk=topic_pk)
    team = topic.team
    
    if not check_team_member(request.user, team):
        messages.error(request, '只有團隊成員可以建立項目。')
        return redirect('knowledge:team_list')
    
    if request.method == 'POST':
        form = KnowledgeItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.topic = topic
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
    topics = team.topics.prefetch_related('items').all()
    
    return render(request, 'TeamKnowledgeHub/item_detail.html', {
        'item': item,
        'topic': item.topic,
        'team': team,
        'topics': topics,
        'comments': comments,
        'comment_form': comment_form,
        'is_creator': item.created_by == request.user,
        'is_team_creator': team.is_creator(request.user),
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
