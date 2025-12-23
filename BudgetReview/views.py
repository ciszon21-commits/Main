from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Project, Discipline, QuantityFile, PriceInquiryFile, BudgetFile, FinalBudgetFile, PriceAdjustment, AuditLog
from .forms import ProjectForm, DisciplineForm, FileUploadForm, PriceAdjustmentForm
from .validators import validate_file_extension
import os

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Admin').exists()

# Project Views
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'budget_review/project_list.html'
    context_object_name = 'projects'
    ordering = ['-created_at']
    
    def get_queryset(self):
        """僅顯示未刪除的標案"""
        return Project.objects.filter(deleted_at__isnull=True).order_by('-created_at')

class ProjectCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'budget_review/project_form.html'
    success_url = reverse_lazy('budget_review:project_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # admins 是 ManyToMany，會在 form.save() 後自動處理
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            model_name='Project',
            object_id=self.object.id,
            detail={'name': self.object.name, 'code': self.object.code}
        )
        messages.success(self.request, f"標案 「{self.object.name}」 已建立成功。")
        return response

class ProjectCreateAjaxView(LoginRequiredMixin, AdminRequiredMixin, View):
    """AJAX 版本的建立 view，用於 Modal"""
    def get(self, request):
        form = ProjectForm()
        
        # 渲染表單 HTML
        html = render(request, 'budget_review/project_form_ajax.html', {
            'form': form,
            'project': None  # 建立模式，沒有現有 project
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request):
        form = ProjectForm(request.POST)
        
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m()  # 儲存 ManyToMany 關係 (admins)
            
            AuditLog.objects.create(
                user=request.user,
                action='CREATE',
                model_name='Project',
                object_id=project.id,
                detail={'name': project.name, 'code': project.code}
            )
            return JsonResponse({
                'success': True,
                'message': f'標案 「{project.name}」 已建立成功。'
            })
        else:
            # 返回帶有錯誤的表單 HTML
            html = render(request, 'budget_review/project_form_ajax.html', {
                'form': form,
                'project': None
            }).content.decode('utf-8')
            
            return JsonResponse({
                'success': False,
                'html': html
            })

class ProjectUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'budget_review/project_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            model_name='Project',
            object_id=self.object.id,
            detail={'name': self.object.name, 'code': self.object.code}
        )
        messages.success(self.request, f"標案 「{self.object.name}」 已更新。")
        return response

    def get_success_url(self):
        return reverse('budget_review:project_detail', kwargs={'pk': self.object.id})

class ProjectUpdateAjaxView(LoginRequiredMixin, AdminRequiredMixin, View):
    """AJAX 版本的編輯 view，用於 Modal"""
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectForm(instance=project)
        
        # 渲染表單 HTML
        html = render(request, 'budget_review/project_form_ajax.html', {
            'form': form,
            'project': project
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectForm(request.POST, instance=project)
        
        if form.is_valid():
            form.save()
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='Project',
                object_id=project.id,
                detail={'name': project.name, 'code': project.code}
            )
            return JsonResponse({
                'success': True,
                'message': f'標案 「{project.name}」 已更新。'
            })
        else:
            # 返回帶有錯誤的表單 HTML
            html = render(request, 'budget_review/project_form_ajax.html', {
                'form': form,
                'project': project
            }).content.decode('utf-8')
            
            return JsonResponse({
                'success': False,
                'html': html
            })

class ProjectDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        from django.utils import timezone
        from .permissions import can_delete_project
        
        project = get_object_or_404(Project, pk=pk)
        
        # 使用 permissions.py 檢查權限
        if not can_delete_project(request.user, project):
            messages.error(request, "您沒有權限刪除此標案。")
            return redirect('budget_review:project_detail', pk=pk)
        
        name = project.name
        # 軟刪除：設定刪除時間與刪除者
        project.deleted_at = timezone.now()
        project.deleted_by = request.user
        project.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Project',
            object_id=pk,
            detail={'name': name, 'deleted_at': project.deleted_at.isoformat()}
        )
        messages.success(request, f"標案 「{name}」 已移至隱藏標案。")
        return redirect('budget_review:project_list')

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'budget_review/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        from .models import Stage
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # 取得專業分組
        context['disciplines'] = project.disciplines.all()
        
        # 取得階段（按順序排序）
        context['stages'] = project.stages.all().order_by('order')
        
        # 檢查使用者權限
        from .permissions import has_project_admin_permission
        context['can_manage_project'] = has_project_admin_permission(self.request.user, project)
        
        return context

