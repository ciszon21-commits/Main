import json
from datetime import timedelta
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from .models import (
    Post, Comment, PostInteraction, Petition, Endorsement,
    PetitionComment, PetitionSave, CommentLike, SiteConfig,
)


# ========== 工具函式 ==========

def _is_manager(user):
    """判斷使用者是否為主管角色（可擴充判定邏輯）"""
    return user.is_staff


def _is_developer(user):
    """判斷使用者是否為開發者（superuser）"""
    return user.is_superuser


def _annotate_posts(qs, user):
    """在 QuerySet 上標註互動資訊"""
    if user.is_authenticated:
        qs = qs.annotate(
            _like_count=Count('interactions', filter=Q(interactions__liked=True)),
            _comment_count=Count('comments', distinct=True),
        )
    return qs


def _get_user_interactions(user, post_ids):
    """取得使用者對指定貼文的互動狀態"""
    interactions = PostInteraction.objects.filter(
        user=user, post_id__in=post_ids
    )
    return {
        i.post_id: {'liked': i.liked, 'saved': i.saved}
        for i in interactions
    }


class PostListMixin:
    """共用的貼文列表 Mixin"""

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_manager'] = _is_manager(self.request.user)
        user = self.request.user
        if user.is_authenticated and 'posts' in ctx:
            post_ids = [p.id for p in ctx['posts']]
            ctx['user_interactions'] = _get_user_interactions(user, post_ids)
        ctx['search_term'] = self.request.GET.get('q', '')
        return ctx

    def filter_by_search(self, qs):
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q) |
                Q(author__first_name__icontains=q) |
                Q(author__last_name__icontains=q)
            )
        return qs


# ========== 研發專案（Dashboard 首頁）==========

