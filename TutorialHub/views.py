from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, F
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User

from .models import (
    Tutorial,
    TutorialMaintainer,
    TutorialStep,
    StepSnippet,
    ReadingLog,
    Question,
    Answer
)
from .email_utils import send_question_notification, send_answer_notification


class TutorialListView(ListView):
    """教材列表視圖"""
    model = Tutorial
    template_name = 'tutorialhub/tutorial_list.html'
    context_object_name = 'tutorials'
    paginate_by = 12

    def get_queryset(self):
        queryset = Tutorial.objects.filter(is_published=True)
        
        # 搜尋功能
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class TutorialDetailView(DetailView):
    """教材詳情視圖"""
    model = Tutorial
    template_name = 'tutorialhub/tutorial_detail.html'
    context_object_name = 'tutorial'

    def get_queryset(self):
        return Tutorial.objects.filter(is_published=True)

    def get_object(self):
        obj = super().get_object()
        # 增加瀏覽次數
        obj.view_count = F('view_count') + 1
        obj.save(update_fields=['view_count'])
        obj.refresh_from_db()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutorial = self.object
        
        # 獲取所有步驟及其片段
        steps = tutorial.steps.prefetch_related('snippets', 'questions__answers__user')
        context['steps'] = steps
        
        # 獲取維護者列表（按貢獻度排序）
        context['maintainers'] = tutorial.maintainers.select_related('user').all()
        
        # 檢查當前使用者是否為維護者
        if self.request.user.is_authenticated:
            context['is_maintainer'] = tutorial.maintainers.filter(
                user=self.request.user
            ).exists()
        else:
            context['is_maintainer'] = False
        
        return context


class TutorialCreateView(LoginRequiredMixin, CreateView):
    """建立教材視圖"""
    model = Tutorial
    template_name = 'tutorialhub/tutorial_form.html'
    fields = ['title', 'description', 'cover_image', 'is_published']

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # 自動將建立者加入為維護者
        TutorialMaintainer.objects.create(
            tutorial=self.object,
            user=self.request.user,
            role='creator',
            contribution_score=100
        )
        
        messages.success(self.request, '教材建立成功！')
        return response


class TutorialUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """編輯教材視圖"""
    model = Tutorial
    template_name = 'tutorialhub/tutorial_form.html'
    fields = ['title', 'description', 'cover_image', 'is_published']

    def test_func(self):
        """只有維護者可以編輯"""
        tutorial = self.get_object()
        return tutorial.maintainers.filter(user=self.request.user).exists()

    def form_valid(self, form):
        messages.success(self.request, '教材更新成功！')
        return super().form_valid(form)


@login_required
def update_reading_time(request):
    """
    更新閱讀時間 API
    POST: tutorial_id, seconds
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只接受 POST 請求'}, status=405)
    
    tutorial_id = request.POST.get('tutorial_id')
    seconds = request.POST.get('seconds', 0)
    
    try:
        seconds = int(seconds)
        tutorial = Tutorial.objects.get(pk=tutorial_id, is_published=True)
        
        # 更新或建立閱讀記錄
        reading_log, created = ReadingLog.objects.get_or_create(
            tutorial=tutorial,
            user=request.user,
            defaults={'total_seconds': 0}
        )
        
        reading_log.total_seconds += seconds
        reading_log.save()
        
        return JsonResponse({
            'success': True,
            'total_seconds': reading_log.total_seconds,
            'display': reading_log.reading_time_display
        })
    
    except (ValueError, Tutorial.DoesNotExist) as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
def create_question(request):
    """
    建立問題 API
    POST: step_id, content
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只接受 POST 請求'}, status=405)
    
    step_id = request.POST.get('step_id')
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'success': False, 'message': '問題內容不可為空'}, status=400)
    
    try:
        step = TutorialStep.objects.get(pk=step_id)
        
        # 建立問題
        question = Question.objects.create(
            step=step,
            user=request.user,
            content=content
        )
        
        # 發送郵件通知
        send_question_notification(question)
        
        return JsonResponse({
            'success': True,
            'message': '問題已送出，維護者將收到通知',
            'question': {
                'id': question.id,
                'user': request.user.get_full_name() or request.user.username,
                'content': question.content,
                'created_at': question.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    except TutorialStep.DoesNotExist:
        return JsonResponse({'success': False, 'message': '步驟不存在'}, status=404)


@login_required
def create_answer(request):
    """
    建立回答 API
    POST: question_id, content
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只接受 POST 請求'}, status=405)
    
    question_id = request.POST.get('question_id')
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'success': False, 'message': '回答內容不可為空'}, status=400)
    
    try:
        question = Question.objects.get(pk=question_id)
        
        # 建立回答
        answer = Answer.objects.create(
            question=question,
            user=request.user,
            content=content
        )
        
        # 發送郵件通知
        send_answer_notification(answer)
        
        return JsonResponse({
            'success': True,
            'message': '回答已送出',
            'answer': {
                'id': answer.id,
                'user': request.user.get_full_name() or request.user.username,
                'content': answer.content,
                'is_from_maintainer': answer.is_from_maintainer,
                'created_at': answer.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    except Question.DoesNotExist:
        return JsonResponse({'success': False, 'message': '問題不存在'}, status=404)


@login_required
def toggle_question_resolved(request, question_id):
    """切換問題解決狀態"""
    question = get_object_or_404(Question, pk=question_id)
    tutorial = question.step.tutorial
    
    # 只有維護者可以標記為已解決
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '只有維護者可以標記問題狀態'}, status=403)
    
    question.is_resolved = not question.is_resolved
    question.save()
    
    return JsonResponse({
        'success': True,
        'is_resolved': question.is_resolved
    })


class UserProfileView(DetailView):
    """個人頁面視圖"""
    model = User
    template_name = 'tutorialhub/user_profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        
        # 獲取使用者的所有貢獻
        contributions = TutorialMaintainer.objects.filter(
            user=user
        ).select_related('tutorial').order_by('-contribution_score')
        
        context['contributions'] = contributions
        
        # 統計資料
        context['total_tutorials'] = contributions.count()
        context['total_contribution'] = contributions.aggregate(
            total=Sum('contribution_score')
        )['total'] or 0
        
        # 檢查是否為本人
        context['is_own_profile'] = (
            self.request.user.is_authenticated and
            self.request.user == user
        )
        
        return context


def analytics_view(request):
    """統計分析視圖"""
    # 熱門教材（按閱讀時間）
    popular_tutorials = Tutorial.objects.filter(
        is_published=True
    ).annotate(
        total_time=Sum('reading_logs__total_seconds'),
        reader_count=Count('reading_logs', distinct=True)
    ).order_by('-total_time')[:10]
    
    # 貢獻者排行榜
    top_contributors = User.objects.annotate(
        total_contribution=Sum('tutorial_contributions__contribution_score'),
        tutorial_count=Count('tutorial_contributions', distinct=True)
    ).filter(
        total_contribution__gt=0
    ).order_by('-total_contribution')[:10]
    
    # 閱讀時長排行榜
    top_readers = User.objects.annotate(
        total_time=Sum('tutorial_reading_logs__total_seconds')
    ).filter(
        total_time__gt=0
    ).order_by('-total_time')[:10]
    
    context = {
        'popular_tutorials': popular_tutorials,
        'top_contributors': top_contributors,
        'top_readers': top_readers,
    }
    
    return render(request, 'tutorialhub/analytics.html', context)