# Discipline Views
class DisciplineCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Discipline
    form_class = DisciplineForm
    template_name = 'budget_review/discipline_form.html'

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs.get('project_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.get_project()
        return context

    def form_valid(self, form):
        project = self.get_project()
        form.instance.project = project
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            model_name='Discipline',
            object_id=self.object.id,
            detail={'name': self.object.name, 'project_id': project.id}
        )
        messages.success(self.request, f"專業分組 「{self.object.name}」 已新增至標案 「{project.name}」。")
        return response

    def get_success_url(self):
        return reverse('budget_review:project_detail', kwargs={'pk': self.kwargs.get('project_id')})

class DisciplineCreateAjaxView(LoginRequiredMixin, AdminRequiredMixin, View):
    """AJAX 版本的專業分組建立 view，用於 Modal"""
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        form = DisciplineForm()
        
        # 渲染表單 HTML
        html = render(request, 'budget_review/discipline_form_ajax.html', {
            'form': form,
            'project': project,
            'discipline': None
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        form = DisciplineForm(request.POST)
        
        if form.is_valid():
            discipline = form.save(commit=False)
            discipline.project = project
            discipline.save()
            form.save_m2m()  # 儲存 ManyToMany 關係
            
            AuditLog.objects.create(
                user=request.user,
                action='CREATE',
                model_name='Discipline',
                object_id=discipline.id,
                detail={'name': discipline.name, 'project_id': project.id}
            )
            return JsonResponse({
                'success': True,
                'message': f'專業分組 「{discipline.name}」 已新增成功。'
            })
        else:
            # 返回帶有錯誤的表單 HTML
            html = render(request, 'budget_review/discipline_form_ajax.html', {
                'form': form,
                'project': project,
                'discipline': None
            }).content.decode('utf-8')
            
            return JsonResponse({
                'success': False,
                'html': html
            })

class DisciplineUpdateAjaxView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request, project_id, pk):
        project = get_object_or_404(Project, pk=project_id)
        discipline = get_object_or_404(Discipline, pk=pk, project=project)
        
        # 根據是否為整合專業選擇不同表單
        if discipline.is_overall:
            from .forms import OverallDisciplineForm
            form = OverallDisciplineForm(instance=discipline)
        else:
            form = DisciplineForm(instance=discipline)
        
        html = render(request, 'budget_review/discipline_form_ajax.html', {
            'form': form,
            'project': project,
            'discipline': discipline,
            'is_update': True,
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id, pk):
        project = get_object_or_404(Project, pk=project_id)
        discipline = get_object_or_404(Discipline, pk=pk, project=project)
        
        # 根據是否為整合專業選擇不同表單
        if discipline.is_overall:
            from .forms import OverallDisciplineForm
            form = OverallDisciplineForm(request.POST, instance=discipline)
        else:
            form = DisciplineForm(request.POST, instance=discipline)
        
        if form.is_valid():
            discipline = form.save()
            # 只有非整合專業需要儲存 ManyToMany 關係
            # OverallDisciplineForm 會自動處理 budget_members
            
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='Discipline',
                object_id=discipline.id,
                detail={'name': discipline.name, 'project_id': project.id}
            )
            return JsonResponse({
                'success': True,
                'message': f'專業分組 「{discipline.name}」 已更新成功。'
            })
        else:
            # 返回帶有錯誤的表單 HTML
            html = render(request, 'budget_review/discipline_form_ajax.html', {
                'form': form,
                'project': project,
                'discipline': discipline,
                'is_update': True,
            }).content.decode('utf-8')
            return JsonResponse({
                'success': False,
                'html': html
            })

class DisciplineUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Discipline
    template_name = 'budget_review/discipline_form.html'
    
    def get_form_class(self):
        # 整合專業使用特殊表單（只能編輯預算管理員和預算成員）
        if self.object.is_overall:
            from .forms import OverallDisciplineForm
            return OverallDisciplineForm
        else:
            from .forms import DisciplineForm
            return DisciplineForm
    
    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['project_id'])
    
    def get_queryset(self):
        return Discipline.objects.filter(project=self.get_project())
    
    def form_valid(self, form):
        messages.success(self.request, f"專業分組 「{form.instance.name}」 更新成功。")
        return super().form_valid(form)
    
    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy('budget_review:project_detail', kwargs={'pk': self.get_project().id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.get_project()
        return context

class DisciplineDeleteView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, project_id, pk):
        project = get_object_or_404(Project, pk=project_id)
        discipline = get_object_or_404(Discipline, pk=pk, project=project)
        
        # 禁止刪除整合專業
        if discipline.is_overall:
            return JsonResponse({
                'success': False,
                'message': '整合專業不可被刪除。'
            })
        
        name = discipline.name
        discipline.delete()
        
        AuditLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Discipline',
            object_id=pk,
            detail={'name': name, 'project_id': project_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'專業分組 「{name}」 已被刪除。'
        })

