"""
Site360 使用者操作記錄系統 - 工具函數

提供中間件和視圖所需的輔助函數
"""
from django.contrib.contenttypes.models import ContentType
import json
import re


def get_client_ip(request):
    """
    從 request 中提取客戶端真實 IP 地址
    考慮代理和負載均衡的情況
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    從 request 中提取用戶代理資訊
    """
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def get_action_type_from_request(request, view_name=''):
    """
    根據請求方法和視圖名稱判斷操作類型
    
    Args:
        request: Django request object
        view_name: 視圖名稱（可選）
        
    Returns:
        str: 操作類型（對應 UserActionLog.ACTION_TYPE_CHOICES）
    """
    method = request.method
    path = request.path.lower()
    
    # 登入/登出
    if 'login' in path:
        return 'LOGIN'
    if 'logout' in path:
        return 'LOGOUT'
    
    # 特定操作
    if 'upload' in path or 'upload' in view_name.lower():
        return 'UPLOAD'
    if 'download' in path or 'download' in view_name.lower():
        return 'DOWNLOAD'
    if 'reorder' in path:
        return 'REORDER'
    if 'move' in path:
        return 'MOVE'
    if 'set-cover' in path or 'set_cover' in path:
        return 'SET_COVER'
    if 'reference' in path or 'library' in path:
        return 'REFERENCE'
    
    # 標準 CRUD 操作
    if method == 'POST':
        return 'CREATE'
    elif method in ['PUT', 'PATCH']:
        return 'UPDATE'
    elif method == 'DELETE':
        return 'DELETE'
    elif method == 'GET':
        # 只有特定的 GET 請求才記錄為 VIEW
        if any(keyword in path for keyword in ['/tour/', '/detail/', '/map/']):
            return 'VIEW'
        return None  # 一般的 GET 請求不記錄
    
    return 'OTHER'


def extract_object_info(request, response=None):
    """
    從請求（和響應）中提取操作對象資訊
    
    Returns:
        dict: 包含 content_type, object_id, object_repr 的字典
    """
    result = {
        'content_type': None,
        'object_id': None,
        'object_repr': ''
    }
    
    path = request.path
    
    # 從 URL 中提取 ID（假設格式為 /app/model/123/ 或 /app/model/123/action/）
    # 匹配 site360 的 URL 格式
    patterns = [
        r'/site360/projects/(\d+)/',
        r'/site360/scenes/(\d+)/',
        r'/site360/hotspots/(\d+)/',
        r'/site360/scene/(\d+)/',
        r'/site360/project/(\d+)/',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, path)
        if match:
            result['object_id'] = int(match.group(1))
            
            # 根據 URL 路徑判斷 content_type
            if '/projects/' in path or '/project/' in path:
                from .models import Project
                result['content_type'] = ContentType.objects.get_for_model(Project)
                try:
                    obj = Project.objects.get(pk=result['object_id'])
                    result['object_repr'] = str(obj)
                except Project.DoesNotExist:
                    result['object_repr'] = f"專案 #{result['object_id']}"
                    
            elif '/scenes/' in path or '/scene/' in path:
                from .models import Scene
                result['content_type'] = ContentType.objects.get_for_model(Scene)
                try:
                    obj = Scene.objects.get(pk=result['object_id'])
                    result['object_repr'] = str(obj)
                except Scene.DoesNotExist:
                    result['object_repr'] = f"場景 #{result['object_id']}"
                    
            elif '/hotspots/' in path:
                from .models import Hotspot
                result['content_type'] = ContentType.objects.get_for_model(Hotspot)
                try:
                    obj = Hotspot.objects.get(pk=result['object_id'])
                    result['object_repr'] = str(obj)
                except Hotspot.DoesNotExist:
                    result['object_repr'] = f"熱點 #{result['object_id']}"
            
            break
    
    # 如果 URL 中沒有 ID，檢查 POST 數據
    if not result['object_id'] and request.method in ['POST', 'PUT', 'PATCH']:
        # 從 POST 數據中獲取相關資訊
        if 'project' in request.POST:
            from .models import Project
            try:
                project_id = int(request.POST['project'])
                result['object_id'] = project_id
                result['content_type'] = ContentType.objects.get_for_model(Project)
                obj = Project.objects.get(pk=project_id)
                result['object_repr'] = str(obj)
            except (ValueError, Project.DoesNotExist):
                pass
        elif 'scene' in request.POST:
            from .models import Scene
            try:
                scene_id = int(request.POST['scene'])
                result['object_id'] = scene_id
                result['content_type'] = ContentType.objects.get_for_model(Scene)
                obj = Scene.objects.get(pk=scene_id)
                result['object_repr'] = str(obj)
            except (ValueError, Scene.DoesNotExist):
                pass
    
    return result