class DashboardView(LoginRequiredMixin, PostListMixin, ListView):
    model = Post
    template_name = 'LHAWish/dashboard.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        qs = Post.objects.filter(type='rnd').select_related('author')
        return self.filter_by_search(qs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'rnd'
        return ctx


# ========== 跳蚤市場 ==========

class MarketListView(LoginRequiredMixin, PostListMixin, ListView):
    model = Post
    template_name = 'LHAWish/market_list.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        qs = Post.objects.filter(type='market').select_related('author')
        qs = self.filter_by_search(qs)
        # 篩選
        f = self.request.GET.get('filter', '')
        if f == 'on_sale':
            qs = qs.filter(status='on_sale')
        elif f == 'sold':
            qs = qs.filter(status='sold')
        elif f == 'newest':
            qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'market'
        ctx['current_filter'] = self.request.GET.get('filter', '')
        return ctx


# ========== 七嘴八舌 ==========

class GossipListView(LoginRequiredMixin, PostListMixin, ListView):
    model = Post
    template_name = 'LHAWish/gossip_list.html'
    context_object_name = 'posts'
    paginate_by = 20

    def get_queryset(self):
        qs = Post.objects.filter(type='gossip').select_related('author')
        qs = self.filter_by_search(qs)
        user = self.request.user
        if not _is_manager(user):
            qs = qs.filter(
                Q(visibility='all') | Q(author=user)
            )
        # 篩選
        f = self.request.GET.get('filter', '')
        if f == 'newest':
            qs = qs.order_by('-created_at')
        elif f == 'hot':
            qs = qs.annotate(
                _hot=Count('interactions', filter=Q(interactions__liked=True))
            ).order_by('-_hot', '-created_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'gossip'
        ctx['current_filter'] = self.request.GET.get('filter', '')
        return ctx


# ========== 主管信箱 ==========

class MailboxView(LoginRequiredMixin, TemplateView):
    template_name = 'LHAWish/mailbox.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'mailbox'
        ctx['is_manager'] = _is_manager(self.request.user)
        config = SiteConfig.load()
        ctx['managers'] = [
            {'name': e.get('name', ''), 'email': e.get('email', '')}
            for e in config.manager_emails
        ] if isinstance(config.manager_emails, list) and config.manager_emails and isinstance(config.manager_emails[0], dict) else [
            {'name': '部門主管(資協)', 'email': 'test.manager@company.com'},
        ]
        return ctx


# ========== 管理儀表板 ==========

class ManagerDashboardView(LoginRequiredMixin, PostListMixin, ListView):
    model = Post
    template_name = 'LHAWish/manager_dashboard.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(type='rnd').select_related('author')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'dashboard'

        # 園路願望 — 只統計已成案(需處理的)
        established_qs = Petition.objects.filter(status='established')
        ctx['petition_established'] = established_qs.count()
        ctx['petition_responded'] = Petition.objects.filter(status='responded').count()
        ctx['petition_total'] = ctx['petition_established']

        # 依組別分組已成案案件
        groups = {}
        for p in established_qs.select_related('proposer').order_by('-created_at'):
            group_label = p.get_assigned_group_display() if p.assigned_group else '未指定'
            groups.setdefault(group_label, []).append(p)
        ctx['petition_groups'] = groups

        # 所有未撤案的願望（用於卡片點擊展開）
        ctx['petitions'] = Petition.objects.exclude(
            status='withdrawn'
        ).select_related('proposer').order_by('-created_at')[:30]

        # 研發專案 — 依狀態分組
        rnd_qs = Post.objects.filter(type='rnd')
        ctx['rnd_pending'] = rnd_qs.filter(status='pending').count()
        ctx['rnd_in_progress'] = rnd_qs.filter(status='in_progress').count()
        ctx['rnd_scheduled'] = rnd_qs.filter(status='scheduled').count()
        ctx['rnd_total'] = ctx['rnd_pending'] + ctx['rnd_in_progress'] + ctx['rnd_scheduled']
        # 依狀態分組
        rnd_active = rnd_qs.exclude(status='done').select_related('author').order_by('-created_at')[:50]
        rnd_groups = {}
        for p in rnd_active:
            s = p.status_display
            rnd_groups.setdefault(s, []).append(p)
        ctx['rnd_groups'] = rnd_groups
        ctx['rnd_posts'] = rnd_active

        # 預設顯示分頁
        ctx['active_section'] = self.request.GET.get('section', 'petition')

        return ctx


# ========== 個人中心 ==========

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'LHAWish/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'profile'
        ctx['is_manager'] = _is_manager(self.request.user)
        sub_tab = self.request.GET.get('tab', 'my-posts')
        ctx['profile_sub_tab'] = sub_tab

        user = self.request.user
        if sub_tab == 'saved':
            saved_ids = PostInteraction.objects.filter(
                user=user, saved=True
            ).values_list('post_id', flat=True)
            ctx['posts'] = Post.objects.filter(id__in=saved_ids).select_related('author')
        else:
            ctx['posts'] = Post.objects.filter(author=user).select_related('author')

        ctx['my_post_count'] = Post.objects.filter(author=user).count()
        ctx['saved_count'] = PostInteraction.objects.filter(user=user, saved=True).count()

        post_ids = [p.id for p in ctx['posts']]
        ctx['user_interactions'] = _get_user_interactions(user, post_ids)
        return ctx


# ========== 貼文詳情 ==========

class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'LHAWish/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.select_related('author')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        ctx['comments'] = post.comments.select_related('author').all()
        ctx['is_manager'] = _is_manager(self.request.user)
        # 使用者互動
        try:
            interaction = PostInteraction.objects.get(
                post=post, user=self.request.user
            )
            ctx['is_liked'] = interaction.liked
            ctx['is_saved'] = interaction.saved
        except PostInteraction.DoesNotExist:
            ctx['is_liked'] = False
            ctx['is_saved'] = False

        # 載入使用者對留言的按讚狀態
        comment_ids = [c.id for c in ctx['comments']]
        user_liked_comment_ids = set(CommentLike.objects.filter(
            user=self.request.user, comment_id__in=comment_ids
        ).values_list('comment_id', flat=True))
        ctx['user_liked_comment_ids'] = user_liked_comment_ids
        return ctx


# ========== 發文 ==========

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'LHAWish/post_form.html'
    fields = ['type', 'title', 'content', 'category', 'status',
              'package_name', 'problem_type', 'assigned_group', 'price', 'price_label',
              'condition', 'image', 'visibility', 'is_anonymous']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_manager'] = _is_manager(self.request.user)
        ctx['form_type'] = self.request.GET.get('type', 'rnd')
        ctx['active_tab'] = ctx['form_type']
        config = SiteConfig.load()
        ctx['group_choices'] = config.group_choices or []
        return ctx

    def form_valid(self, form):
        form.instance.author = self.request.user
        post_type = form.instance.type
        # 設定預設狀態
        if post_type == 'rnd' and not form.instance.status:
            form.instance.status = 'pending'
        elif post_type == 'market' and not form.instance.status:
            form.instance.status = 'on_sale'

        # 處理多圖上傳
        uploaded_files = self.request.FILES.getlist('image')
        if len(uploaded_files) > 1:
            # 多張圖片：第一張存 image 欄位，所有圖片存 images JSON
            from django.core.files.storage import default_storage
            import os
            from django.utils.timezone import now
            image_urls = []
            for i, f in enumerate(uploaded_files):
                folder = now().strftime('lhawish/posts/%Y/%m/')
                filename = default_storage.save(
                    os.path.join(folder, f.name), f
                )
                image_urls.append(default_storage.url(filename))
            form.instance.images = image_urls
            # 第一張仍存到 image 欄位
            form.instance.image = uploaded_files[0]

        return super().form_valid(form)

    def get_success_url(self):
        post = self.object
        type_to_url = {
            'rnd': 'lhawish:dashboard',
            'market': 'lhawish:market_list',
            'gossip': 'lhawish:gossip_list',
        }
        return reverse(type_to_url.get(post.type, 'lhawish:dashboard'))


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    template_name = 'LHAWish/post_form.html'
    fields = ['title', 'content', 'category', 'status',
              'package_name', 'problem_type', 'price', 'price_label',
              'condition', 'image', 'visibility', 'is_anonymous']

    def get_queryset(self):
        # 只能編輯自己的文章（主管可編輯所有）
        if _is_manager(self.request.user):
            return Post.objects.all()
        return Post.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_manager'] = _is_manager(self.request.user)
        ctx['form_type'] = self.object.type
        ctx['is_edit'] = True
        config = SiteConfig.load()
        ctx['group_choices'] = config.group_choices or []
        return ctx

    def get_success_url(self):
        return reverse('lhawish:post_detail', kwargs={'pk': self.object.pk})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post

    def get_queryset(self):
        if _is_manager(self.request.user):
            return Post.objects.all()
        return Post.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('lhawish:dashboard')


# ========== AJAX API ==========

@login_required
@require_POST
def toggle_like(request, pk):
    post = get_object_or_404(Post, pk=pk)
    interaction, created = PostInteraction.objects.get_or_create(
        post=post, user=request.user
    )
    interaction.liked = not interaction.liked
    interaction.save()
    return JsonResponse({
        'liked': interaction.liked,
        'like_count': post.like_count,
    })


@login_required
@require_POST
def toggle_save(request, pk):
    post = get_object_or_404(Post, pk=pk)
    interaction, created = PostInteraction.objects.get_or_create(
        post=post, user=request.user
    )
    interaction.saved = not interaction.saved
    interaction.save()
    return JsonResponse({
        'saved': interaction.saved,
    })


@login_required
@require_POST
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        is_anonymous = data.get('is_anonymous', False)
        is_official = data.get('is_official', False)
    except json.JSONDecodeError:
        content = request.POST.get('content', '').strip()
        is_anonymous = False
        is_official = False

    if not content:
        return JsonResponse({'error': '留言不能為空'}, status=400)

    comment = Comment.objects.create(
        post=post,
        author=request.user,
        content=content,
        is_official=bool(is_official) and _is_manager(request.user),
        is_anonymous=is_anonymous,
    )
    return JsonResponse({
        'id': comment.id,
        'author': comment.display_author,
        'content': comment.content,
        'is_official': comment.is_official,
        'is_anonymous': comment.is_anonymous,
        'created_at': comment.created_at.strftime('%Y/%m/%d %H:%M'),
        'comment_count': post.comment_count,
    })


@login_required
@require_POST
def update_status(request, pk):
    """主管更新貼文狀態"""
    if not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    post = get_object_or_404(Post, pk=pk)
    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')
    except json.JSONDecodeError:
        new_status = request.POST.get('status', '')

    post.status = new_status
    post.save(update_fields=['status'])
    return JsonResponse({
        'status': post.status,
        'status_display': post.status_display,
    })


# ========== 留言按讚 API ==========

@login_required
@require_POST
def toggle_comment_like(request, pk):
    """通用留言按讚（Post Comment 或 Petition Comment）"""
    try:
        data = json.loads(request.body)
        comment_type = data.get('type', 'comment')  # 'comment' or 'petition_comment'
    except json.JSONDecodeError:
        comment_type = 'comment'

    if comment_type == 'petition_comment':
        pc = get_object_or_404(PetitionComment, pk=pk)
        like, created = CommentLike.objects.get_or_create(
            user=request.user, petition_comment=pc
        )
        if not created:
            like.delete()
            return JsonResponse({'liked': False, 'like_count': pc.like_count})
        return JsonResponse({'liked': True, 'like_count': pc.like_count})
    else:
        c = get_object_or_404(Comment, pk=pk)
        like, created = CommentLike.objects.get_or_create(
            user=request.user, comment=c
        )
        if not created:
            like.delete()
            return JsonResponse({'liked': False, 'like_count': c.like_count})
        return JsonResponse({'liked': True, 'like_count': c.like_count})


# ========== 園路願望 ==========

class PetitionListView(LoginRequiredMixin, ListView):
    model = Petition
    template_name = 'LHAWish/petition_list.html'
    context_object_name = 'petitions'
    paginate_by = 20

    def get_queryset(self):
        qs = Petition.objects.select_related('proposer')
        # 排除隱藏的提議（一般使用者看不到）
        qs = qs.exclude(status='hidden')
        # 狀態篩選（預設附議中）
        status_filter = self.request.GET.get('status', 'endorsing')
        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)
        # 搜尋
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        # 排序
        sort = self.request.GET.get('sort', 'newest')
        if sort == 'hot':
            qs = qs.annotate(endorse_cnt=Count('endorsements')).order_by('-endorse_cnt', '-created_at')
        else:
            qs = qs.order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'petition'
        ctx['is_manager'] = _is_manager(self.request.user)
        ctx['selected_status'] = self.request.GET.get('status', 'endorsing')
        ctx['search_term'] = self.request.GET.get('q', '')
        ctx['sort'] = self.request.GET.get('sort', 'newest')
        return ctx


class PetitionDetailView(LoginRequiredMixin, DetailView):
    model = Petition
    template_name = 'LHAWish/petition_detail.html'
    context_object_name = 'petition'

    def get_queryset(self):
        return Petition.objects.select_related('proposer', 'response_by')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        petition = self.object
        ctx['active_tab'] = 'petition'
        ctx['is_manager'] = _is_manager(self.request.user)
        ctx['comments'] = petition.petition_comments.select_related('author').all()
        ctx['has_endorsed'] = Endorsement.objects.filter(
            petition=petition, user=self.request.user
        ).exists()
        ctx['is_proposer'] = (petition.proposer == self.request.user)
        # 收藏狀態
        ctx['is_petition_saved'] = PetitionSave.objects.filter(
            petition=petition, user=self.request.user
        ).exists()
        # 留言按讚狀態
        comment_ids = [c.id for c in ctx['comments']]
        ctx['user_liked_pcomment_ids'] = set(CommentLike.objects.filter(
            user=self.request.user, petition_comment_id__in=comment_ids
        ).values_list('petition_comment_id', flat=True))
        return ctx


class PetitionCreateView(LoginRequiredMixin, CreateView):
    model = Petition
    template_name = 'LHAWish/petition_form.html'
    fields = ['title', 'content', 'assigned_group', 'is_anonymous', 'display_name']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'petition'
        ctx['is_manager'] = _is_manager(self.request.user)
        config = SiteConfig.load()
        ctx['group_choices'] = config.group_choices or []
        return ctx

    def form_valid(self, form):
        form.instance.proposer = self.request.user
        form.instance.status = 'endorsing'
        # 從 SiteConfig 讀取門檻
        config = SiteConfig.load()
        form.instance.endorsement_threshold = config.endorsement_threshold
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('lhawish:petition_list')


@login_required
@require_POST
def endorse_petition(request, pk):
    """附議提議"""
    petition = get_object_or_404(Petition, pk=pk)
    if petition.status != 'endorsing':
        return JsonResponse({'error': '此提議已不在附議階段'}, status=400)

    # 檢查是否已附議
    if Endorsement.objects.filter(petition=petition, user=request.user).exists():
        return JsonResponse({'error': '您已經附議過此提議'}, status=400)

    Endorsement.objects.create(petition=petition, user=request.user)

    # 檢查是否達到門檻 → 自動成案
    if petition.endorsement_count >= petition.endorsement_threshold:
        petition.status = 'established'
        petition.deadline = timezone.now() + timedelta(days=60)
        petition.save(update_fields=['status', 'deadline'])

    return JsonResponse({
        'endorsed': True,
        'endorsement_count': petition.endorsement_count,
        'endorsement_percent': petition.endorsement_percent,
        'status': petition.status,
    })


@login_required
@require_POST
def withdraw_petition(request, pk):
    """撤案（僅提議者、未成案前）"""
    petition = get_object_or_404(Petition, pk=pk)
    if petition.proposer != request.user:
        return JsonResponse({'error': '僅提議者可撤案'}, status=403)
    if petition.status not in ('endorsing', 'established'):
        return JsonResponse({'error': '目前狀態無法撤案'}, status=400)

    try:
        data = json.loads(request.body)
        reason = data.get('reason', '').strip()
    except json.JSONDecodeError:
        reason = request.POST.get('reason', '').strip()

    if not reason:
        return JsonResponse({'error': '請填寫撤案理由'}, status=400)

    petition.status = 'withdrawn'
    petition.withdraw_reason = reason
    petition.save(update_fields=['status', 'withdraw_reason'])
    return JsonResponse({'status': 'withdrawn'})


@login_required
@require_POST
def respond_petition(request, pk):
    """主管/指定組別回應成案提議"""
    if not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    petition = get_object_or_404(Petition, pk=pk)
    if petition.status not in ('established', 'responded'):
        return JsonResponse({'error': '此提議尚未成案'}, status=400)

    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
    except json.JSONDecodeError:
        content = request.POST.get('content', '').strip()

    if not content:
        return JsonResponse({'error': '請填寫回應內容'}, status=400)

    petition.response_content = content
    petition.response_at = timezone.now()
    petition.response_by = request.user
    if petition.status == 'established':
        petition.status = 'responded'
    petition.save(update_fields=['status', 'response_content', 'response_at', 'response_by'])
    return JsonResponse({'status': petition.status})


@login_required
@require_POST
def delete_petition_response(request, pk):
    """管理者刪除官方回應"""
    if not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    petition = get_object_or_404(Petition, pk=pk)
    if petition.status != 'responded':
        return JsonResponse({'error': '此提議沒有官方回應'}, status=400)

    petition.response_content = ''
    petition.response_at = None
    petition.response_by = None
    petition.status = 'established'
    petition.save(update_fields=['status', 'response_content', 'response_at', 'response_by'])
    return JsonResponse({'status': 'established'})


@login_required
@require_POST
def update_petition_status(request, pk):
    """管理儀表板 — 更新園路願望狀態"""
    if not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    petition = get_object_or_404(Petition, pk=pk)
    try:
        data = json.loads(request.body)
        new_status = data.get('status', '')
        reason = data.get('reason', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效請求'}, status=400)

    valid_statuses = ['endorsing', 'established', 'responded', 'withdrawn']
    if new_status not in valid_statuses:
        return JsonResponse({'error': '無效狀態'}, status=400)

    if new_status == 'withdrawn' and not reason:
        return JsonResponse({'error': '撤案需提供理由'}, status=400)

    petition.status = new_status
    if new_status == 'withdrawn':
        petition.withdraw_reason = reason
    if new_status == 'established' and not petition.deadline:
        petition.deadline = timezone.now() + timezone.timedelta(days=60)
    petition.save()
    return JsonResponse({'status': new_status})


@login_required
@require_POST
def add_petition_comment(request, pk):
    """提議留言"""
    petition = get_object_or_404(Petition, pk=pk)
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        is_anonymous = data.get('is_anonymous', False)
        is_official = data.get('is_official', False)
    except json.JSONDecodeError:
        content = request.POST.get('content', '').strip()
        is_anonymous = False
        is_official = False

    if not content:
        return JsonResponse({'error': '留言不能為空'}, status=400)

    comment = PetitionComment.objects.create(
        petition=petition,
        author=request.user,
        content=content,
        is_official=bool(is_official) and _is_manager(request.user),
        is_anonymous=is_anonymous,
    )
    return JsonResponse({
        'id': comment.id,
        'author': comment.display_author,
        'content': comment.content,
        'is_anonymous': comment.is_anonymous,
        'is_official': comment.is_official,
        'created_at': comment.created_at.strftime('%Y/%m/%d %H:%M'),
        'comment_count': petition.comment_count,
    })


# ========== 園路願望 — 收藏 ==========

@login_required
@require_POST
def toggle_petition_save(request, pk):
    """收藏/取消收藏園路願望"""
    petition = get_object_or_404(Petition, pk=pk)
    save_obj = PetitionSave.objects.filter(petition=petition, user=request.user).first()
    if save_obj:
        save_obj.delete()
        return JsonResponse({'saved': False})
    PetitionSave.objects.create(petition=petition, user=request.user)
    return JsonResponse({'saved': True})


# ========== 園路願望 — 編輯 ==========

@login_required
@require_POST
def edit_petition(request, pk):
    """提案人編輯內文"""
    petition = get_object_or_404(Petition, pk=pk)
    if petition.proposer != request.user:
        return JsonResponse({'error': '僅提案人可編輯'}, status=403)
    if petition.status == 'withdrawn':
        return JsonResponse({'error': '已撤案的提議無法編輯'}, status=400)

    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效請求'}, status=400)

    if not new_content:
        return JsonResponse({'error': '內容不能為空'}, status=400)

    petition.content = new_content
    petition.is_edited = True
    petition.save(update_fields=['content', 'is_edited', 'updated_at'])
    return JsonResponse({'success': True})


# ========== 設定頁面 ==========

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'LHAWish/settings.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['active_tab'] = 'settings'
        ctx['is_developer'] = _is_developer(self.request.user)
        ctx['is_manager'] = _is_manager(self.request.user)
        config = SiteConfig.load()
        ctx['config'] = config
        ctx['group_choices'] = config.group_choices or Petition.GROUP_CHOICES
        from django.contrib.auth.models import User
        ctx['all_users'] = User.objects.all().order_by('username')
        return ctx


@login_required
@require_POST
def save_settings(request):
    """儲存系統設定"""
    if not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效請求'}, status=400)

    config = SiteConfig.load()

    if 'endorsement_threshold' in data:
        config.endorsement_threshold = int(data['endorsement_threshold'])
    if 'package_choices' in data:
        config.package_choices = data['package_choices']
    if 'group_choices' in data:
        config.group_choices = data['group_choices']
    if 'manager_emails' in data:
        config.manager_emails = data['manager_emails']
    if 'board_admins' in data:
        config.board_admins = data['board_admins']

    config.save()
    return JsonResponse({'success': True})


# ========== 留言編輯/刪除 API ==========

@login_required
@require_POST
def edit_comment(request, pk):
    """編輯註釋（支援 Comment 和 PetitionComment）"""
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        comment_type = data.get('type', 'comment')
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效請求'}, status=400)

    if not content:
        return JsonResponse({'error': '內容不能為空'}, status=400)

    if comment_type == 'petition_comment':
        c = get_object_or_404(PetitionComment, pk=pk)
    else:
        c = get_object_or_404(Comment, pk=pk)

    if c.author != request.user:
        return JsonResponse({'error': '僅作者可編輯'}, status=403)

    c.content = content
    c.is_edited = True
    c.save(update_fields=['content', 'is_edited'])
    return JsonResponse({'success': True, 'content': c.content})


@login_required
@require_POST
def delete_comment(request, pk):
    """刪除留言（支援 Comment 和 PetitionComment）"""
    try:
        data = json.loads(request.body)
        comment_type = data.get('type', 'comment')
    except json.JSONDecodeError:
        comment_type = 'comment'

    if comment_type == 'petition_comment':
        c = get_object_or_404(PetitionComment, pk=pk)
    else:
        c = get_object_or_404(Comment, pk=pk)

    if c.author != request.user and not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    c.delete()
    return JsonResponse({'success': True})


# ========== 跳蚤市場 — 標註已售出 ==========

@login_required
@require_POST
def mark_sold(request, pk):
    """發文者標註已售出"""
    post = get_object_or_404(Post, pk=pk, type='market')
    if post.author != request.user and not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    post.status = 'sold'
    post.save(update_fields=['status'])
    return JsonResponse({'success': True, 'status': 'sold'})


# ========== 管理儀表板 — 園路願望操作 ==========

@login_required
@require_POST
def petition_action(request, pk):
    """管理員對園路願望執行操作：刪除/隱藏/撤銷"""
    if not _is_manager(request.user):
        return JsonResponse({'error': '權限不足'}, status=403)

    petition = get_object_or_404(Petition, pk=pk)
    try:
        data = json.loads(request.body)
        action = data.get('action', '')
        reason = data.get('reason', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': '無效請求'}, status=400)

    if action == 'delete':
        petition.delete()
        return JsonResponse({'success': True, 'action': 'deleted'})
    elif action == 'hide':
        petition.status = 'hidden'
        petition.save(update_fields=['status'])
        return JsonResponse({'success': True, 'action': 'hidden'})
    elif action == 'withdraw':
        if not reason:
            return JsonResponse({'error': '請提供撤銷理由'}, status=400)
        petition.status = 'withdrawn'
        petition.withdraw_reason = reason
        petition.save(update_fields=['status', 'withdraw_reason'])
        return JsonResponse({'success': True, 'action': 'withdrawn'})
    else:
        return JsonResponse({'error': '無效操作'}, status=400)