# File Upload Views
class FileUploadViewBase(LoginRequiredMixin, FormView):
    form_class = FileUploadForm
    template_name = 'budget_review/file_upload.html'
    model_class = None  # To be set in subclasses

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs['project_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_project()
        
        # 獲取整合預算書（最新版本）
        overall_budget = project.budget_files.filter(budget_type='OVERALL', is_latest=True).first()
        context['overall_budget'] = overall_budget
        
        # 簡單權限檢查（可改為更複雜的邏輯）
        user = self.request.user
        context['can_edit'] = user.is_superuser or user.groups.filter(name='Admin').exists()
        
        context['project'] = project
        context['upload_type'] = self.kwargs.get('upload_type', '')
        return context

    def form_valid(self, form):
        project = self.get_project()
        uploaded_file = self.request.FILES['file']
        description = form.cleaned_data.get('description', '')
        discipline_id = self.request.POST.get('discipline')
        
        # 嚴格驗證檔案格式
        upload_type = self.kwargs.get('upload_type', '')
        if not upload_type:
            # Try to infer from model_class
            model_map = {QuantityFile: 'quantity', PriceInquiryFile: 'price_inquiry', BudgetFile: 'budget', FinalBudgetFile: 'integrated_budget'}
            upload_type = model_map.get(self.model_class, '')
            
        is_valid, error_msg = validate_file_extension(uploaded_file, upload_type)
        if not is_valid:
            messages.error(self.request, error_msg)
            return self.form_invalid(form)

        # Handle versioning

        if discipline_id:
            discipline = get_object_or_404(Discipline, pk=discipline_id, project=project)
            # Mark previous files as not latest
            self.model_class.objects.filter(project=project, discipline=discipline, is_latest=True).update(is_latest=False)
            # Get the latest version number
            latest = self.model_class.objects.filter(project=project, discipline=discipline).order_by('-version').first()
            version = (latest.version + 1) if latest else 1
            
            file_obj = self.model_class.objects.create(
                project=project,
                discipline=discipline,
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=self.request.user,
                description=description,
                is_latest=True
            )
        else:
            # For files without discipline (e.g., final budget)
            self.model_class.objects.filter(project=project, discipline__isnull=True, is_latest=True).update(is_latest=False)
            latest = self.model_class.objects.filter(project=project, discipline__isnull=True).order_by('-version').first()
            version = (latest.version + 1) if latest else 1
            
            file_obj = self.model_class.objects.create(
                project=project,
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=self.request.user,
                description=description,
                is_latest=True
            )

        AuditLog.objects.create(
            user=self.request.user,
            action='UPLOAD',
            model_name=self.model_class.__name__,
            object_id=file_obj.id,
            detail={'file_name': uploaded_file.name, 'version': version}
        )
        messages.success(self.request, f"檔案 「{uploaded_file.name}」 (版本 {version}) 上傳成功。")
        return redirect('budget_review:project_detail', pk=project.id)

class QuantityFileUploadView(FileUploadViewBase):
    model_class = QuantityFile

class QuantityFileUploadAjaxView(LoginRequiredMixin, View):
    """AJAX 版本的數量文件上傳 view，用於 Modal"""
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        discipline_id = request.GET.get('discipline', '')
        
        # 渲染表單 HTML
        html = render(request, 'budget_review/file_upload_ajax.html', {
            'project': project,
            'discipline_id': discipline_id,
            'upload_type': 'quantity'
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '請選擇要上傳的檔案'
            })
        
        uploaded_file = request.FILES['file']
        
        # 嚴格驗證檔案格式
        is_valid, error_msg = validate_file_extension(uploaded_file, 'quantity')
        if not is_valid:
            return JsonResponse({'success': False, 'message': error_msg})
            
        description = request.POST.get('description', '')
        discipline_id = request.POST.get('discipline')
        
        if not discipline_id:
            return JsonResponse({
                'success': False,
                'message': '請選擇專業分組'
            })
        
        discipline = get_object_or_404(Discipline, pk=discipline_id, project=project)
        
        # Mark previous files as not latest
        QuantityFile.objects.filter(project=project, discipline=discipline, is_latest=True).update(is_latest=False)
        
        # Get the latest version number
        latest = QuantityFile.objects.filter(project=project, discipline=discipline).order_by('-version').first()
        version = (latest.version + 1) if latest else 1
        
        # Create new file record
        file_obj = QuantityFile.objects.create(
            project=project,
            discipline=discipline,
            file=uploaded_file,
            file_name=uploaded_file.name,
            version=version,
            uploaded_by=request.user,
            description=description,
            is_latest=True
        )
        
        AuditLog.objects.create(
            user=request.user,
            action='UPLOAD',
            model_name='QuantityFile',
            object_id=file_obj.id,
            detail={'file_name': uploaded_file.name, 'version': version, 'discipline': discipline.name}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'數量檔案 「{uploaded_file.name}」 (版本 {version}) 上傳成功。'
        })

