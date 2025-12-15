from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, F
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction

from .models import (
    Tutorial,
    TutorialMaintainer,
    TutorialStep,
    StepSnippet,
    ReadingLog,
    Question,
    Answer
)
from .forms import TutorialForm, TutorialStepForm, StepSnippetForm, TutorialStepFormSet, StepSnippetFormSet
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
        
        return queryset.order_by('-view_count', '-created_at')

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
    form_class = TutorialForm
    template_name = 'tutorialhub/tutorial_form.html'

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            
            # 自動將建立者加入為維護者
            TutorialMaintainer.objects.create(
                tutorial=self.object,
                user=self.request.user,
                role='creator',
                contribution_score=100
            )
        
        messages.success(self.request, '教材建立成功！現在可以新增步驟和內容。')
        return redirect('tutorialhub:tutorial_edit_steps', slug=self.object.slug)


class TutorialUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """編輯教材基本資料視圖"""
    model = Tutorial
    form_class = TutorialForm
    template_name = 'tutorialhub/tutorial_form.html'

    def test_func(self):
        """只有維護者可以編輯"""
        tutorial = self.get_object()
        return tutorial.maintainers.filter(user=self.request.user).exists()

    def form_valid(self, form):
        messages.success(self.request, '教材更新成功！')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tutorialhub:tutorial_detail', kwargs={'slug': self.object.slug})


class TutorialDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """刪除教材視圖"""
    model = Tutorial
    template_name = 'tutorialhub/tutorial_confirm_delete.html'
    success_url = reverse_lazy('tutorialhub:tutorial_list')

    def test_func(self):
        """只有創建者可以刪除"""
        tutorial = self.get_object()
        return tutorial.maintainers.filter(user=self.request.user, role='creator').exists()

    def delete(self, request, *args, **kwargs):
        messages.success(request, '教材已刪除。')
        return super().delete(request, *args, **kwargs)


@login_required
def tutorial_edit_steps(request, slug):
    """編輯教材步驟視圖"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    
    # 檢查權限
    if not tutorial.maintainers.filter(user=request.user).exists():
        messages.error(request, '您沒有權限編輯此教材。')
        return redirect('tutorialhub:tutorial_detail', slug=slug)
    
    if request.method == 'POST':
        formset = TutorialStepFormSet(request.POST, instance=tutorial)
        if formset.is_valid():
            formset.save()
            messages.success(request, '步驟已儲存！')
            return redirect('tutorialhub:tutorial_edit_steps', slug=slug)
    else:
        formset = TutorialStepFormSet(instance=tutorial)
    
    return render(request, 'tutorialhub/tutorial_edit_steps.html', {
        'tutorial': tutorial,
        'formset': formset,
    })


@login_required
def step_edit_snippets(request, slug, step_id):
    """編輯步驟片段視圖"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    step = get_object_or_404(TutorialStep, pk=step_id, tutorial=tutorial)
    
    # 檢查權限
    if not tutorial.maintainers.filter(user=request.user).exists():
        messages.error(request, '您沒有權限編輯此教材。')
        return redirect('tutorialhub:tutorial_detail', slug=slug)
    
    if request.method == 'POST':
        formset = StepSnippetFormSet(request.POST, request.FILES, instance=step)
        if formset.is_valid():
            formset.save()
            messages.success(request, '內容已儲存！')
            return redirect('tutorialhub:step_edit_snippets', slug=slug, step_id=step_id)
    else:
        formset = StepSnippetFormSet(instance=step)
    
    return render(request, 'tutorialhub/step_edit_snippets.html', {
        'tutorial': tutorial,
        'step': step,
        'formset': formset,
    })