def get_action_detail(request):
    """
    從請求中提取操作詳情
    
    Returns:
        dict: 包含請求參數和變更內容的字典
    """
    detail = {}
    
    # GET 參數
    if request.GET:
        detail['query_params'] = dict(request.GET)
    
    # POST 數據（排除敏感資訊）
    if request.method in ['POST', 'PUT', 'PATCH'] and request.POST:
        post_data = dict(request.POST)
        # 排除密碼、CSRF token 等敏感資訊
        excluded_keys = ['password', 'csrfmiddlewaretoken', 'password1', 'password2']
        filtered_data = {k: v for k, v in post_data.items() if k not in excluded_keys}
        detail['post_data'] = filtered_data
    
    # FILES 資訊（只記錄檔案名稱和大小，不記錄內容）
    if request.FILES:
        files_info = {}
        for key, file_obj in request.FILES.items():
            if hasattr(file_obj, 'name') and hasattr(file_obj, 'size'):
                files_info[key] = {
                    'name': file_obj.name,
                    'size': file_obj.size,
                }
            elif isinstance(file_obj, list):
                # 批量上傳的情況
                files_info[key] = [
                    {'name': f.name, 'size': f.size}
                    for f in file_obj if hasattr(f, 'name') and hasattr(f, 'size')
                ]
        detail['files'] = files_info
    
    # JSON 數據（用於 API 請求）
    if request.content_type == 'application/json':
        try:
            if hasattr(request, 'body') and request.body:
                json_data = json.loads(request.body)
                detail['json_data'] = json_data
        except (json.JSONDecodeError, AttributeError):
            pass
    
    return detail


def should_log_action(request):
    """
    判斷是否應該記錄此操作
    
    排除靜態文件、media 文件、健康檢查等不需要記錄的請求
    
    Returns:
        bool: True 表示應該記錄，False 表示不記錄
    """
    path = request.path.lower()
    
    # 排除靜態文件和 media 文件
    if path.startswith('/static/') or path.startswith('/media/'):
        return False
    
    # 排除 admin 靜態文件
    if path.startswith('/admin/jsi18n/'):
        return False
    
    # 排除健康檢查
    if path in ['/health/', '/ping/', '/status/']:
        return False
    
    # 排除 favicon
    if 'favicon.ico' in path:
        return False
    
    # 只記錄 site360 app 的操作
    if not path.startswith('/site360/'):
        return False
    
    # 排除 API 端點（根據實際情況調整）
    excluded_paths = [
        '/site360/api/cities/',  # 城市列表 API
        '/site360/api/districts/',  # 區域列表 API
    ]
    
    if path in excluded_paths:
        return False
    
    # 只記錄特定的方法
    # GET 請求只記錄重要的查看操作
    if request.method == 'GET':
        # 只記錄特定的 GET 請求
        important_views = ['/tour/', '/detail/', '/map/', '/resources/']
        if not any(view in path for view in important_views):
            return False
    
    return True


def create_action_log(user, action_type, request, content_type=None, object_id=None, object_repr=''):
    """
    創建操作記錄的便捷函數
    
    Args:
        user: User object or None
        action_type: str, 操作類型
        request: Django request object
        content_type: ContentType object or None
        object_id: int or None
        object_repr: str, 對象的字串表示
        
    Returns:
        UserActionLog object
    """
    from .models import UserActionLog
    
    log = UserActionLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action_type=action_type,
        content_type=content_type,
        object_id=object_id,
        object_repr=object_repr,
        action_detail=get_action_detail(request),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        request_path=request.path,
        request_method=request.method,
        session_key=request.session.session_key if hasattr(request, 'session') else '',
    )
    
    return log
