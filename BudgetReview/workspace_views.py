from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import DetailView, View
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db import models
from .models import Project, Stage, Discipline, AuditLog
from .models import QuantityFile, PriceInquiryFile, BudgetFile, FinalBudgetFile
from .validators import validate_file_extension

# Project Workspace Views
class ProjectWorkspaceView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """標案工作區 - 顯示特定階段的檔案管理介面"""
    model = Stage
    template_name = 'budget_review/project_workspace.html'
    context_object_name = 'stage'
    pk_url_kwarg = 'stage_id'
    
    def test_func(self):
        """檢查使用者是否有權限進入工作區"""
        from .permissions import has_project_admin_permission, has_discipline_admin_permission, has_budget_permission
        
        stage = self.get_object()
        project = stage.project
        user = self.request.user
        
        # 超級管理員、標案管理員、預算管理員有完整權限
        if user.is_superuser:
            return True
        if has_project_admin_permission(user, project):
            return True
        if user.groups.filter(name='Budget').exists():
            return True
        
        # 專業管理員/成員對自己的專業有權限
        disciplines = project.disciplines.filter(
            models.Q(responsible_user=user) | models.Q(members=user)
        ).distinct()
        if disciplines.exists():
            return True
        
        # 預算成員有權限
        if user.groups.filter(name__in=['Budget_Member']).exists():
            return True
            
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stage = self.get_object()
        project = stage.project
        user = self.request.user
        
        context['project'] = project
        
        # 取得所有專業分組，一般專業優先，最後才是整合專業
        disciplines = list(project.disciplines.all().order_by('is_overall', 'code'))
        
        # 權限檢查輔助
        from .permissions import has_project_admin_permission, has_discipline_member_permission
        is_admin = (
            user.is_superuser or 
            has_project_admin_permission(user, project) or
            user.groups.filter(name='Budget').exists()
        )
        context['is_admin'] = is_admin
        
        # 整合專業管理員判斷
        overall_discipline_obj = next((d for d in disciplines if d.is_overall), None)
        context['is_overall_admin'] = (
            overall_discipline_obj.responsible_user == user if overall_discipline_obj else False
        )
        
        # 為每個專業判斷當前使用者是否可上傳
        for d in disciplines:
            if is_admin:
                d.user_can_upload = True
            elif d.is_overall:
                d.user_can_upload = (d.responsible_user == user)
            else:
                d.user_can_upload = has_discipline_member_permission(user, d)
        
        def group_files_by_name(queryset):
            """將文件按名稱分組，並按版本降序排列"""
            groups = {}
            for f in queryset:
                if f.file_name not in groups:
                    groups[f.file_name] = []
                groups[f.file_name].append(f)
            
            # 轉換為列表以便模板迭代
            result = []
            for name, versions in groups.items():
                result.append({
                    'file_name': name,
                    'latest': versions[0] if versions else None,
                    'versions': versions
                })
            return result

        # 為每個專業取得當前階段的所有檔案，按名稱分組後供模板讀取
        for discipline in disciplines:
            discipline.grouped_quantity_files = group_files_by_name(
                QuantityFile.objects.filter(project=project, stage=stage, discipline=discipline).order_by('file_name', '-version')
            )
            
            discipline.grouped_price_files = group_files_by_name(
                PriceInquiryFile.objects.filter(project=project, stage=stage, discipline=discipline).order_by('file_name', '-version')
            )
            
            discipline.grouped_budget_files = group_files_by_name(
                BudgetFile.objects.filter(project=project, stage=stage, discipline=discipline).order_by('file_name', '-version')
            )
            
            discipline.grouped_blank_tender_files = group_files_by_name(
                FinalBudgetFile.objects.filter(project=project, stage=stage, discipline=discipline, file_type='BLANK_TENDER').order_by('file_name', '-version')
            )
        
        context['disciplines'] = disciplines
        
        # 檢查是否超過截止時間
        if stage.deadline:
            import pytz
            local_tz = pytz.timezone('Asia/Taipei')
            now = timezone.now().astimezone(local_tz)
            context['is_past_deadline'] = now > stage.deadline.astimezone(local_tz)
        else:
            context['is_past_deadline'] = False
        
        return context


