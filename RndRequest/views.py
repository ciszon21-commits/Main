from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Sum, Q
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import RndRequest, RndRequestVote, RndRequestComment
from .forms import RndRequestForm


class RndRequestListView(ListView):
    """研發需求列表頁面 - 按淨票數排序"""
    model = RndRequest
    template_name = 'RndRequest/request_list.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        # 使用 annotate 計算淨票數，按票數排序
        return RndRequest.objects.annotate(
            score=Sum('votes__vote_type')
        ).order_by('-score', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 取得當前使用者已投票的需求
        if self.request.user.is_authenticated:
            user_votes = RndRequestVote.objects.filter(
                user=self.request.user
            ).values_list('request_id', 'vote_type')
            context['user_votes'] = {req_id: vote_type for req_id, vote_type in user_votes}
        else:
            context['user_votes'] = {}
        return context


class RndRequestDetailView(DetailView):
    """研發需求詳細頁面"""
    model = RndRequest
    template_name = 'RndRequest/request_detail.html'
    context_object_name = 'rnd_request'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 檢查當前使用者是否已投票
        if self.request.user.is_authenticated:
            user_vote = RndRequestVote.objects.filter(
                request=self.object,
                user=self.request.user
            ).first()
            context['user_vote'] = user_vote.vote_type if user_vote else None
            
            # 管理員可以看到所有投票詳情
            if self.request.user.is_staff:
                context['all_votes'] = self.object.votes.select_related('user').order_by('-voted_at')
        else:
            context['user_vote'] = None
        
        # 取得留言列表（由新到舊）
        context['comments'] = self.object.comments.select_related('user').order_by('-created_at')
        return context


class RndRequestCreateView(LoginRequiredMixin, CreateView):
    """建立研發需求"""
    model = RndRequest
    form_class = RndRequestForm
    template_name = 'RndRequest/request_form.html'
    success_url = reverse_lazy('rndrequest:request_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '需求提案已成功建立！')
        return super().form_valid(form)


class RndRequestUpdateView(LoginRequiredMixin, UpdateView):
    """編輯研發需求 - 僅提案人可編輯"""
    model = RndRequest
    form_class = RndRequestForm
    template_name = 'RndRequest/request_form.html'
    
    def get_queryset(self):
        # 只允許提案人編輯
        return RndRequest.objects.filter(created_by=self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('rndrequest:request_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, '需求提案已更新！')
        return super().form_valid(form)


@login_required
def vote_request(request, pk):
    """投票 API（AJAX）- 支援更改投票"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    rnd_request = get_object_or_404(RndRequest, pk=pk)
    vote_type = request.POST.get('vote_type')
    
    # 驗證投票類型
    try:
        vote_type = int(vote_type)
        if vote_type not in [1, -1]:
            raise ValueError("Invalid vote type")
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': '無效的投票類型'}, status=400)
    
    # 檢查是否已投票
    existing_vote = RndRequestVote.objects.filter(
        request=rnd_request,
        user=request.user
    ).first()
    
    if existing_vote:
        # 如果已投過票，更改投票
        if existing_vote.vote_type == vote_type:
            return JsonResponse({
                'success': False, 
                'error': '您已經投過相同的票了',
                'current_vote': existing_vote.vote_type
            }, status=400)
        
        # 更新投票
        existing_vote.vote_type = vote_type
        existing_vote.save()
        message = '已更改投票'
    else:
        # 建立新投票記錄
        RndRequestVote.objects.create(
            request=rnd_request,
            user=request.user,
            vote_type=vote_type
        )
        message = '投票成功'
    
    return JsonResponse({
        'success': True,
        'message': message,
        'vote_score': rnd_request.vote_score,
        'upvote_count': rnd_request.upvote_count,
        'downvote_count': rnd_request.downvote_count,
        'user_vote': vote_type,
    })


@login_required
def update_status(request, pk):
    """更新需求狀態 API（僅管理員）"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': '您沒有權限執行此操作'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    rnd_request = get_object_or_404(RndRequest, pk=pk)
    new_status = request.POST.get('status')
    
    valid_statuses = ['pending', 'reviewing', 'accepted', 'rejected']
    if new_status not in valid_statuses:
        return JsonResponse({'success': False, 'error': '無效的狀態值'}, status=400)
    
    rnd_request.status = new_status
    rnd_request.save(update_fields=['status'])
    
    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': rnd_request.get_status_display(),
    })


@login_required
def add_comment(request, pk):
    """新增留言並寄信通知提案人"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    rnd_request = get_object_or_404(RndRequest, pk=pk)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'success': False, 'error': '請輸入留言內容'}, status=400)
    
    # 建立留言
    comment = RndRequestComment.objects.create(
        request=rnd_request,
        user=request.user,
        content=content
    )
    
    # 寄信通知提案人（若留言者非提案人本人）
    if request.user != rnd_request.created_by and rnd_request.created_by.email:
        commenter_name = request.user.get_full_name() or request.user.username
        try:
            send_mail(
                subject=f'[許願池] 您的願望「{rnd_request.title}」有新留言',
                message=f'''您好，{rnd_request.created_by.get_full_name() or rnd_request.created_by.username}，

您在許願池發布的願望「{rnd_request.title}」收到了一則新留言：

留言者：{commenter_name}
留言內容：
{content}

請至系統查看詳情。

---
此為系統自動發送的通知信件''',
                from_email=getattr(settings, 'SYSTEM_EMAIL', None) or getattr(settings, 'NOTIFY_EMAIL', 'noreply@example.com'),
                recipient_list=[rnd_request.created_by.email],
                fail_silently=True,
            )
        except Exception as e:
            # 寄信失敗不影響留言功能
            import logging
            logging.getLogger(__name__).warning(f"寄送留言通知失敗: {e}")
    
    # 取得留言者顯示名稱
    user_display = request.user.get_full_name() or request.user.username
    
    return JsonResponse({
        'success': True,
        'message': '留言成功',
        'comment': {
            'id': comment.id,
            'user': user_display,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        }
    })

