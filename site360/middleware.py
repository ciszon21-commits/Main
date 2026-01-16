"""
Site360 使用者操作記錄中間件

自動記錄使用者在 site360 應用中的所有重要操作
"""
from django.utils.deprecation import MiddlewareMixin
from .models import UserActionLog
from .utils import (
    get_client_ip,
    get_user_agent,
    get_action_type_from_request,
    extract_object_info,
    get_action_detail,
    should_log_action
)


class UserActionLoggingMiddleware(MiddlewareMixin):
    """
    記錄使用者操作的中間件
    
    在每個請求處理完成後，自動創建操作記錄
    """
    
    def process_response(self, request, response):
        """
        在響應返回給客戶端之前記錄操作
        """
        # 判斷是否應該記錄此操作
        if not should_log_action(request):
            return response
        
        try:
            # 判斷操作類型
            action_type = get_action_type_from_request(request)
            
            # 如果操作類型為 None（例如一般的 GET 請求），則不記錄
            if not action_type:
                return response
            
            # 提取操作對象資訊
            obj_info = extract_object_info(request, response)
            
            # 提取操作詳情
            action_detail = get_action_detail(request)
            
            # 獲取用戶（如果已登入）
            user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
            
            # 創建操作記錄
            UserActionLog.objects.create(
                user=user,
                action_type=action_type,
                content_type=obj_info['content_type'],
                object_id=obj_info['object_id'],
                object_repr=obj_info['object_repr'],
                action_detail=action_detail,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                request_path=request.path,
                request_method=request.method,
                session_key=request.session.session_key if hasattr(request, 'session') and request.session.session_key else '',
            )
            
        except Exception as e:
            # 記錄失敗不應該影響正常的請求處理
            # 可以選擇記錄錯誤到日誌系統
            import logging
            logger = logging.getLogger('site360.logging')
            logger.error(f"Failed to log user action: {str(e)}")
        
        return response