class FileSubmitView(LoginRequiredMixin, UserPassesTestMixin, View):
    """檔案提送 View"""
    
    def test_func(self):
        """檢查使用者是否有權限提送檔案"""
        return True  # 詳細權限在 post 方法中檢查
    
    def post(self, request, file_type, file_id):
        """提送檔案"""
        from .permissions import has_project_admin_permission, has_discipline_admin_permission
        
        # 根據檔案類型獲取檔案
        file_models = {
            'quantity': QuantityFile,
            'price_inquiry': PriceInquiryFile,
            'price': PriceInquiryFile, # Alias for legacy
            'budget': BudgetFile,
            'final_budget': FinalBudgetFile,
            'blank_tender': FinalBudgetFile, # New standard
            'blank-tender': FinalBudgetFile, # Legacy alias
        }
        
        if file_type not in file_models:
            return JsonResponse({'success': False, 'message': '無效的檔案類型'})
        
        FileModel = file_models[file_type]
        file_obj = get_object_or_404(FileModel, pk=file_id)
        
        # 權限檢查
        user = request.user
        project = file_obj.project
        discipline = file_obj.discipline
        
        # 超級管理員、標案管理員、預算管理員有完整權限
        has_permission = (
            user.is_superuser or
            has_project_admin_permission(user, project) or
            user.groups.filter(name='Budget').exists()
        )
        
        # 專業相關權限
        if not has_permission and discipline:
            has_permission = has_discipline_admin_permission(user, discipline)
        
        if not has_permission:
            return JsonResponse({'success': False, 'message': '您沒有權限提送此檔案'})
        
        # 檢查是否為最新版本
        if not file_obj.is_latest:
            return JsonResponse({'success': False, 'message': '只能提送最新版本的檔案'})
        
        # 檢查截止時間（整合專業豁免）
        if file_obj.stage and file_obj.stage.deadline:
            import pytz
            local_tz = pytz.timezone('Asia/Taipei')
            now = timezone.now().astimezone(local_tz)
            deadline = file_obj.stage.deadline.astimezone(local_tz)
            
            # 一般專業需要檢查截止時間
            if discipline and not discipline.is_overall and now > deadline:
                return JsonResponse({
                    'success': False, 
                    'message': '已超過截止時間，無法提送檔案'
                })
        
        # 提送檔案
        file_obj.is_submitted = True
        file_obj.submitted_at = timezone.now()
        file_obj.submitted_by = user
        file_obj.save()
        
        # 記錄操作
        AuditLog.objects.create(
            user=user,
            action='SUBMIT',
            model_name=FileModel.__name__,
            object_id=file_obj.id,
            detail={
                'file_name': file_obj.file_name,
                'version': file_obj.version,
                'stage_id': file_obj.stage.id if file_obj.stage else None
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'檔案「{file_obj.file_name} v{file_obj.version}」已提送成功'
        })


class WorkspaceFileUploadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """工作區檔案上傳 - 簡化版本，直接處理上傳"""
    
    def test_func(self):
        return True
    
    def post(self, request, project_id, stage_id, file_type):
        """處理檔案上傳"""
        from .permissions import has_project_admin_permission, has_discipline_admin_permission
        
        project = get_object_or_404(Project, pk=project_id)
        stage = get_object_or_404(Stage, pk=stage_id, project=project)
        
        # 檢查檔案
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'message': '請選擇要上傳的檔案'})
        
        # 取得表單數據
        discipline_id = request.POST.get('discipline')
        description = request.POST.get('description', '')
        
        if not discipline_id:
            return JsonResponse({'success': False, 'message': '請選擇專業分組'})
        
        try:
            discipline = Discipline.objects.get(pk=discipline_id, project=project)
        except Discipline.DoesNotExist:
            return JsonResponse({'success': False, 'message': '找不到專業分組'})
        
        # 權限檢查
        user = request.user
        has_permission = (
            user.is_superuser or
            has_project_admin_permission(user, project) or
            user.groups.filter(name='Budget').exists() or
            has_discipline_admin_permission(user, discipline)
        )
        
        if not has_permission:
            return JsonResponse({'success': False, 'message': '您沒有權限上傳此檔案'})
        
        # 根據檔案類型選擇模型
        file_models = {
            'quantity': QuantityFile,
            'price_inquiry': PriceInquiryFile,
            'budget': BudgetFile,
            'blank_tender': FinalBudgetFile
        }
        
        file_labels = {
            'quantity': '數量計算書',
            'price_inquiry': '訪價資料',
            'budget': '預算書',
            'blank_tender': '空白標單'
        }
        
        if file_type not in file_models:
            return JsonResponse({'success': False, 'message': '無效的檔案類型'})
        
        FileModel = file_models[file_type]
        
        # 嚴格驗證檔案格式
        files_to_validate = request.FILES.getlist('file')
        for uploaded_file in files_to_validate:
            is_valid, error_msg = validate_file_extension(uploaded_file, file_type)
            if not is_valid:
                return JsonResponse({'success': False, 'message': error_msg})
        
        # 處理多檔案上傳（僅訪價）
        files_to_upload = request.FILES.getlist('file') if file_type == 'price_inquiry' else [request.FILES['file']]
        uploaded_count = 0
        last_version = 0
        
        for uploaded_file in files_to_upload:
            # 建立過濾器，僅針對同樣檔名的檔案
            version_filter = {
                'project': project,
                'stage': stage,
                'discipline': discipline,
                'file_name': uploaded_file.name
            }
            if file_type == 'blank_tender':
                version_filter['file_type'] = 'BLANK_TENDER'
            
            # 標記舊版本為非最新
            FileModel.objects.filter(**version_filter, is_latest=True).update(is_latest=False)
            
            # 取得該檔名的最新版本號
            latest_file = FileModel.objects.filter(**version_filter).order_by('-version').first()
            
            version = (latest_file.version + 1) if latest_file else 1
            last_version = version
            
            # 建立檔案物件
            file_kwargs = {
                'project': project,
                'stage': stage,
                'discipline': discipline,
                'file': uploaded_file,
                'file_name': uploaded_file.name,
                'version': version,
                'uploaded_by': user,
                'description': description,
                'is_latest': True,
                'is_submitted': False
            }
            
            if file_type == 'blank_tender':
                file_kwargs['file_type'] = 'BLANK_TENDER'
            
            file_obj = FileModel.objects.create(**file_kwargs)
            
            # 記錄操作
            AuditLog.objects.create(
                user=user,
                action='UPLOAD',
                model_name=FileModel.__name__,
                object_id=file_obj.id,
                detail={
                    'file_name': uploaded_file.name,
                    'version': version,
                    'stage_id': stage.id,
                    'discipline': discipline.name
                }
            )
            
            uploaded_count += 1
        
        # 返回成功訊息
        if uploaded_count == 1:
            message = f'{file_labels[file_type]}「{files_to_upload[0].name}」(v{last_version}) 上傳成功（未提送）'
        else:
            message = f'已上傳 {uploaded_count} 個{file_labels[file_type]}檔案（未提送）'
        
        return JsonResponse({
            'success': True,
            'message': message
        })


