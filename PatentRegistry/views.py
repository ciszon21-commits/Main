from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count
from datetime import datetime

from .models import PatentApplication, PatentRebuttal, GrantedPatent, PatentAnnuity
from .forms import PatentApplicationForm, PatentRebuttalForm, GrantedPatentForm, PatentAnnuityForm


# ============================================================
# 公開頁面 - 已取得專利分年度瀏覽
# ============================================================

class PublicPatentListView(ListView):
    """公開首頁 - 分年度瀏覽已取得專利"""
    model = GrantedPatent
    template_name = 'patent_registry/public_patent_list.html'
    context_object_name = 'patents'
    
    def get_queryset(self):
        queryset = GrantedPatent.objects.select_related('application').order_by('-start_date')
        year = self.request.GET.get('year')
        if year:
            try:
                queryset = queryset.filter(start_date__year=int(year))
            except ValueError:
                pass
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 取得所有年度選項
        years = GrantedPatent.objects.dates('start_date', 'year', order='DESC')
        context['years'] = [d.year for d in years]
        context['selected_year'] = self.request.GET.get('year', '')
        context['total_count'] = GrantedPatent.objects.count()
        return context


# ============================================================
# 專利申請管理
# ============================================================

class ApplicationListView(LoginRequiredMixin, ListView):
    """專利申請列表"""
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
        return context


class ApplicationCreateView(LoginRequiredMixin, CreateView):
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


class ApplicationDetailView(LoginRequiredMixin, DetailView):
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


class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
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


class ApplicationDeleteView(LoginRequiredMixin, DeleteView):
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

class RebuttalCreateView(LoginRequiredMixin, CreateView):
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


class RebuttalDeleteView(LoginRequiredMixin, DeleteView):
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

class GrantApplicationView(LoginRequiredMixin, CreateView):
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


class RejectApplicationView(LoginRequiredMixin, View):
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

class GrantedPatentDetailView(LoginRequiredMixin, DetailView):
    """已取得專利詳情"""
    model = GrantedPatent
    template_name = 'patent_registry/granted_detail.html'
    context_object_name = 'patent'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['annuities'] = self.object.annuities.all()
        context['annuity_form'] = PatentAnnuityForm(initial={'year': datetime.now().year})
        return context


class GrantedPatentUpdateView(LoginRequiredMixin, UpdateView):
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

class AnnuityListView(LoginRequiredMixin, ListView):
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


class AnnuityCreateView(LoginRequiredMixin, CreateView):
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


class AnnuityDeleteView(LoginRequiredMixin, DeleteView):
    """刪除年費核銷記錄"""
    model = PatentAnnuity
    template_name = 'patent_registry/annuity_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('patent_registry:granted_detail', kwargs={'pk': self.object.granted_patent.pk})
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '年費核銷記錄已刪除！')
        return super().delete(request, *args, **kwargs)
