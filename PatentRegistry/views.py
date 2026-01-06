from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.exceptions import PermissionDenied
from datetime import datetime

from .models import PatentApplication, PatentRebuttal, GrantedPatent, PatentAnnuity, PatentAdmin, is_patent_admin
from .forms import PatentApplicationForm, PatentRebuttalForm, GrantedPatentForm, PatentAnnuityForm


class PatentAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to require patent admin or superuser permission.
    """
    def test_func(self):
        return is_patent_admin(self.request.user)
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, '您沒有專利管理權限。')
            return redirect('patent_registry:public_list')
        return super().handle_no_permission()


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to require superuser permission.
    """
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, '此操作需要超級使用者權限。')
            return redirect('patent_registry:public_list')
        return super().handle_no_permission()




# ============================================================
# 公開頁面 - 已取得專利分年度瀏覽
# ============================================================

class PublicPatentListView(ListView):
    """公開首頁 - 分年度瀏覽已取得專利"""
    model = GrantedPatent
    template_name = 'patent_registry/public_patent_list.html'
    context_object_name = 'patents'
    
    def get_queryset(self):
        # 若為專利管理員則顯示所有資料，否則只顯示公開資料
        user = self.request.user
        if user.is_authenticated and is_patent_admin(user):
            queryset = GrantedPatent.objects.select_related('application').order_by('-start_date')
        else:
            queryset = GrantedPatent.objects.select_related('application').filter(
                application__is_public=True
            ).order_by('-start_date')
        
        year = self.request.GET.get('year')
        if year:
            try:
                queryset = queryset.filter(start_date__year=int(year))
            except ValueError:
                pass
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_admin = user.is_authenticated and is_patent_admin(user)
        context['is_patent_admin'] = is_admin
        
        # 取得所有年度選項 (based on visibility)
        if is_admin:
            years = GrantedPatent.objects.dates('start_date', 'year', order='DESC')
            context['total_count'] = GrantedPatent.objects.count()
        else:
            years = GrantedPatent.objects.filter(application__is_public=True).dates('start_date', 'year', order='DESC')
            context['total_count'] = GrantedPatent.objects.filter(application__is_public=True).count()
        
        context['years'] = [d.year for d in years]
        context['selected_year'] = self.request.GET.get('year', '')
        return context


# ============================================================
# 專利申請管理
# ============================================================

class ApplicationListView(PatentAdminRequiredMixin, ListView):
    """專利申請列表 - 僅專利管理員可見"""
    model = PatentApplication
    template_name = 'patent_registry/application_list.html'
    context_object_name = 'applications'
    
    def get_queryset(self):
        queryset = PatentApplication.objects.prefetch_related('rebuttals').order_by('-created_at')
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = PatentApplication.STATUS_CHOICES
        context['selected_status'] = self.request.GET.get('status', '')
        context['pending_count'] = PatentApplication.objects.filter(status='PENDING').count()
        context['approved_count'] = PatentApplication.objects.filter(status='APPROVED').count()
        context['rejected_count'] = PatentApplication.objects.filter(status='REJECTED').count()
        context['is_patent_admin'] = True  # Must be admin to see this view
        return context