class PriceInquiryFileUploadView(FileUploadViewBase):
    model_class = PriceInquiryFile

class PriceInquiryFileUploadAjaxView(LoginRequiredMixin, View):
    """AJAX 版本的訪價文件上傳 view，用於 Modal，支援多檔案上傳"""
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        discipline_id = request.GET.get('discipline', '')
        
        # 渲染表單 HTML
        html = render(request, 'budget_review/file_upload_ajax.html', {
            'project': project,
            'discipline_id': discipline_id,
            'upload_type': 'price_inquiry',
            'multiple_files': True,  # 訪價支援多檔案
            'accept_formats': '.pdf,.jpg,.jpeg,.png,.xlsx,.xls'
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        
        # 支援多檔案上傳
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '請選擇要上傳的檔案'
            })
        
        files = request.FILES.getlist('file')  # 獲取多個檔案
        
        # 嚴格驗證檔案格式
        for uploaded_file in files:
            is_valid, error_msg = validate_file_extension(uploaded_file, 'price_inquiry')
            if not is_valid:
                return JsonResponse({'success': False, 'message': error_msg})
                
        description = request.POST.get('description', '')
        discipline_id = request.POST.get('discipline')
        
        if not discipline_id:
            return JsonResponse({
                'success': False,
                'message': '請選擇專業分組'
            })
        
        discipline = get_object_or_404(Discipline, pk=discipline_id, project=project)
        
        # 處理多個檔案
        uploaded_files = []
        for uploaded_file in files:
            # Mark previous files as not latest
            PriceInquiryFile.objects.filter(project=project, discipline=discipline, is_latest=True).update(is_latest=False)
            
            # Get the latest version number
            latest = PriceInquiryFile.objects.filter(project=project, discipline=discipline).order_by('-version').first()
            version = (latest.version + 1) if latest else 1
            
            # Create new file record
            file_obj = PriceInquiryFile.objects.create(
                project=project,
                discipline=discipline,
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=request.user,
                description=description,
                is_latest=True
            )
            
            uploaded_files.append(uploaded_file.name)
            
            AuditLog.objects.create(
                user=request.user,
                action='UPLOAD',
                model_name='PriceInquiryFile',
                object_id=file_obj.id,
                detail={'file_name': uploaded_file.name, 'version': version, 'discipline': discipline.name}
            )
        
        file_count = len(uploaded_files)
        file_list = '、'.join(uploaded_files[:3])  # 顯示前3個檔案名稱
        if file_count > 3:
            file_list += f' 等 {file_count} 個檔案'
        
        return JsonResponse({
            'success': True,
            'message': f'訪價檔案 {file_list} 上傳成功。'
        })

