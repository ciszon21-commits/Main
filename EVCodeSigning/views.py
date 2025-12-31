"""
EVCodeSigning Views - 簽章管理視圖
"""
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, FileResponse, Http404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import SigningRequest, SigningFile, SigningAdmin
from .forms import SigningRequestForm, SignedFileUploadForm, RejectForm
from .services import notify_admins_new_request, notify_applicant_completed, notify_applicant_rejected
from .validators import get_allowed_extensions_display


class EVCodeSigningInfoView(TemplateView):
    """EV Code Signing 說明頁面"""
    template_name = 'EVCodeSigning/info.html'


class PublicSigningRecordListView(ListView):
    """公開的簽章記錄列表 - 所有人可查看，但只有有權限者可以點擊連結"""
    model = SigningRequest
    template_name = 'EVCodeSigning/public_record_list.html'
    context_object_name = 'records'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SigningRequest.objects.select_related(
            'applicant', 'assigned_admin', 'assigned_admin__user'
        ).order_by('-created_at')
        
        # 搜尋功能
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(applicant__username__icontains=search_query) |
                Q(applicant__first_name__icontains=search_query) |
                Q(applicant__last_name__icontains=search_query) |
                Q(assigned_admin__user__username__icontains=search_query) |
                Q(assigned_admin__user__first_name__icontains=search_query) |
                Q(assigned_admin__user__last_name__icontains=search_query)
            )
        
        # 狀態過濾
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['status_choices'] = SigningRequest.STATUS_CHOICES
        
        # 權限檢查：決定使用者可以查看哪些申請的詳情
        user = self.request.user
        if user.is_authenticated:
            context['is_superuser'] = user.is_superuser
            context['is_admin'] = hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active
            context['user_id'] = user.id
            # 取得該使用者是簽章管理員時處理過的申請 ID
            if context['is_admin']:
                context['admin_handled_ids'] = list(
                    SigningRequest.objects.filter(
                        assigned_admin__user=user
                    ).values_list('id', flat=True)
                )
            else:
                context['admin_handled_ids'] = []
        else:
            context['is_superuser'] = False
            context['is_admin'] = False
            context['user_id'] = None
            context['admin_handled_ids'] = []
        
        return context


class SigningRequestListView(LoginRequiredMixin, ListView):
    """使用者的簽章申請列表"""
    model = SigningRequest
    template_name = 'EVCodeSigning/request_list.html'
    context_object_name = 'requests'
    
    def get_queryset(self):
        # 一般使用者只能看到自己的申請
        # 簽章管理員可以看到所有申請
        user = self.request.user
        if hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active:
            return SigningRequest.objects.all().select_related('applicant', 'assigned_admin')
        return SigningRequest.objects.filter(applicant=user).select_related('assigned_admin')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self._is_signing_admin()
        return context
    
    def _is_signing_admin(self):
        user = self.request.user
        return hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active