class ApplicationCreateView(PatentAdminRequiredMixin, CreateView):
    """新增專利申請"""
    model = PatentApplication
    form_class = PatentApplicationForm
    template_name = 'patent_registry/application_form.html'
    success_url = reverse_lazy('patent_registry:application_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '專利申請已成功建立！')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '新增專利申請'
        context['submit_text'] = '建立申請'
        return context


class ApplicationDetailView(PatentAdminRequiredMixin, DetailView):
    """專利申請詳情"""
    model = PatentApplication
    template_name = 'patent_registry/application_detail.html'
    context_object_name = 'application'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rebuttals'] = self.object.rebuttals.all()
        context['rebuttal_form'] = PatentRebuttalForm()
        context['grant_form'] = GrantedPatentForm()
        # Check if granted patent exists
        try:
            context['granted_patent'] = self.object.granted_patent
        except GrantedPatent.DoesNotExist:
            context['granted_patent'] = None
        return context


class ApplicationUpdateView(PatentAdminRequiredMixin, UpdateView):
    """編輯專利申請"""
    model = PatentApplication
    form_class = PatentApplicationForm
    template_name = 'patent_registry/application_form.html'
    
    def get_success_url(self):
        return reverse('patent_registry:application_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, '專利申請已更新！')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '編輯專利申請'
        context['submit_text'] = '儲存變更'
        return context


class ApplicationDeleteView(PatentAdminRequiredMixin, DeleteView):
    """刪除專利申請"""
    model = PatentApplication
    template_name = 'patent_registry/application_confirm_delete.html'
    success_url = reverse_lazy('patent_registry:application_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '專利申請已刪除！')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 答辯管理
# ============================================================

class RebuttalCreateView(PatentAdminRequiredMixin, CreateView):
    """新增答辯記錄"""
    model = PatentRebuttal
    form_class = PatentRebuttalForm
    template_name = 'patent_registry/rebuttal_form.html'
    
    def get_application(self):
        return get_object_or_404(PatentApplication, pk=self.kwargs['app_id'])
    
    def form_valid(self, form):
        application = self.get_application()
        form.instance.application = application
        messages.success(self.request, '答辯記錄已新增！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('patent_registry:application_detail', kwargs={'pk': self.kwargs['app_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.get_application()
        return context


class RebuttalDeleteView(PatentAdminRequiredMixin, DeleteView):
    """刪除答辯記錄"""
    model = PatentRebuttal
    template_name = 'patent_registry/rebuttal_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('patent_registry:application_detail', kwargs={'pk': self.object.application.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '答辯記錄已刪除！')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 審核結果管理
# ============================================================

class GrantApplicationView(PatentAdminRequiredMixin, CreateView):
    """將申請設定為通過並填寫專利資訊"""
    model = GrantedPatent
    form_class = GrantedPatentForm
    template_name = 'patent_registry/grant_form.html'
    
    def get_application(self):
        return get_object_or_404(PatentApplication, pk=self.kwargs['pk'])
    
    def form_valid(self, form):
        application = self.get_application()
        form.instance.application = application
        # 更新申請狀態為通過
        application.status = 'APPROVED'
        application.save()
        messages.success(self.request, '專利申請已核准，專利資訊已建立！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('patent_registry:application_detail', kwargs={'pk': self.kwargs['pk']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.get_application()
        return context


class RejectApplicationView(PatentAdminRequiredMixin, View):
    """將申請設定為不通過"""
    def post(self, request, pk):
        application = get_object_or_404(PatentApplication, pk=pk)
        application.status = 'REJECTED'
        application.save()
        messages.warning(request, '專利申請已設定為不通過')
        return redirect('patent_registry:application_detail', pk=pk)


# ============================================================
# 已取得專利管理
# ============================================================

class GrantedPatentDetailView(PatentAdminRequiredMixin, DetailView):
    """已取得專利詳情"""
    model = GrantedPatent
    template_name = 'patent_registry/granted_detail.html'
    context_object_name = 'patent'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['annuities'] = self.object.annuities.all()
        context['annuity_form'] = PatentAnnuityForm(initial={'year': datetime.now().year})
        return context


class GrantedPatentUpdateView(PatentAdminRequiredMixin, UpdateView):
    """更新已取得專利資訊"""
    model = GrantedPatent
    form_class = GrantedPatentForm
    template_name = 'patent_registry/grant_form.html'
    
    def get_success_url(self):
        return reverse('patent_registry:granted_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, '專利資訊已更新！')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['application'] = self.object.application
        context['is_edit'] = True
        return context


# ============================================================
# 年費核銷管理
# ============================================================

class AnnuityListView(PatentAdminRequiredMixin, ListView):
    """專利年費核銷管理列表"""
    model = GrantedPatent
    template_name = 'patent_registry/annuity_list.html'
    context_object_name = 'patents'
    
    def get_queryset(self):
        return GrantedPatent.objects.prefetch_related('annuities').order_by('-start_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = datetime.now().year
        return context


class AnnuityCreateView(PatentAdminRequiredMixin, CreateView):
    """新增年費核銷記錄"""
    model = PatentAnnuity
    form_class = PatentAnnuityForm
    template_name = 'patent_registry/annuity_form.html'
    
    def get_granted_patent(self):
        return get_object_or_404(GrantedPatent, pk=self.kwargs['patent_id'])
    
    def form_valid(self, form):
        patent = self.get_granted_patent()
        form.instance.granted_patent = patent
        form.instance.created_by = self.request.user
        messages.success(self.request, '年費核銷記錄已新增！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('patent_registry:granted_detail', kwargs={'pk': self.kwargs['patent_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['patent'] = self.get_granted_patent()
        return context


class AnnuityDeleteView(PatentAdminRequiredMixin, DeleteView):
    """刪除年費核銷記錄"""
    model = PatentAnnuity
    template_name = 'patent_registry/annuity_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('patent_registry:granted_detail', kwargs={'pk': self.object.granted_patent.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '年費核銷記錄已刪除！')
        return super().delete(request, *args, **kwargs)


# ============================================================
# 專利管理員設定 (僅超級使用者)
# ============================================================

class PatentAdminListView(SuperuserRequiredMixin, ListView):
    """專利管理員列表"""
    model = PatentAdmin
    template_name = 'patent_registry/admin_settings.html'
    context_object_name = 'admins'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '專利管理員設定'
        return context


class PatentAdminCreateView(SuperuserRequiredMixin, View):
    """新增專利管理員"""
    def post(self, request):
        user_id = request.POST.get('user_id')
        if not user_id:
            messages.error(request, '請選擇使用者')
            return redirect('patent_registry:admin_settings')
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            messages.error(request, '找不到該使用者')
            return redirect('patent_registry:admin_settings')
        
        # Check if already admin
        if PatentAdmin.objects.filter(user=user).exists():
            messages.warning(request, f'{user.username} 已是專利管理員')
            return redirect('patent_registry:admin_settings')
        
        PatentAdmin.objects.create(
            user=user,
            created_by=request.user
        )
        messages.success(request, f'已將 {user.username} 設為專利管理員')
        return redirect('patent_registry:admin_settings')


class PatentAdminDeleteView(SuperuserRequiredMixin, View):
    """移除專利管理員"""
    def post(self, request, pk):
        admin = get_object_or_404(PatentAdmin, pk=pk)
        username = admin.user.username
        admin.delete()
        messages.success(request, f'已移除 {username} 的專利管理員權限')
        return redirect('patent_registry:admin_settings')


def user_search_api(request):
    """AJAX 搜尋使用者 API"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'error': '權限不足'}, status=403)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'users': []})
    
    # 搜尋使用者，排除已是管理員的使用者
    existing_admin_user_ids = PatentAdmin.objects.values_list('user_id', flat=True)
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id__in=existing_admin_user_ids)[:10]
    
    result = [{
        'id': u.id,
        'username': u.username,
        'display_name': u.get_full_name() or u.username,
        'email': u.email
    } for u in users]
    
    return JsonResponse({'users': result})
