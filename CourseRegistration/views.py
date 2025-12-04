from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, FileResponse, Http404
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Course, Registration, PDFDownloadLog, CourseComment
from .forms import CourseForm, CommentForm


class CourseListView(LoginRequiredMixin, ListView):
    """課程列表視圖"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Course.objects.all()
        
        # 篩選功能
        filter_type = self.request.GET.get('filter', 'all')
        now = timezone.now()
        
        if filter_type == 'open':
            # 報名開放中
            queryset = queryset.filter(
                registration_start__lte=now,
                registration_end__gte=now
            )
        elif filter_type == 'upcoming':
            # 即將開始
            queryset = queryset.filter(registration_start__gt=now)
        elif filter_type == 'closed':
            # 已結束
            queryset = queryset.filter(registration_end__lt=now)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_filter'] = self.request.GET.get('filter', 'all')
        return context


class CourseDetailView(LoginRequiredMixin, DetailView):
    """課程詳情視圖"""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        
        # 檢查使用者是否已報名
        context['is_registered'] = Registration.objects.filter(
            course=course,
            user=user
        ).exists()
        
        # 檢查是否為課程建立者
        context['is_creator'] = course.created_by == user
        
        # 取得報名名單（前5名）
        context['recent_registrations'] = course.registrations.select_related('user')[:5]
        
        # 取得留言列表（按時間倒序）
        context['comments'] = course.comments.select_related('user').all()
        
        # 留言表單
        context['comment_form'] = CommentForm()
        
        return context


class CourseCreateView(LoginRequiredMixin, CreateView):
    """建立課程視圖"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '課程建立成功！')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '建立新課程'
        return context


class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """編輯課程視圖"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    
    def test_func(self):
        """檢查是否為課程建立者"""
        course = self.get_object()
        return self.request.user == course.created_by
    
    def form_valid(self, form):
        messages.success(self.request, '課程更新成功！')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '編輯課程'
        return context


class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """刪除課程視圖"""
    model = Course
    template_name = 'courses/course_confirm_delete.html'
    success_url = reverse_lazy('courses:course_list')
    
    def test_func(self):
        """檢查是否為課程建立者"""
        course = self.get_object()
        return self.request.user == course.created_by
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '課程已刪除')
        return super().delete(request, *args, **kwargs)


@login_required
def register_course(request, pk):
    """報名課程"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '無效的請求方法'}, status=400)
    
    course = get_object_or_404(Course, pk=pk)
    user = request.user
    
    # 檢查是否已報名
    if Registration.objects.filter(course=course, user=user).exists():
        return JsonResponse({'success': False, 'message': '您已經報名過此課程'})
    
    # 檢查報名期間
    if not course.is_registration_open:
        return JsonResponse({'success': False, 'message': '目前不在報名期間內'})
    
    # 檢查人數限制
    if course.is_full:
        return JsonResponse({'success': False, 'message': '報名人數已額滿'})
    
    # 建立報名記錄
    Registration.objects.create(course=course, user=user)
    
    return JsonResponse({
        'success': True,
        'message': '報名成功！',
        'participants_count': course.current_participants_count
    })


@login_required
def cancel_registration(request, pk):
    """取消報名"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '無效的請求方法'}, status=400)
    
    course = get_object_or_404(Course, pk=pk)
    user = request.user
    
    # 檢查是否已報名
    registration = Registration.objects.filter(course=course, user=user).first()
    if not registration:
        return JsonResponse({'success': False, 'message': '您尚未報名此課程'})
    
    # 檢查是否在報名期間內（只允許在報名期間內取消）
    if not course.is_registration_open:
        return JsonResponse({'success': False, 'message': '報名期間已結束，無法取消報名'})
    
    # 刪除報名記錄
    registration.delete()
    
    return JsonResponse({
        'success': True,
        'message': '已取消報名',
        'participants_count': course.current_participants_count
    })


@login_required
def download_pdf(request, pk):
    """下載 PDF 附件"""
    course = get_object_or_404(Course, pk=pk)
    
    if not course.pdf_file:
        raise Http404('此課程沒有 PDF 附件')
    
    # 記錄下載
    PDFDownloadLog.objects.create(course=course, user=request.user)
    
    # 提供檔案下載
    try:
        return FileResponse(
            course.pdf_file.open('rb'),
            as_attachment=True,
            filename=f'{course.title}.pdf'
        )
    except Exception as e:
        raise Http404('檔案不存在')


class RegistrationListView(LoginRequiredMixin, ListView):
    """報名名單視圖"""
    model = Registration
    template_name = 'courses/registration_list.html'
    context_object_name = 'registrations'
    paginate_by = 50
    
    def get_queryset(self):
        self.course = get_object_or_404(Course, pk=self.kwargs['pk'])
        return Registration.objects.filter(course=self.course).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context


@login_required
def add_comment(request, pk):
    """新增留言"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '無效的請求方法'}, status=400)
    
    course = get_object_or_404(Course, pk=pk)
    user = request.user
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.course = course
        comment.user = user
        comment.save()
        
        # 發送郵件通知給課程建立者
        try:
            if course.created_by.email:
                subject = f'[課程通知] 您的課程「{course.title}」有新留言'
                message = f'''您好，

您建立的課程「{course.title}」有新的留言：

留言者：{user.username}
留言時間：{comment.created_at.strftime("%Y-%m-%d %H:%M")}
留言內容：
{comment.content}

請點擊以下連結查看詳情：
{request.build_absolute_uri(course.get_absolute_url())}

---
此為系統自動通知郵件，請勿回覆。
'''
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,
                    [course.created_by.email],
                    fail_silently=True,  # 郵件發送失敗不影響留言功能
                )
        except Exception as e:
            # 記錄錯誤但不影響留言功能
            print(f'郵件發送失敗: {e}')
        
        return JsonResponse({
            'success': True,
            'message': '留言發布成功！',
            'comment': {
                'id': comment.id,
                'user': comment.user.username,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': '留言內容不能為空'
        })
