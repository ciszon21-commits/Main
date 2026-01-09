from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Q, Count, Prefetch
from django.contrib import messages
from .models import AITool, Category, Tag, ViewLog, Favorite, Like, Comment, CommentReaction
from .forms import AIToolForm, CommentForm, ReplyForm, CommentEditForm


class AIToolListView(ListView):
    """工具列表頁 - 支援搜尋、分類篩選、依收藏數排序"""
    model = AITool
    template_name = 'AIToolsHub/tool_list.html'
    context_object_name = 'tools'
    paginate_by = 12

    def get_queryset(self):
        queryset = AITool.objects.select_related('category', 'created_by').prefetch_related('tags')

        # 搜尋功能
        search = self.request.GET.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(summary__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()

        # 分類篩選
        category_slug = self.request.GET.get('category', '')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # 排序：收藏多的排在前面
        return queryset.order_by('-favorite_count', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')

        # 如果已登入，取得使用者的收藏和點讚
        if self.request.user.is_authenticated:
            context['user_favorites'] = set(
                Favorite.objects.filter(user=self.request.user).values_list('tool_id', flat=True)
            )
            context['user_likes'] = set(
                Like.objects.filter(user=self.request.user).values_list('tool_id', flat=True)
            )
        else:
            context['user_favorites'] = set()
            context['user_likes'] = set()

        return context


class AIToolDetailView(DetailView):
    """工具詳細頁"""
    model = AITool
    template_name = 'AIToolsHub/tool_detail.html'
    context_object_name = 'tool'

    def get_queryset(self):
        return AITool.objects.select_related('category', 'created_by').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tool = self.object

        # 取得頂層留言（非回覆）和其回覆
        context['comments'] = tool.comments.filter(parent__isnull=True).select_related('user').prefetch_related(
            Prefetch('replies', queryset=Comment.objects.select_related('user'))
        )
        context['comment_form'] = CommentForm()
        context['reply_form'] = ReplyForm()

        # 檢查使用者是否為上傳者（可回覆留言）
        context['is_owner'] = self.request.user.is_authenticated and self.request.user == tool.created_by

        # 記錄瀏覽
        if self.request.user.is_authenticated:
            view_log, created = ViewLog.objects.get_or_create(
                tool=tool,
                user=self.request.user
            )
            if created:
                tool.view_count += 1
                tool.save(update_fields=['view_count'])

            # 檢查收藏和點讚狀態
            context['is_favorited'] = Favorite.objects.filter(tool=tool, user=self.request.user).exists()
            context['is_liked'] = Like.objects.filter(tool=tool, user=self.request.user).exists()
        else:
            context['is_favorited'] = False
            context['is_liked'] = False

        return context


class AIToolCreateView(LoginRequiredMixin, CreateView):
    """建立工具"""
    model = AITool
    form_class = AIToolForm
    template_name = 'AIToolsHub/tool_form.html'
    success_url = reverse_lazy('aitoolshub:tool_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '新增 AI 工具'
        context['submit_text'] = '建立'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '工具建立成功！')
        return super().form_valid(form)


class AIToolUpdateView(LoginRequiredMixin, UpdateView):
    """編輯工具 - 僅上傳者可編輯"""
    model = AITool
    form_class = AIToolForm
    template_name = 'AIToolsHub/tool_form.html'

    def get_queryset(self):
        # 只允許建立者編輯
        return AITool.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '編輯 AI 工具'
        context['submit_text'] = '更新'
        return context

    def get_success_url(self):
        return reverse_lazy('aitoolshub:tool_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, '工具更新成功！')
        return super().form_valid(form)


class AIToolDeleteView(LoginRequiredMixin, DeleteView):
    """刪除工具 - 僅上傳者可刪除"""
    model = AITool
    template_name = 'AIToolsHub/tool_confirm_delete.html'
    success_url = reverse_lazy('aitoolshub:tool_list')

    def get_queryset(self):
        return AITool.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, '工具已刪除！')
        return super().form_valid(form)


class MyFavoritesView(LoginRequiredMixin, ListView):
    """我的收藏列表"""
    model = AITool
    template_name = 'AIToolsHub/my_favorites.html'
    context_object_name = 'tools'
    paginate_by = 12

    def get_queryset(self):
        # 取得使用者收藏的工具
        favorite_tool_ids = Favorite.objects.filter(
            user=self.request.user
        ).values_list('tool_id', flat=True)

        return AITool.objects.filter(
            id__in=favorite_tool_ids
        ).select_related('category', 'created_by').prefetch_related('tags').order_by('-favorites__created_at')


@login_required
def toggle_favorite(request, pk):
    """收藏/取消收藏 (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    tool = get_object_or_404(AITool, pk=pk)
    favorite, created = Favorite.objects.get_or_create(tool=tool, user=request.user)

    if not created:
        # 已存在則刪除（取消收藏）
        favorite.delete()
        tool.favorite_count = max(0, tool.favorite_count - 1)
        tool.save(update_fields=['favorite_count'])
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'favorite_count': tool.favorite_count
        })
    else:
        # 新增收藏
        tool.favorite_count += 1
        tool.save(update_fields=['favorite_count'])
        return JsonResponse({
            'success': True,
            'action': 'added',
            'favorite_count': tool.favorite_count
        })


@login_required
def toggle_like(request, pk):
    """點讚/取消點讚 (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    tool = get_object_or_404(AITool, pk=pk)
    like, created = Like.objects.get_or_create(tool=tool, user=request.user)

    if not created:
        # 已存在則刪除（取消點讚）
        like.delete()
        tool.like_count = max(0, tool.like_count - 1)
        tool.save(update_fields=['like_count'])
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'like_count': tool.like_count
        })
    else:
        # 新增點讚
        tool.like_count += 1
        tool.save(update_fields=['like_count'])
        return JsonResponse({
            'success': True,
            'action': 'added',
            'like_count': tool.like_count
        })


@login_required
def comment_create(request, pk):
    """新增留言 (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    tool = get_object_or_404(AITool, pk=pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.tool = tool
        comment.user = request.user
        comment.save()

        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'user': comment.get_display_name(),
                'content': comment.content,
                'is_anonymous': comment.is_anonymous,
                'is_owner': True,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def reply_create(request, pk):
    """回覆留言 (AJAX) - 所有人都可以回覆"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    parent_comment = get_object_or_404(Comment, pk=pk)
    tool = parent_comment.tool

    form = ReplyForm(request.POST)

    if form.is_valid():
        reply = form.save(commit=False)
        reply.tool = tool
        reply.user = request.user
        reply.parent = parent_comment
        reply.save()

        return JsonResponse({
            'success': True,
            'reply': {
                'id': reply.id,
                'user': reply.get_display_name(),
                'content': reply.content,
                'is_anonymous': reply.is_anonymous,
                'is_owner': True,
                'is_tool_owner': request.user == tool.created_by,
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def comment_update(request, pk):
    """編輯留言 (AJAX) - 僅發表者可編輯"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    comment = get_object_or_404(Comment, pk=pk)

    # 只有發表者可以編輯，且留言未被刪除
    if not comment.can_edit(request.user):
        return JsonResponse({'success': False, 'error': '無法編輯此留言'}, status=403)

    form = CommentEditForm(request.POST, instance=comment)

    if form.is_valid():
        comment = form.save()
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'content': comment.content,
                'updated_at': comment.updated_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


@login_required
def toggle_comment_reaction(request, pk):
    """留言反應 (AJAX) - 新增/移除 emoji 反應"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    comment = get_object_or_404(Comment, pk=pk)
    reaction_type = request.POST.get('reaction_type', 'like')

    # 驗證反應類型
    valid_reactions = [choice[0] for choice in CommentReaction.REACTION_CHOICES]
    if reaction_type not in valid_reactions:
        return JsonResponse({'success': False, 'error': '無效的反應類型'}, status=400)

    # 檢查是否已有相同反應
    existing_reaction = CommentReaction.objects.filter(
        comment=comment,
        user=request.user,
        reaction_type=reaction_type
    ).first()

    if existing_reaction:
        # 移除反應
        existing_reaction.delete()
        action = 'removed'
    else:
        # 新增反應
        CommentReaction.objects.create(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type
        )
        action = 'added'

    # 取得反應統計
    reaction_counts = {}
    for rt, _ in CommentReaction.REACTION_CHOICES:
        count = CommentReaction.objects.filter(comment=comment, reaction_type=rt).count()
        if count > 0:
            reaction_counts[rt] = count

    return JsonResponse({
        'success': True,
        'action': action,
        'reaction_type': reaction_type,
        'reaction_counts': reaction_counts
    })


@login_required
def comment_delete(request, pk):
    """刪除留言 (AJAX) - 軟刪除，將內容標記為已刪除"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)

    comment = get_object_or_404(Comment, pk=pk)

    # 只有發表者可以刪除
    if not comment.can_delete(request.user):
        return JsonResponse({'success': False, 'error': '無法刪除此留言'}, status=403)

    # 軟刪除：標記為已刪除
    comment.is_deleted = True
    comment.save(update_fields=['is_deleted'])

    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.get_display_content(),
        }
    })


