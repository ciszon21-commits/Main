from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import Announcement, DroneReservation, DroneReviewer
from .forms import ReservationForm, ReviewForm, AnnouncementForm


class ReviewerRequiredMixin(UserPassesTestMixin):
    """只允許簽核人訪問的 Mixin"""
    def test_func(self):
        try:
            reviewer_profile = self.request.user.drone_reviewer_profile
            return reviewer_profile.is_active
        except DroneReviewer.DoesNotExist:
            return False
    
    def handle_no_permission(self):
        messages.error(self.request, '您沒有權限訪問此頁面。')
        return redirect('drone:dashboard')


class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard 首頁 - 顯示公告與行事曆"""
    template_name = 'DroneReservation/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 取得啟用的公告
        context['announcements'] = Announcement.objects.filter(is_active=True)[:5]
        
        # 檢查使用者是否為簽核人
        try:
            reviewer_profile = self.request.user.drone_reviewer_profile
            context['is_reviewer'] = reviewer_profile.is_active
            context['pending_count'] = DroneReservation.objects.filter(
                status='pending'
            ).count()
        except DroneReviewer.DoesNotExist:
            context['is_reviewer'] = False
            context['pending_count'] = 0
        
        # 使用者的申請數量
        context['my_reservation_count'] = DroneReservation.objects.filter(
            applicant=self.request.user
        ).count()
        
        return context


class ReservationCreateView(LoginRequiredMixin, CreateView):
    """新增預約申請"""
    model = DroneReservation
    form_class = ReservationForm
    template_name = 'DroneReservation/reservation_form.html'
    success_url = reverse_lazy('drone:my_reservations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '新增無人機預約申請'
        context['submit_text'] = '送出申請'
        user = self.request.user
        # 優先使用 last_name（中文姓名可能存在這裡），再用 full_name，最後用 username
        context['applicant_name'] = user.last_name or user.get_full_name() or user.username
        return context

    def form_valid(self, form):
        form.instance.applicant = self.request.user
        response = super().form_valid(form)
        
        # 發送郵件通知簽核人
        self.send_notification_to_reviewers(form.instance)
        
        messages.success(self.request, '預約申請已送出，等待簽核人審核。')
        return response

    def send_notification_to_reviewers(self, reservation):
        """發送通知給所有啟用的簽核人"""
        reviewers = DroneReviewer.objects.filter(is_active=True).select_related('user')
        reviewer_emails = [r.user.email for r in reviewers if r.user.email]
        
        if reviewer_emails:
            try:
                send_mail(
                    subject=f'[無人機預約] 新申請待審核 - {reservation.applicant.get_full_name() or reservation.applicant.username}',
                    message=f"""您好，

有一筆新的無人機預約申請待審核：

申請人：{reservation.applicant.get_full_name() or reservation.applicant.username}
使用時間：{reservation.usage_start_datetime.strftime('%Y/%m/%d %H:%M')} ~ {reservation.usage_end_datetime.strftime('%Y/%m/%d %H:%M')}
地點：{reservation.location}
計畫編號：{reservation.project_number}
申請理由：{reservation.reason}

請登入系統進行審核。