class BudgetFileUploadView(FileUploadViewBase):
    model_class = BudgetFile

    def form_valid(self, form):
        project = self.get_project()
        uploaded_file = self.request.FILES['file']
        description = form.cleaned_data.get('description', '')
        discipline_id = self.request.POST.get('discipline')
        budget_type = self.request.POST.get('budget_type', 'GROUP')

        # Handle versioning
        if budget_type == 'GROUP' and discipline_id:
            discipline = get_object_or_404(Discipline, pk=discipline_id, project=project)
            BudgetFile.objects.filter(project=project, discipline=discipline, budget_type='GROUP', is_latest=True).update(is_latest=False)
            latest = BudgetFile.objects.filter(project=project, discipline=discipline, budget_type='GROUP').order_by('-version').first()
            version = (latest.version + 1) if latest else 1

            file_obj = BudgetFile.objects.create(
                project=project,
                discipline=discipline,
                budget_type='GROUP',
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=self.request.user,
                description=description,
                is_latest=True
            )
        else:
            # OVERALL budget
            BudgetFile.objects.filter(project=project, budget_type='OVERALL', is_latest=True).update(is_latest=False)
            latest = BudgetFile.objects.filter(project=project, budget_type='OVERALL').order_by('-version').first()
            version = (latest.version + 1) if latest else 1

            file_obj = BudgetFile.objects.create(
                project=project,
                budget_type='OVERALL',
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=self.request.user,
                description=description,
                is_latest=True
            )

        AuditLog.objects.create(
            user=self.request.user,
            action='UPLOAD',
            model_name='BudgetFile',
            object_id=file_obj.id,
            detail={'file_name': uploaded_file.name, 'version': version, 'budget_type': budget_type}
        )
        messages.success(self.request, f"預算書 「{uploaded_file.name}」 (版本 {version}) 上傳成功。")
        return redirect('budget_review:project_detail', pk=project.id)

