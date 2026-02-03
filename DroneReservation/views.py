from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import localtime
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User

from .models import Announcement, DroneReservation, DroneReviewer, SiteSettings, EmailTemplate
from .forms import ReservationForm, ReviewForm, AnnouncementForm, SiteSettingsForm, ReviewerCancelForm, ReviewerTimeEditForm, EmailTemplateForm


def format_local_datetime(dt):
    """將 datetime 轉換為本地時區並格式化"""
    return localtime(dt).strftime('%Y/%m/%d %H:%M')


def send_templated_email(email_type, context, recipient_list):
    """使用資料庫模板發送郵件"""
    if not recipient_list:
        return
    
    template = EmailTemplate.get_template(email_type)
    subject, body = template.render(context)
    
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list,
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")


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
        
        # 取得網站設定
        context['site_settings'] = SiteSettings.get_settings()
        
        # 取得啟用的公告
        context['announcements'] = Announcement.objects.filter(is_active=True)[:5]
        
        # 檢查使用者是否為簽核人
        try:
            reviewer_profile = self.request.user.drone_reviewer_profile
            context['is_reviewer'] = reviewer_profile.is_active
            context['is_admin'] = reviewer_profile.is_active and reviewer_profile.can_manage_reviewers
            context['pending_count'] = DroneReservation.objects.filter(
                status='pending'
            ).count()
        except DroneReviewer.DoesNotExist:
            context['is_reviewer'] = False
            context['is_admin'] = False
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
        """發送通知給所有啟用且接收郵件的簽核人"""
        reviewers = DroneReviewer.objects.filter(is_active=True, receive_email=True).select_related('user')
        reviewer_emails = [r.user.email for r in reviewers if r.user.email]
        
        context = {
            'applicant_name': reservation.applicant.get_full_name() or reservation.applicant.username,
            'start_time': format_local_datetime(reservation.usage_start_datetime),
            'end_time': format_local_datetime(reservation.usage_end_datetime),
            'location': reservation.location,
            'project_number': reservation.project_number,
            'reason': reservation.reason,
        }
        send_templated_email('new_application', context, reviewer_emails)


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    """編輯預約申請"""
    model = DroneReservation
    form_class = ReservationForm
    template_name = 'DroneReservation/reservation_form.html'
    success_url = reverse_lazy('drone:my_reservations')

    def get_queryset(self):
        # 申請人只能編輯申請中的預約（已核准後只有審核人可修改時間）
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
        # 儲存舊的時間資訊（用於已核准預約的時間變更通知）
        reservation = self.get_object()
        old_start = reservation.usage_start_datetime
        old_end = reservation.usage_end_datetime
        old_status = reservation.status
        
        response = super().form_valid(form)
        
        # 取得更新後的預約
        updated_reservation = form.instance
        
        # 檢查時間是否變動
        time_changed = (
            old_start != updated_reservation.usage_start_datetime or
            old_end != updated_reservation.usage_end_datetime
        )
        
        if old_status == 'approved' and time_changed:
            # 已核准預約且時間有變動，發送通知給申請人與審核人
            self.send_time_change_notification(
                updated_reservation, old_start, old_end
            )
            messages.success(self.request, '預約時間已更新，已通知相關人員。')
        elif old_status == 'pending':
            # 申請中的預約編輯，通知簽核人
            self.send_edit_notification_to_reviewers(updated_reservation)
            messages.success(self.request, '預約申請已更新。')
        else:
            messages.success(self.request, '預約申請已更新。')
        
        return response

    def send_time_change_notification(self, reservation, old_start, old_end):
        """發送時間變更通知給申請人與審核人"""
        recipients = []
        if reservation.applicant.email:
            recipients.append(reservation.applicant.email)
        if reservation.reviewer and reservation.reviewer.email:
            recipients.append(reservation.reviewer.email)
        
        context = {
            'applicant_name': reservation.applicant.get_full_name() or reservation.applicant.username,
            'start_time': format_local_datetime(reservation.usage_start_datetime),
            'end_time': format_local_datetime(reservation.usage_end_datetime),
            'location': reservation.location,
            'project_number': reservation.project_number,
            'old_start_time': format_local_datetime(old_start),
            'old_end_time': format_local_datetime(old_end),
        }
        send_templated_email('time_changed', context, recipients)

    def send_edit_notification_to_reviewers(self, reservation):
        """發送編輯通知給所有啟用且接收郵件的簽核人"""
        reviewers = DroneReviewer.objects.filter(is_active=True, receive_email=True).select_related('user')
        reviewer_emails = [r.user.email for r in reviewers if r.user.email]
        
        context = {
            'applicant_name': reservation.applicant.get_full_name() or reservation.applicant.username,
            'start_time': format_local_datetime(reservation.usage_start_datetime),
            'end_time': format_local_datetime(reservation.usage_end_datetime),
            'location': reservation.location,
            'project_number': reservation.project_number,
            'reason': reservation.reason,
        }
        send_templated_email('new_application', context, reviewer_emails)