此為系統自動發送郵件，請勿直接回覆。
""",
                    from_email=settings.SYSTEM_EMAIL,
                    recipient_list=reviewer_emails,
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    """編輯預約申請"""
    model = DroneReservation
    form_class = ReservationForm
    template_name = 'DroneReservation/reservation_form.html'
    success_url = reverse_lazy('drone:my_reservations')

    def get_queryset(self):
        # 只允許申請人編輯自己的申請，且狀態為申請中
        return DroneReservation.objects.filter(
            applicant=self.request.user,
            status='pending'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '編輯無人機預約申請'
        context['submit_text'] = '更新申請'
        user = self.request.user
        context['applicant_name'] = user.last_name or user.get_full_name() or user.username
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, '預約申請已更新。')
        return super().form_valid(form)


class MyReservationsView(LoginRequiredMixin, ListView):
    """申請人管理頁面 - 我的預約"""
    model = DroneReservation
    template_name = 'DroneReservation/my_reservations.html'
    context_object_name = 'reservations'
    paginate_by = 10

    def get_queryset(self):
        queryset = DroneReservation.objects.filter(
            applicant=self.request.user
        ).select_related('reviewer')
        
        # 狀態篩選
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['status_choices'] = DroneReservation.STATUS_CHOICES
        return context


class PendingApprovalsView(LoginRequiredMixin, ListView):
    """簽核人管理頁面 - 待審核預約"""
    model = DroneReservation
    template_name = 'DroneReservation/pending_approvals.html'
    context_object_name = 'reservations'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        # 檢查是否為簽核人
        try:
            reviewer_profile = request.user.drone_reviewer_profile
            if not reviewer_profile.is_active:
                messages.error(request, '您沒有權限訪問此頁面。')
                return redirect('drone:dashboard')
        except DroneReviewer.DoesNotExist:
            messages.error(request, '您沒有權限訪問此頁面。')
            return redirect('drone:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = DroneReservation.objects.select_related('applicant', 'reviewer')
        
        # 狀態篩選
        status = self.request.GET.get('status', 'pending')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'pending')
        context['status_choices'] = DroneReservation.STATUS_CHOICES
        context['pending_count'] = DroneReservation.objects.filter(status='pending').count()
        return context


class ReservationDetailView(LoginRequiredMixin, DetailView):
    """預約詳情頁"""
    model = DroneReservation
    template_name = 'DroneReservation/reservation_detail.html'
    context_object_name = 'reservation'

    def get_queryset(self):
        return DroneReservation.objects.select_related('applicant', 'reviewer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation = self.object
        user = self.request.user
        
        context['can_edit'] = reservation.can_edit(user)
        context['can_cancel'] = reservation.can_cancel(user)
        context['can_review'] = reservation.can_review(user)
        
        if context['can_review']:
            context['review_form'] = ReviewForm()
        
        return context


@login_required
def review_reservation(request, pk):
    """簽核預約"""
    reservation = get_object_or_404(DroneReservation, pk=pk)
    
    # 檢查權限
    if not reservation.can_review(request.user):
        messages.error(request, '您沒有權限簽核此預約。')
        return redirect('drone:pending_approvals')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            
            reservation.reviewer = request.user
            reservation.review_datetime = timezone.now()
            
            if action == 'approve':
                reservation.status = 'approved'
                messages.success(request, '預約已核准。')
            else:
                reservation.status = 'rejected'
                reservation.rejection_reason = form.cleaned_data['rejection_reason']
                messages.success(request, '預約已拒絕。')
            
            reservation.save()
            
            # 發送通知給申請人
            send_review_notification(reservation)
            
            return redirect('drone:pending_approvals')
        else:
            messages.error(request, '表單驗證失敗，請重新填寫。')
    
    return redirect('drone:reservation_detail', pk=pk)


@login_required
def cancel_reservation(request, pk):
    """取消預約"""
    reservation = get_object_or_404(DroneReservation, pk=pk)
    
    # 檢查權限
    if not reservation.can_cancel(request.user):
        messages.error(request, '您沒有權限取消此預約。')
        return redirect('drone:my_reservations')
    
    if request.method == 'POST':
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, '預約已取消。')
        
        # 如果原本是已核准，通知簽核人
        if reservation.reviewer:
            send_cancel_notification(reservation)
    
    return redirect('drone:my_reservations')


def send_review_notification(reservation):
    """發送簽核結果通知給申請人"""
    if not reservation.applicant.email:
        return
    
    if reservation.status == 'approved':
        subject = f'[無人機預約] 您的申請已核准'
        message = f"""您好，

您的無人機預約申請已核准：

使用時間：{reservation.usage_start_datetime.strftime('%Y/%m/%d %H:%M')} ~ {reservation.usage_end_datetime.strftime('%Y/%m/%d %H:%M')}
地點：{reservation.location}
簽核人：{reservation.reviewer.get_full_name() or reservation.reviewer.username}

請依照核准時間使用無人機。

此為系統自動發送郵件，請勿直接回覆。
"""
    else:
        subject = f'[無人機預約] 您的申請已被拒絕'
        message = f"""您好，

您的無人機預約申請已被拒絕：

使用時間：{reservation.usage_start_datetime.strftime('%Y/%m/%d %H:%M')} ~ {reservation.usage_end_datetime.strftime('%Y/%m/%d %H:%M')}
地點：{reservation.location}
簽核人：{reservation.reviewer.get_full_name() or reservation.reviewer.username}
拒絕理由：{reservation.rejection_reason}

