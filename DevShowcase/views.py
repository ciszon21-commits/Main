from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.db.models import Count, Prefetch, Q
from django.contrib import messages
from .models import Achievement, Category, ViewLog, Comment
from .forms import AchievementForm, CommentForm, CategoryForm
from .utils import send_comment_notification


class AchievementListView(ListView):
    """成果列表頁面 - 按分類顯示所有成果"""
    model = Category
    template_name = 'DevShowcase/achievement_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        # 取得所有分類，並預載入所有成果（前端負責顯示控制）
        return Category.objects.prefetch_related(
            Prefetch(
                'achievements',
                queryset=Achievement.objects.order_by('-view_count', '-created_at')
            )
        ).all()


class AchievementDetailView(DetailView):
    """成果詳細頁面"""
    model = Achievement
    template_name = 'DevShowcase/achievement_detail.html'
    context_object_name = 'achievement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        achievement = self.object
        
        # 取得留言
        context['comments'] = achievement.comments.select_related('user').all()
        context['comment_form'] = CommentForm()
        
        # 記錄瀏覽
        if self.request.user.is_authenticated:
            view_log, created = ViewLog.objects.get_or_create(
                achievement=achievement,
                user=self.request.user
            )
            if created:
                # 更新瀏覽次數
                achievement.view_count += 1
                achievement.save(update_fields=['view_count'])
        
        return context


class AchievementCreateView(LoginRequiredMixin, CreateView):
    """建立成果"""
    model = Achievement
    form_class = AchievementForm
    template_name = 'DevShowcase/achievement_form.html'
    success_url = reverse_lazy('devshowcase:achievement_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '成果建立成功！')
        return super().form_valid(form)


class AchievementUpdateView(LoginRequiredMixin, UpdateView):
    """編輯成果"""
    model = Achievement
    form_class = AchievementForm
    template_name = 'DevShowcase/achievement_form.html'

    def get_success_url(self):
        return reverse_lazy('devshowcase:achievement_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        # 只允許建立者和協同開發者編輯
        qs = super().get_queryset()
        user = self.request.user
        return qs.filter(
            Q(created_by=user) | Q(developers=user)
        ).distinct()

    def form_valid(self, form):
        messages.success(self.request, '成果更新成功！')
        return super().form_valid(form)


@login_required
def comment_create(request, pk):
    """建立留言（AJAX）"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    achievement = get_object_or_404(Achievement, pk=pk)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.achievement = achievement
        comment.user = request.user
        comment.save()
        
        # 發送郵件通知
        try:
            send_comment_notification(achievement, comment)
        except Exception as e:
            print(f"郵件通知失敗: {e}")
        
        return JsonResponse({
            'success': True,
            'comment': {
                'user': comment.user.get_full_name() or comment.user.get_username(),
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


# ===== Category Management Views (Staff Only) =====

class StaffRequiredMixin(UserPassesTestMixin):
    """限制只有 staff 使用者可以存取"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, '您沒有權限存取此頁面')
        return redirect('devshowcase:achievement_list')


class CategoryListView(StaffRequiredMixin, ListView):
    """分類管理列表頁面"""
    model = Category
    template_name = 'DevShowcase/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.annotate(
            achievement_count=Count('achievements')
        ).order_by('order', 'name')


class CategoryCreateView(StaffRequiredMixin, CreateView):
    """新增分類"""
    model = Category
    form_class = CategoryForm
    template_name = 'DevShowcase/category_form.html'
    success_url = reverse_lazy('devshowcase:category_list')

    def form_valid(self, form):
        messages.success(self.request, '分類建立成功！')
        return super().form_valid(form)


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    """編輯分類"""
    model = Category
    form_class = CategoryForm
    template_name = 'DevShowcase/category_form.html'
    success_url = reverse_lazy('devshowcase:category_list')

    def form_valid(self, form):
        messages.success(self.request, '分類更新成功！')
        return super().form_valid(form)


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    """刪除分類"""
    model = Category
    template_name = 'DevShowcase/category_confirm_delete.html'
    success_url = reverse_lazy('devshowcase:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['achievement_count'] = self.object.achievements.count()
        return context

    def form_valid(self, form):
        if self.object.achievements.exists():
            messages.error(self.request, '無法刪除此分類，因為仍有成果使用此分類。請先移除或更改相關成果的分類。')
            return redirect('devshowcase:category_list')
        messages.success(self.request, '分類已刪除！')
        return super().form_valid(form)