class ReviewerUpdateView(LoginRequiredMixin, ReviewerRequiredMixin, UpdateView):
    """審核人編輯已核准預約時間"""
    model = DroneReservation
    form_class = ReviewerTimeEditForm
    template_name = 'DroneReservation/reviewer_edit_form.html'
    
    def get_success_url(self):
        return reverse('drone:reservation_detail', kwargs={'pk': self.object.pk})

    def get_queryset(self):
        # 只能編輯已核准的預約
        return DroneReservation.objects.filter(status='approved')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservation'] = self.object
        return context

    def form_valid(self, form):
        # 儲存舊的時間資訊
        reservation = self.get_object()
        old_start = reservation.usage_start_datetime
        old_end = reservation.usage_end_datetime
        
        response = super().form_valid(form)
        
        # 取得更新後的預約
        updated_reservation = form.instance
        
        # 檢查時間是否變動
        time_changed = (
            old_start != updated_reservation.usage_start_datetime or
            old_end != updated_reservation.usage_end_datetime
        )
        
        if time_changed:
            # 發送時間變更通知給申請人
            self.send_reviewer_time_change_notification(
                updated_reservation, old_start, old_end
            )
            messages.success(self.request, '預約時間已更新，已通知申請人。')
        else:
            messages.info(self.request, '預約時間未變更。')
        
        return response

    def send_reviewer_time_change_notification(self, reservation, old_start, old_end):
        """發送時間變更通知給申請人"""
        if not reservation.applicant.email:
            return
        
        applicant_name = reservation.applicant.get_full_name() or reservation.applicant.username
        reviewer_name = self.request.user.get_full_name() or self.request.user.username
        
        message = f"""您好，

您的無人機預約時間已被審核人修改：

申請人：{applicant_name}
地點：{reservation.location}
計畫編號：{reservation.project_number}

【時間變更】
原時間：{format_local_datetime(old_start)} ~ {format_local_datetime(old_end)}
新時間：{format_local_datetime(reservation.usage_start_datetime)} ~ {format_local_datetime(reservation.usage_end_datetime)}

修改人：{reviewer_name}

如有疑問，請聯繫簽核人(#07130)。

此為系統自動發送郵件，請勿直接回覆。
"""
        
        try:
            send_mail(
                subject=f'[無人機預約] 您的預約時間已被修改',
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[reservation.applicant.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")


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
        context['can_reviewer_cancel'] = reservation.can_reviewer_cancel(user)
        context['can_reviewer_edit'] = reservation.can_reviewer_edit(user)
        
        if context['can_review']:
            context['review_form'] = ReviewForm()
        
        if context['can_reviewer_cancel']:
            context['reviewer_cancel_form'] = ReviewerCancelForm()
        
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
    
    context = {
        'applicant_name': reservation.applicant.get_full_name() or reservation.applicant.username,
        'start_time': format_local_datetime(reservation.usage_start_datetime),
        'end_time': format_local_datetime(reservation.usage_end_datetime),
        'location': reservation.location,
        'reviewer_name': reservation.reviewer.get_full_name() or reservation.reviewer.username,
        'rejection_reason': reservation.rejection_reason or '',
    }
    
    email_type = 'approved' if reservation.status == 'approved' else 'rejected'
    send_templated_email(email_type, context, [reservation.applicant.email])


def send_cancel_notification(reservation):
    """發送取消通知給簽核人"""
    if not reservation.reviewer or not reservation.reviewer.email:
        return
    
    context = {
        'applicant_name': reservation.applicant.get_full_name() or reservation.applicant.username,
        'start_time': format_local_datetime(reservation.usage_start_datetime),
        'end_time': format_local_datetime(reservation.usage_end_datetime),
        'location': reservation.location,
    }
    send_templated_email('cancelled', context, [reservation.reviewer.email])


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


# ========================================
# 管理員相關視圖
# ========================================

class AdminRequiredMixin(UserPassesTestMixin):
    """只允許管理簽核人的人訪問"""
    def test_func(self):
        try:
            reviewer_profile = self.request.user.drone_reviewer_profile
            return reviewer_profile.is_active and reviewer_profile.can_manage_reviewers
        except DroneReviewer.DoesNotExist:
            return False
    
    def handle_no_permission(self):
        messages.error(self.request, '您沒有權限訪問此頁面。')
        return redirect('drone:dashboard')


class SettingsView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """系統設定頁面"""
    template_name = 'DroneReservation/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.get_settings()
        context['site_settings_form'] = SiteSettingsForm(instance=context['site_settings'])
        context['reviewers'] = DroneReviewer.objects.select_related('user').order_by('-can_manage_reviewers', '-is_active', 'user__last_name')
        context['all_users'] = User.objects.filter(is_active=True).order_by('last_name', 'username')
        
        # 確保所有郵件模板都存在
        EmailTemplate.ensure_all_templates()
        context['email_templates'] = EmailTemplate.objects.all().order_by('email_type')
        
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        
        if action == 'update_settings':
            site_settings = SiteSettings.get_settings()
            form = SiteSettingsForm(request.POST, instance=site_settings)
            if form.is_valid():
                settings_obj = form.save(commit=False)
                settings_obj.updated_by = request.user
                settings_obj.save()
                messages.success(request, '設定已更新。')
            else:
                messages.error(request, '設定更新失敗。')
        
        elif action == 'add_reviewer':
            user_id = request.POST.get('user_id')
            if user_id:
                user = get_object_or_404(User, pk=user_id)
                reviewer, created = DroneReviewer.objects.get_or_create(user=user)
                if not created:
                    reviewer.is_active = True
                    reviewer.save()
                    messages.success(request, f'已重新啟用簽核人：{user.get_full_name() or user.username}')
                else:
                    messages.success(request, f'已新增簽核人：{user.get_full_name() or user.username}')
        
        elif action == 'update_reviewer':
            reviewer_id = request.POST.get('reviewer_id')
            if reviewer_id:
                reviewer = get_object_or_404(DroneReviewer, pk=reviewer_id)
                reviewer.is_active = request.POST.get('is_active') == 'on'
                reviewer.receive_email = request.POST.get('receive_email') == 'on'
                reviewer.can_manage_reviewers = request.POST.get('can_manage_reviewers') == 'on'
                reviewer.save()
                messages.success(request, f'已更新簽核人設定：{reviewer.user.get_full_name() or reviewer.user.username}')
        
        elif action == 'remove_reviewer':
            reviewer_id = request.POST.get('reviewer_id')
            if reviewer_id:
                reviewer = get_object_or_404(DroneReviewer, pk=reviewer_id)
                reviewer.is_active = False
                reviewer.save()
                messages.success(request, f'已停用簽核人：{reviewer.user.get_full_name() or reviewer.user.username}')
        
        elif action == 'update_template':
            template_id = request.POST.get('template_id')
            if template_id:
                template = get_object_or_404(EmailTemplate, pk=template_id)
                form = EmailTemplateForm(request.POST, instance=template)
                if form.is_valid():
                    form.save()
                    messages.success(request, f'已更新郵件模板：{template.get_email_type_display()}')
                else:
                    messages.error(request, '郵件模板更新失敗。')
        
        return redirect('drone:settings')


@login_required
def reviewer_cancel_reservation(request, pk):
    """簽核人取消已核准的預約"""
    reservation = get_object_or_404(DroneReservation, pk=pk)
    
    # 檢查權限
    if not reservation.can_reviewer_cancel(request.user):
        messages.error(request, '您沒有權限取消此預約。')
        return redirect('drone:pending_approvals')
    
    if request.method == 'POST':
        form = ReviewerCancelForm(request.POST)
        if form.is_valid():
            reservation.status = 'cancelled'
            reservation.cancellation_reason = form.cleaned_data['cancellation_reason']
            reservation.save()
            messages.success(request, '預約已取消。')
            
            # 發送通知給申請人
            send_reviewer_cancel_notification(reservation, request.user)
            
            return redirect('drone:pending_approvals')
        else:
            messages.error(request, '請填寫取消理由。')
    
    return redirect('drone:reservation_detail', pk=pk)


def send_reviewer_cancel_notification(reservation, reviewer):
    """發送簽核人取消通知給申請人"""
    if not reservation.applicant.email:
        return
    
    try:
        send_mail(
            subject=f'[無人機預約] 您的核准預約已被取消',
            message=f"""您好，

您的無人機預約已被簽核人取消：

使用時間：{format_local_datetime(reservation.usage_start_datetime)} ~ {format_local_datetime(reservation.usage_end_datetime)}
地點：{reservation.location}
取消人：{reviewer.get_full_name() or reviewer.username}
取消理由：{reservation.cancellation_reason}

如有疑問，請聯繫簽核人(#07130)。

此為系統自動發送郵件，請勿直接回覆。
""",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[reservation.applicant.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email: {e}")