如有疑問，請聯繫簽核人。

此為系統自動發送郵件，請勿直接回覆。
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.SYSTEM_EMAIL,
            recipient_list=[reservation.applicant.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_cancel_notification(reservation):
    """發送取消通知給簽核人"""
    if not reservation.reviewer or not reservation.reviewer.email:
        return
    
    try:
        send_mail(
            subject=f'[無人機預約] 預約已取消 - {reservation.applicant.get_full_name() or reservation.applicant.username}',
            message=f"""您好，

以下無人機預約已被申請人取消：

申請人：{reservation.applicant.get_full_name() or reservation.applicant.username}
使用時間：{reservation.usage_start_datetime.strftime('%Y/%m/%d %H:%M')} ~ {reservation.usage_end_datetime.strftime('%Y/%m/%d %H:%M')}
地點：{reservation.location}

此為系統自動發送郵件，請勿直接回覆。
""",
            from_email=settings.SYSTEM_EMAIL,
            recipient_list=[reservation.reviewer.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


@login_required
def calendar_events_api(request):
    """行事曆事件 API - 返回 FullCalendar 格式的事件"""
    # 取得查詢參數
    start = request.GET.get('start', '')
    end = request.GET.get('end', '')
    
    # 篩選顯示的預約（申請中與已核准）
    queryset = DroneReservation.objects.filter(
        status__in=['pending', 'approved']
    ).select_related('applicant')
    
    # 時間範圍篩選
    if start:
        queryset = queryset.filter(usage_end_datetime__gte=start)
    if end:
        queryset = queryset.filter(usage_start_datetime__lte=end)
    
    events = []
    for reservation in queryset:
        # 根據狀態設定顏色
        if reservation.status == 'pending':
            color = '#f59e0b'  # 黃色 - 申請中
            title_prefix = '[申請中] '
        else:
            color = '#10b981'  # 綠色 - 已核准
            title_prefix = '[已核准] '
        
        applicant_name = reservation.applicant.get_full_name() or reservation.applicant.username
        
        events.append({
            'id': reservation.id,
            'title': f"{title_prefix}{reservation.project_number} - {applicant_name}",
            'start': reservation.usage_start_datetime.isoformat(),
            'end': reservation.usage_end_datetime.isoformat(),
            'color': color,
            'url': reverse('drone:reservation_detail', kwargs={'pk': reservation.id}),
            'extendedProps': {
                'status': reservation.status,
                'applicant': applicant_name,
                'location': reservation.location,
                'project_number': reservation.project_number,
            }
        })
    
    return JsonResponse(events, safe=False)


# ========================================
# 公告管理視圖（僅限簽核人）
# ========================================

class AnnouncementListView(LoginRequiredMixin, ReviewerRequiredMixin, ListView):
    """公告列表"""
    model = Announcement
    template_name = 'DroneReservation/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        return Announcement.objects.all().order_by('-is_pinned', '-updated_at')


class AnnouncementCreateView(LoginRequiredMixin, ReviewerRequiredMixin, CreateView):
    """新增公告"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'DroneReservation/announcement_form.html'
    success_url = reverse_lazy('drone:announcement_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '新增公告'
        context['submit_text'] = '發佈公告'
        return context

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '公告已發佈。')
        return super().form_valid(form)


class AnnouncementUpdateView(LoginRequiredMixin, ReviewerRequiredMixin, UpdateView):
    """編輯公告"""
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'DroneReservation/announcement_form.html'
    success_url = reverse_lazy('drone:announcement_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = '編輯公告'
        context['submit_text'] = '更新公告'
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, '公告已更新。')
        return super().form_valid(form)


class AnnouncementDeleteView(LoginRequiredMixin, ReviewerRequiredMixin, DeleteView):
    """刪除公告"""
    model = Announcement
    success_url = reverse_lazy('drone:announcement_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, '公告已刪除。')
        return super().delete(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    """公告詳情（所有登入用戶可見）"""
    model = Announcement
    template_name = 'DroneReservation/announcement_detail.html'
    context_object_name = 'announcement'

    def get_queryset(self):
        return Announcement.objects.filter(is_active=True)