class SigningRequestDetailView(LoginRequiredMixin, DetailView):
    """簽章申請詳情"""
    model = SigningRequest
    template_name = 'EVCodeSigning/request_detail.html'
    context_object_name = 'signing_request'
    
    def get_queryset(self):
        user = self.request.user
        # 管理員可以看到所有申請
        if hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active:
            return SigningRequest.objects.all()
        # 一般使用者只能看到自己的申請
        return SigningRequest.objects.filter(applicant=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_admin'] = self._is_signing_admin()
        context['is_owner'] = self.object.applicant == self.request.user
        context['signed_file_form'] = SignedFileUploadForm()
        context['reject_form'] = RejectForm()
        return context
    
    def _is_signing_admin(self):
        user = self.request.user
        return hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active


class SigningRequestCreateView(LoginRequiredMixin, CreateView):
    """建立簽章申請"""
    model = SigningRequest
    form_class = SigningRequestForm
    template_name = 'EVCodeSigning/request_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allowed_extensions'] = get_allowed_extensions_display()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        files = request.FILES.getlist('files')
        
        # 驗證表單
        if not form.is_valid():
            return self.form_invalid(form)
        
        # 驗證檔案
        if not files:
            messages.error(request, '請至少上傳一個檔案')
            return self.form_invalid(form)
        
        # 驗證檔案格式
        from .validators import validate_signing_file, ALLOWED_EXTENSIONS
        import os
        
        invalid_files = []
        for f in files:
            ext = os.path.splitext(f.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                invalid_files.append(f.name)
        
        if invalid_files:
            messages.error(
                request, 
                f'以下檔案格式不支援：{", ".join(invalid_files)}。'
                f'允許的格式：{get_allowed_extensions_display()}'
            )
            return self.form_invalid(form)
        
        # 儲存申請
        signing_request = form.save(commit=False)
        signing_request.applicant = request.user
        signing_request.save()
        
        # 儲存檔案
        for f in files:
            SigningFile.objects.create(
                request=signing_request,
                original_file=f,
                original_filename=f.name,
                file_size=f.size
            )
        
        # 發送通知給管理員
        notify_admins_new_request(signing_request, request)
        
        messages.success(request, '簽章申請已成功提交！已通知簽章管理員。')
        return redirect('evcodesigning:request_detail', pk=signing_request.pk)
    
    def get_success_url(self):
        return reverse_lazy('evcodesigning:request_list')


class AdminPendingListView(LoginRequiredMixin, ListView):
    """管理員待處理列表"""
    model = SigningRequest
    template_name = 'EVCodeSigning/admin_pending_list.html'
    context_object_name = 'requests'
    
    def dispatch(self, request, *args, **kwargs):
        if not self._is_signing_admin():
            messages.error(request, '您沒有權限存取此頁面')
            return redirect('evcodesigning:request_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return SigningRequest.objects.filter(
            status__in=['pending', 'processing']
        ).select_related('applicant', 'assigned_admin').order_by('created_at')
    
    def _is_signing_admin(self):
        user = self.request.user
        return hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active


@login_required
def download_original_file(request, pk):
    """下載原始檔案（僅管理員）"""
    signing_file = get_object_or_404(SigningFile, pk=pk)
    
    # 檢查權限：管理員可下載
    user = request.user
    is_admin = hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active
    
    if not is_admin:
        messages.error(request, '您沒有權限下載原始檔案')
        return redirect('evcodesigning:request_detail', pk=signing_file.request.pk)
    
    # 如果是第一次下載，標記申請為處理中
    if signing_file.request.status == 'pending':
        signing_file.request.mark_as_processing(user.signing_admin_profile)
    
    try:
        response = FileResponse(
            signing_file.original_file.open('rb'),
            as_attachment=True,
            filename=signing_file.original_filename
        )
        return response
    except FileNotFoundError:
        raise Http404("檔案不存在")


@login_required
def download_signed_file(request, pk):
    """下載簽章後檔案（申請人和管理員都可以）"""
    signing_file = get_object_or_404(SigningFile, pk=pk)
    signing_request = signing_file.request
    
    # 檢查權限
    user = request.user
    is_admin = hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active
    is_owner = signing_request.applicant == user
    
    if not (is_admin or is_owner):
        messages.error(request, '您沒有權限下載此檔案')
        return redirect('evcodesigning:request_list')
    
    if not signing_file.signed_file:
        messages.error(request, '此檔案尚未完成簽章')
        return redirect('evcodesigning:request_detail', pk=signing_request.pk)
    
    try:
        # 使用原始檔名（加上 _signed 標記）
        import os
        name, ext = os.path.splitext(signing_file.original_filename)
        signed_filename = f"{name}_signed{ext}"
        
        response = FileResponse(
            signing_file.signed_file.open('rb'),
            as_attachment=True,
            filename=signed_filename
        )
        return response
    except FileNotFoundError:
        raise Http404("檔案不存在")


@login_required
def upload_signed_file(request, pk):
    """上傳簽章後檔案（僅管理員）"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    signing_file = get_object_or_404(SigningFile, pk=pk)
    
    # 檢查權限
    user = request.user
    if not (hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active):
        return JsonResponse({'success': False, 'error': '您沒有權限執行此操作'}, status=403)
    
    form = SignedFileUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        errors = [str(e) for e in form.errors.values()]
        return JsonResponse({'success': False, 'error': ''.join(errors)}, status=400)
    
    # 儲存簽章後檔案
    signing_file.signed_file = form.cleaned_data['signed_file']
    signing_file.signed_at = timezone.now()
    signing_file.save()
    
    # 更新申請狀態
    signing_request = signing_file.request
    if signing_request.status == 'pending':
        signing_request.mark_as_processing(user.signing_admin_profile)
    
    return JsonResponse({
        'success': True,
        'message': '簽章後檔案已上傳',
        'signed_at': signing_file.signed_at.strftime('%Y-%m-%d %H:%M'),
    })


@login_required
def complete_signing(request, pk):
    """標記簽章完成"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    signing_request = get_object_or_404(SigningRequest, pk=pk)
    
    # 檢查權限
    user = request.user
    if not (hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active):
        return JsonResponse({'success': False, 'error': '您沒有權限執行此操作'}, status=403)
    
    # 檢查是否所有檔案都已簽章
    if not signing_request.all_files_signed:
        return JsonResponse({
            'success': False, 
            'error': f'尚有 {signing_request.file_count - signing_request.signed_file_count} 個檔案未完成簽章'
        }, status=400)
    
    # 標記完成
    if not signing_request.assigned_admin:
        signing_request.assigned_admin = user.signing_admin_profile
    signing_request.mark_as_completed()
    
    # 發送通知給申請人
    notify_applicant_completed(signing_request, request)
    
    return JsonResponse({
        'success': True,
        'message': '已標記簽章完成，已通知申請人',
    })


@login_required
def reject_request(request, pk):
    """退回申請"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    signing_request = get_object_or_404(SigningRequest, pk=pk)
    
    # 檢查權限
    user = request.user
    if not (hasattr(user, 'signing_admin_profile') and user.signing_admin_profile.is_active):
        return JsonResponse({'success': False, 'error': '您沒有權限執行此操作'}, status=403)
    
    form = RejectForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': '請填寫退回原因（至少 10 個字元）'}, status=400)
    
    # 標記退回
    if not signing_request.assigned_admin:
        signing_request.assigned_admin = user.signing_admin_profile
        signing_request.save(update_fields=['assigned_admin'])
    signing_request.mark_as_rejected(form.cleaned_data['reason'])
    
    # 發送通知給申請人
    notify_applicant_rejected(signing_request, request)
    
    return JsonResponse({
        'success': True,
        'message': '已退回申請，已通知申請人',
    })


# ============================================================
# 簽章管理員管理功能 (僅限 superuser)
# ============================================================

class SigningAdminManageView(LoginRequiredMixin, TemplateView):
    """簽章管理員管理頁面 - 僅 superuser 可存取"""
    template_name = 'EVCodeSigning/admin_manage.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, '只有系統管理員可以存取此頁面')
            return redirect('evcodesigning:info')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['signing_admins'] = SigningAdmin.objects.select_related('user', 'created_by').order_by('-created_at')
        return context


@login_required
def search_users_for_admin(request):
    """搜尋使用者 API（用於新增簽章管理員）- 僅 superuser"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '沒有權限'}, status=403)
    
    from django.contrib.auth.models import User
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # 搜尋使用者（排除已經是簽章管理員的）
    existing_admin_ids = SigningAdmin.objects.values_list('user_id', flat=True)
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(
        id__in=existing_admin_ids
    ).order_by('username')[:10]
    
    return JsonResponse({
        'users': [
            {
                'id': u.id,
                'username': u.username,
                'full_name': u.get_full_name() or u.username,
                'email': u.email or '',
            }
            for u in users
        ]
    })


@login_required
def add_signing_admin(request):
    """新增簽章管理員 API - 僅 superuser"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '沒有權限'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    from django.contrib.auth.models import User
    
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': '請指定使用者'}, status=400)
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': '找不到該使用者'}, status=404)
    
    # 檢查是否已經是簽章管理員
    if SigningAdmin.objects.filter(user=user).exists():
        return JsonResponse({'success': False, 'error': '該使用者已經是簽章管理員'}, status=400)
    
    # 建立簽章管理員
    admin = SigningAdmin.objects.create(
        user=user,
        is_active=True,
        created_by=request.user
    )
    
    return JsonResponse({
        'success': True,
        'message': f'已將 {user.get_full_name() or user.username} 新增為簽章管理員',
        'admin': {
            'id': admin.id,
            'user_id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email or '',
            'is_active': admin.is_active,
            'created_at': admin.created_at.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
def remove_signing_admin(request, pk):
    """移除簽章管理員 API - 僅 superuser"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '沒有權限'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    admin = get_object_or_404(SigningAdmin, pk=pk)
    user_name = admin.user.get_full_name() or admin.user.username
    admin.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'已移除 {user_name} 的簽章管理員權限',
    })


@login_required
def toggle_signing_admin(request, pk):
    """切換簽章管理員啟用狀態 API - 僅 superuser"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': '沒有權限'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': '無效的請求方法'}, status=405)
    
    admin = get_object_or_404(SigningAdmin, pk=pk)
    admin.is_active = not admin.is_active
    admin.save(update_fields=['is_active'])
    
    status_text = '啟用' if admin.is_active else '停用'
    user_name = admin.user.get_full_name() or admin.user.username
    
    return JsonResponse({
        'success': True,
        'message': f'已{status_text} {user_name} 的簽章管理員權限',
        'is_active': admin.is_active,
    })