@login_required
def add_step(request, slug):
    """快速新增步驟 (AJAX)"""
    from django.db.models import Max
    tutorial = get_object_or_404(Tutorial, slug=slug)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'message': '標題不可為空'}, status=400)
        
        # 計算最大順序
        max_order = tutorial.steps.aggregate(Max('order'))['order__max'] or 0
        
        step = TutorialStep.objects.create(
            tutorial=tutorial,
            title=title,
            order=max_order + 1
        )
        
        return JsonResponse({
            'success': True,
            'step_id': step.id,
            'message': '步驟已新增'
        })
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def add_snippet(request, slug, step_id):
    """快速新增片段 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    step = get_object_or_404(TutorialStep, pk=step_id, tutorial=tutorial)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        from django.db import models as db_models
        snippet_type = request.POST.get('snippet_type', 'text')
        content = request.POST.get('content', '')
        language = request.POST.get('language', 'plaintext')
        caption = request.POST.get('caption', '')
        
        # 計算最大順序
        max_order = step.snippets.aggregate(db_models.Max('order'))['order__max'] or 0
        
        snippet = StepSnippet.objects.create(
            step=step,
            snippet_type=snippet_type,
            order=max_order + 1,
            content=content,
            language=language,
            caption=caption
        )
        
        # 處理圖片上傳
        if snippet_type == 'image' and 'image' in request.FILES:
            snippet.image = request.FILES['image']
            snippet.save()
        
        return JsonResponse({
            'success': True,
            'snippet_id': snippet.id,
            'message': '片段已新增'
        })
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def delete_step(request, slug, step_id):
    """刪除步驟 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    step = get_object_or_404(TutorialStep, pk=step_id, tutorial=tutorial)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        step.delete()
        return JsonResponse({'success': True, 'message': '步驟已刪除'})
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def update_step(request, slug, step_id):
    """更新步驟標題 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    step = get_object_or_404(TutorialStep, pk=step_id, tutorial=tutorial)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'message': '標題不可為空'}, status=400)
        
        step.title = title
        step.save()
        return JsonResponse({'success': True, 'message': '步驟標題已更新'})
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def delete_snippet(request, slug, snippet_id):
    """刪除片段 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    snippet = get_object_or_404(StepSnippet, pk=snippet_id, step__tutorial=tutorial)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        snippet.delete()
        return JsonResponse({'success': True, 'message': '片段已刪除'})
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def update_snippet(request, slug, snippet_id):
    """更新片段 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    snippet = get_object_or_404(StepSnippet, pk=snippet_id, step__tutorial=tutorial)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        snippet.snippet_type = request.POST.get('snippet_type', snippet.snippet_type)
        snippet.content = request.POST.get('content', snippet.content)
        snippet.language = request.POST.get('language', snippet.language)
        snippet.caption = request.POST.get('caption', snippet.caption)
        
        if 'image' in request.FILES:
            snippet.image = request.FILES['image']
        
        snippet.save()
        return JsonResponse({'success': True, 'message': '片段已更新'})
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def reorder_steps(request, slug):
    """重新排序步驟 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        import json
        try:
            order_data = json.loads(request.body)
            for item in order_data:
                TutorialStep.objects.filter(
                    pk=item['id'],
                    tutorial=tutorial
                ).update(order=item['order'])
            return JsonResponse({'success': True, 'message': '順序已更新'})
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'success': False, 'message': '資料格式錯誤'}, status=400)
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def reorder_snippets(request, slug):
    """重新排序片段 (AJAX)"""
    tutorial = get_object_or_404(Tutorial, slug=slug)
    
    if not tutorial.maintainers.filter(user=request.user).exists():
        return JsonResponse({'success': False, 'message': '權限不足'}, status=403)
    
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            step_id = data.get('step_id')
            snippets = data.get('snippets', [])
            
            # 驗證 step 屬於此 tutorial
            step = get_object_or_404(TutorialStep, pk=step_id, tutorial=tutorial)
            
            for item in snippets:
                StepSnippet.objects.filter(
                    pk=item['id'],
                    step=step
                ).update(order=item['order'])
            return JsonResponse({'success': True, 'message': '順序已更新'})
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'success': False, 'message': '資料格式錯誤'}, status=400)
    
    return JsonResponse({'success': False, 'message': '無效請求'}, status=405)


@login_required
def update_reading_time(request):
    """更新閱讀時間 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只接受 POST 請求'}, status=405)
    
    tutorial_id = request.POST.get('tutorial_id')
    seconds = request.POST.get('seconds', 0)
    
    try:
        seconds = int(seconds)
        tutorial = Tutorial.objects.get(pk=tutorial_id, is_published=True)
        
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
    """建立問題 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只接受 POST 請求'}, status=405)
    
    step_id = request.POST.get('step_id')
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'success': False, 'message': '問題內容不可為空'}, status=400)
    
    try:
        step = TutorialStep.objects.get(pk=step_id)
        
        question = Question.objects.create(
            step=step,
            user=request.user,
            content=content
        )
        
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
    """建立回答 API"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '只接受 POST 請求'}, status=405)
    
    question_id = request.POST.get('question_id')
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'success': False, 'message': '回答內容不可為空'}, status=400)
    
    try:
        question = Question.objects.get(pk=question_id)
        
        answer = Answer.objects.create(
            question=question,
            user=request.user,
            content=content
        )
        
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
        
        contributions = TutorialMaintainer.objects.filter(
            user=user
        ).select_related('tutorial').order_by('-contribution_score')
        
        context['contributions'] = contributions
        context['total_tutorials'] = contributions.count()
        context['total_contribution'] = contributions.aggregate(
            total=Sum('contribution_score')
        )['total'] or 0
        context['is_own_profile'] = (
            self.request.user.is_authenticated and
            self.request.user == user
        )
        
        return context


@login_required
def my_tutorials(request):
    """我的教材列表"""
    contributions = TutorialMaintainer.objects.filter(
        user=request.user
    ).select_related('tutorial').order_by('-tutorial__updated_at')
    
    return render(request, 'tutorialhub/my_tutorials.html', {
        'contributions': contributions,
    })


def analytics_view(request):
    """統計分析視圖"""
    popular_tutorials = Tutorial.objects.filter(
        is_published=True
    ).annotate(
        total_time=Sum('reading_logs__total_seconds'),
        reader_count=Count('reading_logs', distinct=True)
    ).order_by('-total_time')[:10]

    top_contributors = User.objects.annotate(
        total_contribution=Sum('tutorial_contributions__contribution_score'),
        tutorial_count=Count('tutorial_contributions', distinct=True)
    ).filter(
        total_contribution__gt=0
    ).order_by('-total_contribution')[:10]

    top_readers = User.objects.annotate(
        total_time=Sum('tutorial_reading_logs__total_seconds')
    ).filter(
        total_time__gt=0
    ).order_by('-total_time')[:10]

    # 為每個讀者添加計算好的分鐘數
    for reader in top_readers:
        reader.total_minutes = round(reader.total_time / 60) if reader.total_time else 0

    context = {
        'popular_tutorials': popular_tutorials,
        'top_contributors': top_contributors,
        'top_readers': top_readers,
    }

    return render(request, 'tutorialhub/analytics.html', context)
