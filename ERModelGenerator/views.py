from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from functools import wraps
from .utils.scanner import (
    generate_mermaid_er,
    get_project_app_labels,
    get_app_model_stats,
    generate_mermaid_for_single_app,
    get_models_for_app,
)


def admin_required(view_func):
    """
    裝飾器：要求用戶必須是 superuser 或 staff 才能訪問
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not (request.user.is_superuser or request.user.is_staff):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden(
                '<h1>403 Forbidden</h1>'
                '<p>您沒有權限訪問此頁面。此功能僅限管理員使用。</p>'
                '<p><a href="/">返回首頁</a></p>'
            )
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def er_diagram_view(request):
    """
    ER 圖主頁面視圖
    
    支援的 GET 參數:
    - apps: 逗號分隔的 app labels，用於篩選顯示的 apps
    - show_fields: 是否顯示欄位 (1/0)，預設為 1
    - show_types: 是否顯示欄位類型 (1/0)，預設為 1
    - view_mode: 檢視模式 (single/multi/relations)，預設為 single
    - current_app: 目前顯示的單一 app (view_mode=single 時使用)
    """
    # 取得所有專案 apps
    all_apps = get_project_app_labels()
    app_stats = get_app_model_stats()
    
    # 檢視模式
    view_mode = request.GET.get('view_mode', 'single')  # single, multi, relations
    
    # 目前選中的 app (single 模式)
    current_app = request.GET.get('current_app', '')
    if current_app and current_app not in all_apps:
        current_app = ''
    if not current_app and all_apps:
        current_app = all_apps[0]  # 預設第一個 app
    
    # 取得篩選參數 (multi 模式使用)
    selected_apps_param = request.GET.get('apps', '')
    if selected_apps_param:
        selected_apps = [app.strip() for app in selected_apps_param.split(',') if app.strip()]
        selected_apps = [app for app in selected_apps if app in all_apps]
    else:
        selected_apps = []
    
    show_fields = request.GET.get('show_fields', '1') == '1'
    show_types = request.GET.get('show_types', '1') == '1'
    
    # 根據模式產生 Mermaid 語法
    if view_mode == 'single' and current_app:
        # 單一 App 模式
        mermaid_code = generate_mermaid_er(
            app_labels=[current_app],
            show_fields=show_fields,
            show_field_types=show_types,
            group_by_app=False
        )
        displayed_apps = [current_app]
        total_models = app_stats.get(current_app, 0)
    elif view_mode == 'multi' and selected_apps:
        # 多 App 模式
        mermaid_code = generate_mermaid_er(
            app_labels=selected_apps,
            show_fields=show_fields,
            show_field_types=show_types,
            group_by_app=True
        )
        displayed_apps = selected_apps
        total_models = sum(app_stats.get(app, 0) for app in selected_apps)
    elif view_mode == 'relations':
        # 僅關聯模式 (不顯示欄位，適合全覽)
        mermaid_code = generate_mermaid_er(
            app_labels=None,
            show_fields=False,
            show_field_types=False,
            group_by_app=True
        )
        displayed_apps = all_apps
        total_models = sum(app_stats.values())
    else:
        # 預設：單一 app
        if current_app:
            mermaid_code = generate_mermaid_er(
                app_labels=[current_app],
                show_fields=show_fields,
                show_field_types=show_types,
                group_by_app=False
            )
            displayed_apps = [current_app]
            total_models = app_stats.get(current_app, 0)
        else:
            mermaid_code = "erDiagram\n    %% No apps found"
            displayed_apps = []
            total_models = 0
    
    context = {
        'mermaid_code': mermaid_code,
        'all_apps': all_apps,
        'app_stats': app_stats,
        'selected_apps': selected_apps,
        'displayed_apps': displayed_apps,
        'total_models': total_models,
        'total_apps': len(displayed_apps),
        'show_fields': show_fields,
        'show_types': show_types,
        'view_mode': view_mode,
        'current_app': current_app,
    }
    
    return render(request, 'ERModelGenerator/er_diagram.html', context)


@admin_required
@require_GET
def api_mermaid_code(request):
    """
    API: 取得 Mermaid 程式碼
    
    GET 參數:
    - apps: 逗號分隔的 app labels
    - show_fields: 是否顯示欄位 (1/0)
    - show_types: 是否顯示欄位類型 (1/0)
    """
    all_apps = get_project_app_labels()
    
    selected_apps_param = request.GET.get('apps', '')
    if selected_apps_param:
        selected_apps = [app.strip() for app in selected_apps_param.split(',') if app.strip()]
        selected_apps = [app for app in selected_apps if app in all_apps]
    else:
        selected_apps = None
    
    show_fields = request.GET.get('show_fields', '1') == '1'
    show_types = request.GET.get('show_types', '1') == '1'
    
    mermaid_code = generate_mermaid_er(
        app_labels=selected_apps,
        show_fields=show_fields,
        show_field_types=show_types,
        group_by_app=True
    )
    
    return JsonResponse({
        'success': True,
        'mermaid_code': mermaid_code,
        'apps_count': len(selected_apps) if selected_apps else len(all_apps),
    })


@admin_required
@require_GET
def api_app_list(request):
    """API: 取得 App 列表和統計"""
    all_apps = get_project_app_labels()
    app_stats = get_app_model_stats()
    
    apps_info = []
    for app in all_apps:
        model_count = app_stats.get(app, 0)
        apps_info.append({
            'label': app,
            'model_count': model_count,
        })
    
    return JsonResponse({
        'success': True,
        'apps': apps_info,
        'total_apps': len(all_apps),
        'total_models': sum(app_stats.values()),
    })


@admin_required
@require_GET
def api_app_models(request, app_label):
    """API: 取得指定 App 的 Models 資訊"""
    models_list = get_models_for_app(app_label)
    
    if not models_list:
        return JsonResponse({
            'success': False,
            'error': f'App "{app_label}" not found or has no models',
        })
    
    models_info = []
    for model in models_list:
        fields_info = [
            {
                'name': f.name,
                'type': f.field_type,
                'is_pk': f.is_pk,
                'is_fk': f.is_fk,
                'verbose_name': f.verbose_name,
            }
            for f in model.fields
        ]
        
        relations_info = [
            {
                'to_model': f'{r.to_app}.{r.to_model}',
                'type': r.relation_type,
                'field_name': r.field_name,
            }
            for r in model.relations
        ]
        
        models_info.append({
            'name': model.name,
            'verbose_name': model.verbose_name,
            'db_table': model.db_table,
            'fields': fields_info,
            'relations': relations_info,
            'fields_count': len(fields_info),
            'relations_count': len(relations_info),
        })
    
    return JsonResponse({
        'success': True,
        'app_label': app_label,
        'models': models_info,
        'models_count': len(models_info),
    })


@admin_required
def download_mermaid(request):
    """下載 Mermaid 原始碼為 .mmd 檔案"""
    all_apps = get_project_app_labels()
    
    selected_apps_param = request.GET.get('apps', '')
    if selected_apps_param:
        selected_apps = [app.strip() for app in selected_apps_param.split(',') if app.strip()]
        selected_apps = [app for app in selected_apps if app in all_apps]
    else:
        selected_apps = None
    
    show_fields = request.GET.get('show_fields', '1') == '1'
    show_types = request.GET.get('show_types', '1') == '1'
    
    mermaid_code = generate_mermaid_er(
        app_labels=selected_apps,
        show_fields=show_fields,
        show_field_types=show_types,
        group_by_app=True
    )
    
    # 產生檔案名稱
    if selected_apps and len(selected_apps) <= 3:
        filename = f"er_diagram_{'_'.join(selected_apps)}.mmd"
    else:
        filename = "er_diagram_full.mmd"
    
    response = HttpResponse(mermaid_code, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