# Integration Area View
class IntegrationAreaView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """標案整合區 - 顯示各專業已提送的檔案"""
    model = Stage
    template_name = 'budget_review/project_integration.html'
    context_object_name = 'stage'
    pk_url_kwarg = 'stage_id'
    
    def test_func(self):
        """檢查使用者是否有權限進入整合區"""
        from .permissions import has_project_admin_permission
        
        stage = self.get_object()
        project = stage.project
        user = self.request.user
        
        # 超級管理員、標案管理員、預算管理員有完整權限
        if user.is_superuser:
            return True
        if has_project_admin_permission(user, project):
            return True
        if user.groups.filter(name='Budget').exists():
            return True
        
        # 整合專業管理員
        overall_discipline = project.disciplines.filter(is_overall=True).first()
        if overall_discipline and overall_discipline.responsible_user == user:
            return True
        
        # 專業管理員/成員對自己的專業有查看權限
        disciplines = project.disciplines.filter(
            models.Q(responsible_user=user) | models.Q(members=user)
        ).distinct()
        if disciplines.exists():
            return True
        
        # 預算成員有權限
        if user.groups.filter(name='Budget_Member').exists():
            return True
            
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stage = self.get_object()
        project = stage.project
        user = self.request.user
        
        context['project'] = project
        
        # 判斷使用者角色
        from .permissions import has_project_admin_permission
        is_admin = (
            user.is_superuser or 
            has_project_admin_permission(user, project) or
            user.groups.filter(name='Budget').exists()
        )
        context['is_admin'] = is_admin
        
        # 取得整合專業
        overall_discipline = project.disciplines.filter(is_overall=True).first()
        is_overall_admin = False
        if overall_discipline:
            is_overall_admin = (overall_discipline.responsible_user == user)
        context['is_overall_admin'] = is_overall_admin
        context['overall_discipline'] = overall_discipline
    
        # 取得所有專業 (提送區應可查閱所有專業已提送檔案)
        disciplines = project.disciplines.all().order_by('is_overall', 'code')
    
        context['disciplines'] = disciplines
        
        # 取得各專業的已提送檔案，並按檔名分組
        def group_submitted_files_by_name(queryset):
            groups = {}
            for f in queryset:
                if f.file_name not in groups:
                    groups[f.file_name] = []
                groups[f.file_name].append(f)
            result = []
            for name, versions in groups.items():
                result.append({
                    'file_name': name,
                    'latest': versions[0] if versions else None,
                    'versions': versions
                })
            return result

        submissions_by_discipline = {}
        for discipline in disciplines:
            # 獲取已提送檔案的 QuerySets
            qty_qs = QuantityFile.objects.filter(project=project, stage=stage, discipline=discipline, is_submitted=True).order_by('file_name', '-version')
            prc_qs = PriceInquiryFile.objects.filter(project=project, stage=stage, discipline=discipline, is_submitted=True).order_by('file_name', '-version')
            bud_qs = BudgetFile.objects.filter(project=project, stage=stage, discipline=discipline, is_submitted=True).order_by('file_name', '-version')
            bln_qs = FinalBudgetFile.objects.filter(project=project, stage=stage, discipline=discipline, file_type='BLANK_TENDER', is_submitted=True).order_by('file_name', '-version')

            submissions_by_discipline[discipline.id] = {
                'discipline': discipline,
                # 指標用的 QuerySets (原始)
                'quantity_qs': qty_qs,
                'price_qs': prc_qs,
                'budget_qs': bud_qs,
                'blank_tender_qs': bln_qs,
            }
        
            # 附加分組數據到專業對象上，方便模板讀取 (比照工作區)
            discipline.grouped_quantity_files = group_submitted_files_by_name(qty_qs)
            discipline.grouped_price_files = group_submitted_files_by_name(prc_qs)
            discipline.grouped_budget_files = group_submitted_files_by_name(bud_qs)
            discipline.grouped_blank_tender_files = group_submitted_files_by_name(bln_qs)
        
            # 計算提送進度
            submission_summary = self._calculate_submission_progress(
                stage, discipline, submissions_by_discipline[discipline.id]
            )
            submissions_by_discipline[discipline.id]['submission_summary'] = submission_summary
        
        context['submissions_by_discipline'] = submissions_by_discipline
        
        # 計算整體進度
        overall_progress = self._calculate_overall_progress(submissions_by_discipline)
        context['overall_progress'] = overall_progress
        
        # 檢查是否超過截止時間
        if stage.deadline:
            import pytz
            local_tz = pytz.timezone('Asia/Taipei')
            now = timezone.now().astimezone(local_tz)
            context['is_past_deadline'] = now > stage.deadline.astimezone(local_tz)
        else:
            context['is_past_deadline'] = False
        
        return context
    
    def _calculate_submission_progress(self, stage, discipline, files_dict):
        """計算單一專業的提送進度"""
        if discipline.is_overall:
            # 整合專業：整合預算書、空白標單
            expected_types = ['budget', 'blank_tender']
            submitted_count = 0
            
            if files_dict['budget_qs'].exists():
                submitted_count += 1
            if files_dict['blank_tender_qs'].exists():
                submitted_count += 1
        else:
            # 一般專業：數量、訪價、預算
            expected_types = ['quantity', 'price_inquiry', 'budget']
            submitted_count = 0
            
            if files_dict['quantity_qs'].exists():
                submitted_count += 1
            if files_dict['price_qs'].exists():
                submitted_count += 1
            if files_dict['budget_qs'].exists():
                submitted_count += 1
        
        total_expected = len(expected_types)
        is_complete = submitted_count == total_expected
        
        # 取得最後提送時間
        last_submitted_at = None
        all_files = list(files_dict['quantity_qs']) + \
                   list(files_dict['price_qs']) + \
                   list(files_dict['budget_qs']) + \
                   list(files_dict['blank_tender_qs'])
        
        if all_files:
            submitted_files = [f for f in all_files if f.submitted_at]
            if submitted_files:
                last_submitted_at = max(f.submitted_at for f in submitted_files)
        
        return {
            'total_expected': total_expected,
            'total_submitted': submitted_count,
            'is_complete': is_complete,
            'completion_rate': (submitted_count / total_expected * 100) if total_expected > 0 else 0,
            'last_submitted_at': last_submitted_at,
        }
    
    def _calculate_overall_progress(self, submissions_by_discipline):
        """計算整體進度"""
        total_disciplines = len(submissions_by_discipline)
        complete_disciplines = sum(
            1 for data in submissions_by_discipline.values()
            if data['submission_summary']['is_complete']
        )
        
        completion_rate = (complete_disciplines / total_disciplines * 100) if total_disciplines > 0 else 0
        
        return {
            'total_disciplines': total_disciplines,
            'complete_disciplines': complete_disciplines,
            'completion_rate': completion_rate,
        }


