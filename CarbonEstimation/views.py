from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import models
import json
from .models import MainCategory, ComponentItem, Scenario, ScenarioData


def calculator_view(request):
    """計算器主頁面"""
    categories = MainCategory.objects.all().prefetch_related('items')
    
    data = []
    for category in categories:
        data.append({
            'category': category,
            'items': category.items.all()
        })
    
    context = {
        'page_title': '常用組件碳排概算平台',
        'data': data
    }
    
    return render(request, 'carbon_estimation/calculator.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def create_scenario(request):
    """創建新方案並儲存分類數據"""
    try:
        data = json.loads(request.body)
        
        # Create scenario
        scenario = Scenario.objects.create(
            project_number=data.get('project_number'),
            project_name=data.get('project_name'),
            scenario_name=data.get('scenario_name'),
            creator=request.user if request.user.is_authenticated else None
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
def delete_scenario(request, scenario_id):
    """刪除方案"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        
        # Check permission
        if not scenario.can_delete(request.user):
            return JsonResponse({
                'success': False, 
                'error': '您沒有權限刪除此方案'
            }, status=403)
            
        scenario.delete()
        return JsonResponse({'success': True, 'message': '方案已刪除'})
        
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
def manage_collaborators(request, scenario_id):
    """管理協作人員"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
        
        # Check permission (only creator can manage collaborators)
        if request.user.is_authenticated and scenario.creator != request.user:
            return JsonResponse({'success': False, 'error': '只有建立者可以管理協作人員'}, status=403)
            
        data = json.loads(request.body)
        action = data.get('action')
        username = data.get('username')
        
        if not username:
            return JsonResponse({'success': False, 'error': '請提供使用者名稱'}, status=400)
            
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
            
        return JsonResponse({
            'success': True, 
            'message': message,
            'collaborators': [u.username for u in scenario.collaborators.all()]
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def scenario_list(request):
    """方案管理頁面"""
    scenarios = Scenario.objects.all().order_by('-updated_at')
    
    if request.user.is_authenticated:
        scenarios = scenarios.filter(
            models.Q(creator=request.user) | models.Q(collaborators=request.user)
        ).distinct()
    
    context = {
        'scenarios': scenarios
    }
    
    return render(request, 'carbon_estimation/scenario_list.html', context)