class BudgetFileUploadAjaxView(LoginRequiredMixin, View):
    """AJAX 版本的預算書上傳 view，用於 Modal"""
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        discipline_id = request.GET.get('discipline', '')
        budget_type = request.GET.get('budget_type', 'GROUP')
        
        # 渲染表單 HTML
        html = render(request, 'budget_review/file_upload_ajax.html', {
            'project': project,
            'discipline_id': discipline_id,
            'budget_type': budget_type,
            'upload_type': 'budget'
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': '請選擇要上傳的檔案'
            })
        
        uploaded_file = request.FILES['file']
        
        # 嚴格驗證檔案格式
        is_valid, error_msg = validate_file_extension(uploaded_file, 'budget')
        if not is_valid:
            return JsonResponse({'success': False, 'message': error_msg})
            
        description = request.POST.get('description', '')
        discipline_id = request.POST.get('discipline')
        budget_type = request.POST.get('budget_type', 'GROUP')
        
        # Handle versioning based on budget type
        if budget_type == 'GROUP':
            if not discipline_id:
                return JsonResponse({
                    'success': False,
                    'message': '請選擇專業分組'
                })
            
            discipline = get_object_or_404(Discipline, pk=discipline_id, project=project)
            BudgetFile.objects.filter(project=project, discipline=discipline, budget_type='GROUP', is_latest=True).update(is_latest=False)
            latest = BudgetFile.objects.filter(project=project, discipline=discipline, budget_type='GROUP').order_by('-version').first()
            version = (latest.version + 1) if latest else 1
            
            file_obj = BudgetFile.objects.create(
                project=project,
                discipline=discipline,
                budget_type='GROUP',
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=request.user,
                description=description,
                is_latest=True
            )
            
            type_label = f'{discipline.name} 專業分組預算書'
        else:
            # OVERALL budget
            BudgetFile.objects.filter(project=project, budget_type='OVERALL', is_latest=True).update(is_latest=False)
            latest = BudgetFile.objects.filter(project=project, budget_type='OVERALL').order_by('-version').first()
            version = (latest.version + 1) if latest else 1
            
            file_obj = BudgetFile.objects.create(
                project=project,
                budget_type='OVERALL',
                file=uploaded_file,
                file_name=uploaded_file.name,
                version=version,
                uploaded_by=request.user,
                description=description,
                is_latest=True
            )
            
            type_label = '整合預算書'
        
        AuditLog.objects.create(
            user=request.user,
            action='UPLOAD',
            model_name='BudgetFile',
            object_id=file_obj.id,
            detail={'file_name': uploaded_file.name, 'version': version, 'budget_type': budget_type}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{type_label} 「{uploaded_file.name}」 (版本 {version}) 上傳成功。'
        })

class FinalBudgetFileUploadView(FileUploadViewBase):
    model_class = FinalBudgetFile

