from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import View
from django.http import JsonResponse
from .models import Project, AuditLog

# Stage Management Views
class StageCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """建立標案階段"""
    
    def test_func(self):
        """檢查是否有標案管理權限"""
        from .permissions import has_project_admin_permission
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, pk=project_id)
        return has_project_admin_permission(self.request.user, project)
    
    def get(self, request, project_id):
        from .stage_forms import StageForm
        project = get_object_or_404(Project, pk=project_id)
        form = StageForm()
        
        html = render(request, 'budget_review/stage_form_ajax.html', {
            'form': form,
            'project': project,
            'stage': None
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id):
        from .stage_forms import StageForm
        from .models import Stage
        
        project = get_object_or_404(Project, pk=project_id)
        form = StageForm(request.POST)
        
        if form.is_valid():
            stage = form.save(commit=False)
            stage.project = project
            stage.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='CREATE',
                model_name='Stage',
                object_id=stage.id,
                detail={'name': stage.name, 'project_id': project.id, 'order': stage.order}
            )
            
            return JsonResponse({
                'success': True,
                'message': f'階段「{stage.name}」已建立成功。'
            })
        else:
            html = render(request, 'budget_review/stage_form_ajax.html', {
                'form': form,
                'project': project,
                'stage': None
            }).content.decode('utf-8')
            
            return JsonResponse({
                'success': False,
                'html': html
            })


class StageUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """編輯標案階段"""
    
    def test_func(self):
        """檢查是否有標案管理權限"""
        from .permissions import has_project_admin_permission
        from .models import Stage
        
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, pk=project_id)
        return has_project_admin_permission(self.request.user, project)
    
    def get(self, request, project_id, pk):
        from .stage_forms import StageForm
        from .models import Stage
        
        project = get_object_or_404(Project, pk=project_id)
        stage = get_object_or_404(Stage, pk=pk, project=project)
        form = StageForm(instance=stage)
        
        html = render(request, 'budget_review/stage_form_ajax.html', {
            'form': form,
            'project': project,
            'stage': stage
        }).content.decode('utf-8')
        
        return JsonResponse({'html': html})
    
    def post(self, request, project_id, pk):
        from .stage_forms import StageForm
        from .models import Stage
        
        project = get_object_or_404(Project, pk=project_id)
        stage = get_object_or_404(Stage, pk=pk, project=project)
        form = StageForm(request.POST, instance=stage)
        
        if form.is_valid():
            stage = form.save()
            
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE',
                model_name='Stage',
                object_id=stage.id,
                detail={'name': stage.name, 'project_id': project.id, 'order': stage.order}
            )
            
            return JsonResponse({
                'success': True,
                'message': f'階段「{stage.name}」已更新成功。'
            })
        else:
            html = render(request, 'budget_review/stage_form_ajax.html', {
                'form': form,
                'project': project,
                'stage': stage
            }).content.decode('utf-8')
            
            return JsonResponse({
                'success': False,
                'html': html
            })


class StageDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """刪除標案階段"""
    
    def test_func(self):
        """檢查是否有標案管理權限"""
        from .permissions import has_project_admin_permission
        from .models import Stage
        
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, pk=project_id)
        return has_project_admin_permission(self.request.user, project)
    
    def post(self, request, project_id, pk):
        from .models import Stage
        
        project = get_object_or_404(Project, pk=project_id)
        stage = get_object_or_404(Stage, pk=pk, project=project)
        
        name = stage.name
        stage.delete()
        
        AuditLog.objects.create(
            user=request.user,
            action='DELETE',
            model_name='Stage',
            object_id=pk,
            detail={'name': name, 'project_id': project_id}
        )
        
        return JsonResponse({
            'success': True,
            'message': f'階段「{name}」已刪除。'
        })
