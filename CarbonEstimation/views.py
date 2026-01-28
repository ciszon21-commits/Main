from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from django.utils import timezone
import json
from .models import MainCategory, ComponentItem, Scenario, ScenarioData, SectionCategory, SectionItem, ScenarioSectionData
from UserProfile.models import UserProfile


@login_required
def calculator_view(request):
    """計算器主頁面"""
    scenario_id = request.GET.get('scenario')
    categories = MainCategory.objects.all().prefetch_related('items')
    
    data = []
    for category in categories:
        data.append({
            'category': category,
            'items': category.items.all()
        })
    
    scenario = None
    if scenario_id:
        scenario = Scenario.objects.filter(id=scenario_id).first()
    
    context = {
        'page_title': '綜規及基設階段-常用組件碳排概算',
        'data': data,
        'scenario_id': scenario_id,
        'scenario': scenario
    }
    
    return render(request, 'carbon_estimation/calculator.html', context)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def create_scenario(request):
    """創建新方案並儲存分類數據"""
    try:
        data = json.loads(request.body)
        
        # Create scenario (creator is always the logged-in user)
        scenario = Scenario.objects.create(
            project_number=data.get('project_number'),
            project_name=data.get('project_name'),
            scenario_name=data.get('scenario_name'),
            project_phase=data.get('project_phase', 'comprehensive'),
            creator=request.user
        )
        
        # Save category data if provided
        category_id = data.get('category_id')
        if category_id:
            category = get_object_or_404(MainCategory, id=category_id)
            
            for item_data in data.get('data', []):
                component_item = get_object_or_404(ComponentItem, id=item_data['component_item_id'])
                ScenarioData.objects.create(
                    scenario=scenario,
                    component_item=component_item,
                    category=category,
                    quantity=item_data['quantity']
                )
        
        return JsonResponse({
            'success': True,
            'scenario_id': scenario.id,
            'message': '方案已成功建立'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def save_category_data(request, scenario_id):
    """儲存特定分類的數據到現有方案"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        data = json.loads(request.body)
        
        category_id = data.get('category_id')
        category = get_object_or_404(MainCategory, id=category_id)
        
        # Delete existing data for this category in this scenario
        ScenarioData.objects.filter(scenario=scenario, category=category).delete()
        
        # Save new data
        for item_data in data.get('data', []):
            component_item = get_object_or_404(ComponentItem, id=item_data['component_item_id'])
            ScenarioData.objects.create(
                scenario=scenario,
                component_item=component_item,
                category=category,
                quantity=item_data['quantity']
            )
        
        # Update scenario timestamp
        scenario.save()
        
        return JsonResponse({
            'success': True,
            'message': '分類數據已儲存'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    finally:
        # Update timestamp even if save failed partially, or ensure it's called on success.
        # Ideally only on success, but using finally for safety if needed, 
        # but better to put it before return success.
        pass

    
@require_http_methods(["PUT"])
@csrf_exempt
def update_scenario(request, scenario_id):
    """更新方案基本資訊"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        
        # Check permission (similar to can_edit)
        if not scenario.can_edit(request.user):
             return JsonResponse({
                'success': False, 
                'error': '您沒有權限修改此方案'
            }, status=403)
            
        data = json.loads(request.body)
        
        # Update fields
        scenario.project_number = data.get('project_number', scenario.project_number)
        scenario.project_name = data.get('project_name', scenario.project_name)
        scenario.scenario_name = data.get('scenario_name', scenario.scenario_name)
        scenario.description = data.get('description', scenario.description)
        
        scenario.save()
        
        return JsonResponse({
            'success': True,
            'message': '方案資訊已更新',
            'scenario': {
                'id': scenario.id,
                'project_number': scenario.project_number,
                'project_name': scenario.project_name,
                'scenario_name': scenario.scenario_name,
                'description': scenario.description
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["DELETE"])
@csrf_exempt
@login_required
def delete_scenario(request, scenario_id):
    """刪除方案（軟刪除或永久刪除）"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        
        # 權限檢查：只有創建者或管理員可以刪除
        if not scenario.can_delete(request.user) and not request.user.is_superuser:
            return JsonResponse({
                'success': False, 
                'error': '您沒有權限刪除此方案（僅創建者可以刪除）'
            }, status=403)
        
        # 管理員可以選擇永久刪除
        permanent = request.GET.get('permanent', 'false').lower() == 'true'
        
        if request.user.is_superuser and permanent:
            # 永久刪除
            scenario.delete()
            message = '方案已永久刪除'
        else:
            # 軟刪除（隱藏）
            scenario.is_hidden = True
            scenario.hidden_at = timezone.now()
            scenario.hidden_by = request.user
            scenario.save()
            message = '方案已隱藏'
        
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def restore_scenario(request, scenario_id):
    """復原隱藏的方案（僅管理員）"""
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': '只有管理員可以復原方案'
        }, status=403)
    
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id, is_hidden=True)
        
        scenario.is_hidden = False
        scenario.hidden_at = None
        scenario.hidden_by = None
        scenario.save()
        
        return JsonResponse({
            'success': True,
            'message': '方案已復原'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def load_scenario(request, scenario_id):
    """載入方案數據"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        scenario_data = ScenarioData.objects.filter(scenario=scenario).select_related(
            'component_item', 'category'
        )
        
        data = {}
        for item in scenario_data:
            data[str(item.component_item.id)] = float(item.quantity)
        
        return JsonResponse({
            'success': True,
            'scenario': {
                'id': scenario.id,
                'project_number': scenario.project_number,
                'project_name': scenario.project_name,
                'scenario_name': scenario.scenario_name,
            },
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def manage_collaborators(request, scenario_id):
    """管理協作人員"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        
        # Check permission (only creator can manage collaborators)
        if scenario.creator != request.user:
            return JsonResponse({'success': False, 'error': '只有建立者可以管理協作人員'}, status=403)
            
        data = json.loads(request.body)
        action = data.get('action')
        username = data.get('username')
        
        if action != 'list' and not username:
            return JsonResponse({'success': False, 'error': '請提供使用者名稱'}, status=400)
            
        if action == 'list':
            message = '協作人員列表'
        elif username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': '找不到此使用者'}, status=404)
                
            if action == 'add':
                if user == scenario.creator:
                    return JsonResponse({'success': False, 'error': '建立者已經擁有權限'}, status=400)
                scenario.collaborators.add(user)
                message = f'已加入協作人員 {username}'
            elif action == 'remove':
                scenario.collaborators.remove(user)
                message = f'已移除協作人員 {username}'
            else:
                return JsonResponse({'success': False, 'error': '無效的操作'}, status=400)
        else:
            return JsonResponse({'success': False, 'error': '無效的操作'}, status=400)
            
        return JsonResponse({
            'success': True, 
            'message': message,
            'collaborators': [
                {
                    'username': u.username, 
                    'display': (u.profile.get_full_name() if hasattr(u, 'profile') else u.get_full_name()) or u.username
                } for u in scenario.collaborators.all()
            ]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def scenario_list(request):
    """方案管理頁面"""
    # 超級管理員：可以看到所有方案
    # 一般使用者：只能看到自己創建或被分享的方案（且未隱藏）
    
    if request.user.is_superuser:
        # 超級管理員看到所有未隱藏的方案
        scenarios = Scenario.objects.filter(is_hidden=False).order_by('-updated_at')
        # 超級管理員可以看到隱藏的方案
        hidden_scenarios = Scenario.objects.filter(is_hidden=True).order_by('-hidden_at')
    else:
        # 一般使用者只看到自己的未隱藏方案
        scenarios = Scenario.objects.filter(
            models.Q(creator=request.user) | models.Q(collaborators=request.user),
            is_hidden=False
        ).distinct().order_by('-updated_at')
        hidden_scenarios = None
    
    # Get user display name
    current_name = request.user.get_full_name() or request.user.username
    current_user_display = current_name
    
    if hasattr(request.user, 'profile') and request.user.profile.emp_name:
        current_user_display = f"{request.user.profile.emp_name} ({current_name})"
            
    context = {
        'scenarios': scenarios,
        'hidden_scenarios': hidden_scenarios,
        'is_superuser': request.user.is_superuser,
        'current_user_display': current_user_display
    }
    
    return render(request, 'carbon_estimation/scenario_list.html', context)


@login_required
def hidden_scenario_list(request):
    """隱藏方案列表頁面（僅管理員）"""
    if not request.user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': '只有管理員可以訪問此頁面'
        }, status=403)
    
    # 獲取所有隱藏的方案
    hidden_scenarios = Scenario.objects.filter(is_hidden=True).order_by('-hidden_at')
    
    context = {
        'hidden_scenarios': hidden_scenarios
    }
    
    return render(request, 'carbon_estimation/hidden_scenarios.html', context)


@login_required
def search_users(request):
    """搜尋使用者 API (含 UserProfile 資訊)"""
    q = request.GET.get('q', '')
    
    # Use prefetch_related for reverse OneToOne relation
    users = User.objects.exclude(id=request.user.id).prefetch_related('profile').order_by('username')
    
    if q:
        # Search by username OR employee name OR partial full name
        users = users.filter(
            models.Q(username__icontains=q) | 
            models.Q(profile__emp_name__icontains=q) |
            models.Q(first_name__icontains=q) |
            models.Q(last_name__icontains=q)
        )
    
    data = []
    for user in users:
        # Default display
        display_name = user.username
        dept = ""
        
        # Try to get profile data
        if hasattr(user, 'profile'):
            profile = user.profile
            name = profile.get_full_name()
            dept = profile.dept_display  # Use the property from model
            
            if name:
                display_name = f"{name} ({user.username})"
        
        if dept:
            display_name += f" - {dept}"
        
        data.append({
            'username': user.username,
            'display': display_name
        })
    
    return JsonResponse({'users': data})


# ==============================================================================
# 斷面概算相關 Views
# ==============================================================================

@login_required
def section_calculator_view(request):
    """斷面計算器主頁面"""
    scenario_id = request.GET.get('scenario')
    
    categories = SectionCategory.objects.all().prefetch_related('items')
    
    data = []
    for category in categories:
        data.append({
            'category': category,
            'items': category.items.all()
        })
    
    scenario = None
    if scenario_id:
        scenario = Scenario.objects.filter(id=scenario_id).first()
    
    context = {
        'page_title': '可評階段-標準斷面碳排概算',
        'data': data,
        'scenario_id': scenario_id,
        'scenario': scenario
    }
    
    return render(request, 'carbon_estimation/section_calculator.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def save_section_data(request, scenario_id):
    """儲存斷面數據到現有方案"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        data = json.loads(request.body)
        
        category_id = data.get('category_id')
        if category_id:
            category = get_object_or_404(SectionCategory, id=category_id)
            
            # Delete existing data for this category in this scenario
            ScenarioSectionData.objects.filter(scenario=scenario, category=category).delete()
            
            # Save new data
            for item_data in data.get('data', []):
                section_item = get_object_or_404(SectionItem, id=item_data['section_item_id'])
                ScenarioSectionData.objects.create(
                    scenario=scenario,
                    section_item=section_item,
                    category=category,
                    quantity=item_data['quantity']
                )
        
        # Update scenario timestamp
        scenario.save()
        
        return JsonResponse({
            'success': True,
            'message': '分類數據已儲存'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@require_http_methods(["GET"])
def load_section_scenario(request, scenario_id):
    """載入斷面方案數據"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        scenario_data = ScenarioSectionData.objects.filter(scenario=scenario).select_related(
            'section_item', 'category'
        )
        
        data = {}
        for item in scenario_data:
            data[str(item.section_item.id)] = float(item.quantity)
        
        return JsonResponse({
            'success': True,
            'scenario': {
                'id': scenario.id,
                'project_number': scenario.project_number,
                'project_name': scenario.project_name,
                'scenario_name': scenario.scenario_name,
            },
            'data': data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