class BlankTenderFileUploadAjaxView(LoginRequiredMixin, View):
    """AJAX upload view for blank tender forms"""
    def get(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        discipline_id = request.GET.get('discipline', '')
        
        # Render form HTML
        html = render(request, 'budget_review/file_upload_ajax.html', {
            'project': project,
            'discipline_id': discipline_id,
            'upload_type': 'blank-tender',
            'file_label': '空白標單'
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        uploaded_file = request.FILES.get('file')
        
        # 嚴格驗證檔案格式
        if uploaded_file:
            is_valid, error_msg = validate_file_extension(uploaded_file, 'blank_tender')
            if not is_valid:
                return JsonResponse({'success': False, 'message': error_msg})
                
        discipline_id = request.POST.get('discipline')  # Changed from 'discipline_id' to 'discipline'
        
        if not uploaded_file:
            return JsonResponse({'success': False, 'message': '請選擇檔案。'})
        
        try:
            discipline = Discipline.objects.get(pk=discipline_id, project=project)
        except Discipline.DoesNotExist:
            return JsonResponse({'success': False, 'message': '找不到專業分組。'})
        
        # Determine version
        latest_file = FinalBudgetFile.objects.filter(
            project=project,
            discipline=discipline,
            file_type='BLANK_TENDER'
        ).order_by('-version').first()
        
        version = (latest_file.version + 1) if latest_file else 1
        
        # Mark previous versions as not latest
        FinalBudgetFile.objects.filter(
            project=project,
            discipline=discipline,
            file_type='BLANK_TENDER',
            is_latest=True
        ).update(is_latest=False)
        
        # Create new file entry
        file_obj = FinalBudgetFile(
            project=project,
            discipline=discipline,
            file=uploaded_file,
            file_name=uploaded_file.name,
            version=version,
            uploaded_by=request.user,
            file_type='BLANK_TENDER',
            is_latest=True
        )
        file_obj.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='UPLOAD',
            model_name='FinalBudgetFile',
            object_id=file_obj.id,
            detail={'file_name': uploaded_file.name, 'version': version, 'file_type': 'BLANK_TENDER'}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'空白標單 「{uploaded_file.name}」 (版本 {version}) 上傳成功。'
        })


class FileDownloadView(LoginRequiredMixin, View):
    def get(self, request, file_model, file_id):
        models_map = {
            'quantity': QuantityFile,
            'price_inquiry': PriceInquiryFile,
            'budget': BudgetFile,
            'final_budget': FinalBudgetFile,
            'blank_tender': FinalBudgetFile,
        }
        model_class = models_map.get(file_model)
        if not model_class:
            messages.error(request, "無效的檔案類型。")
            return redirect('budget_review:project_list')
        
        file_obj = get_object_or_404(model_class, pk=file_id)
        
        # Permission check can be added here
        
        # Get file path and check if it exists
        file_path = file_obj.file.path
        if not os.path.exists(file_path):
            messages.error(request, "找不到檔案。")
            return redirect('budget_review:project_list')
        
        # Determine MIME type based on file extension
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # Use FileResponse to handle download properly
        from django.http import FileResponse
        from urllib.parse import quote
        
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        encoded_filename = quote(file_obj.file_name)
        response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        return response

# Price Adjustment
class PriceAdjustmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = PriceAdjustment
    form_class = PriceAdjustmentForm
    template_name = 'budget_review/price_adjustment_form.html'

    def get_project(self):
        return get_object_or_404(Project, pk=self.kwargs.get('project_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.get_project()
        return context

    def form_valid(self, form):
        project = self.get_project()
        form.instance.project = project
        response = super().form_valid(form)
        AuditLog.objects.create(
            user=self.request.user,
            action='ADJUST_PRICE',
            model_name='PriceAdjustment',
            object_id=self.object.id,
            detail={'item_code': self.object.item_code, 'item_name': self.object.item_name}
        )
        messages.success(self.request, f"單價調整 「{self.object.item_name}」 已新增。")
        return response

    def get_success_url(self):
        return reverse('budget_review:project_detail', kwargs={'pk': self.kwargs.get('project_id')})

# Hidden Projects Management
class HiddenProjectListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """隱藏標案列表 - 僅超級管理員可見"""
    model = Project
    template_name = 'budget_review/hidden_project_list.html'
    context_object_name = 'projects'
    ordering = ['-deleted_at']
    
    def test_func(self):
        """僅超級管理員可查看"""
        from .permissions import can_access_hidden_projects
        return can_access_hidden_projects(self.request.user)
    
    def get_queryset(self):
        """僅顯示已刪除的標案"""
        return Project.objects.filter(deleted_at__isnull=False).order_by('-deleted_at')
class ProjectRestoreView(LoginRequiredMixin, UserPassesTestMixin, View):
    """復原標案"""
    
    def test_func(self):
        """僅超級管理員可復原"""
        from .permissions import can_restore_project
        return can_restore_project(self.request.user)
    
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        if not project.is_deleted:
            messages.warning(request, f"標案 「{project.name}」 未被刪除。")
            return redirect('budget_review:hidden_project_list')
        
        name = project.name
        # 復原：清除刪除時間與刪除者
        project.deleted_at = None
        project.deleted_by = None
        project.save()
        
        AuditLog.objects.create(
            user=request.user,
            action='UPDATE',
            model_name='Project',
            object_id=pk,
            detail={'name': name, 'action': 'restored'}
        )
        messages.success(request, f"標案 「{name}」 已成功復原。")
        return redirect('budget_review:project_list')
class ProjectPermanentDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """永久刪除標案"""
    
    def test_func(self):
        """僅超級管理員可永久刪除"""
        from .permissions import can_permanent_delete_project
        return can_permanent_delete_project(self.request.user)
    
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        if not project.is_deleted:
            messages.warning(request, "只能永久刪除已在隱藏列表中的標案。")
            return redirect('budget_review:hidden_project_list')
        
        name = project.name
        code = project.code
        
        # 記錄日誌後刪除
        AuditLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Project',
            object_id=pk,
            detail={'name': name, 'code': code, 'permanent': True}
        )
        
        # 真正刪除
        project.delete()
        
        messages.success(request, f"標案 「{name}」 已永久刪除。")
        return redirect('budget_review:hidden_project_list')