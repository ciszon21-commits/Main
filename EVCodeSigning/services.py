"""
EVCodeSigning Services - 郵件通知服務
"""
import logging
import re
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import SigningAdmin

logger = logging.getLogger(__name__)


def is_valid_email(email):
    """檢查是否為有效的電子郵件地址"""
    if not email:
        return False
    # 簡單的 email 格式驗證
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_system_email():
    """取得系統發信地址"""
    email = getattr(settings, 'SYSTEM_EMAIL', None) or \
            getattr(settings, 'DEFAULT_FROM_EMAIL', None) or \
            getattr(settings, 'NOTIFY_EMAIL', None)
    
    # 驗證 email 格式
    if email and is_valid_email(email):
        return email
    
    # 使用預設值
    return 'noreply@example.com'


def notify_admins_new_request(request_obj, request=None):
    """
    通知所有活躍的簽章管理員有新的簽章申請
    
    Args:
        request_obj: SigningRequest 物件
        request: Django HttpRequest 物件（用於建立完整 URL）
    """
    # 取得所有活躍的管理員
    admins = SigningAdmin.objects.filter(is_active=True).select_related('user')
    
    if not admins.exists():
        logger.warning("沒有活躍的簽章管理員，無法發送通知")
        return
    
    # 建立詳情頁 URL
    detail_url = ""
    if request:
        try:
            detail_path = reverse('evcodesigning:request_detail', kwargs={'pk': request_obj.pk})
            detail_url = request.build_absolute_uri(detail_path)
        except Exception:
            pass
    
    applicant_name = request_obj.applicant.get_full_name() or request_obj.applicant.username
    
    subject = f'[EV Code Signing] 新簽章申請：{request_obj.title}'
    message = f'''您好，

有一筆新的 EV Code Signing 簽章申請需要處理：

申請標題：{request_obj.title}
申請人：{applicant_name}
申請時間：{request_obj.created_at.strftime('%Y-%m-%d %H:%M')}
檔案數量：{request_obj.file_count} 個

申請說明：
{request_obj.description}

{f'請點擊以下連結查看詳情：{detail_url}' if detail_url else '請登入系統查看詳情。'}

---
此為系統自動發送的通知信件，請勿直接回覆。
'''
    
    # 收集管理員郵件地址（只收集有效的 email）
    recipient_list = [
        admin.user.email 
        for admin in admins 
        if admin.user.email and is_valid_email(admin.user.email)
    ]
    
    if not recipient_list:
        logger.warning("所有簽章管理員都沒有設定郵件地址")
        return
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=get_system_email(),
            recipient_list=recipient_list,
            fail_silently=False,
        )
        logger.info(f"已發送新申請通知給 {len(recipient_list)} 位管理員")
    except Exception as e:
        logger.error(f"發送新申請通知失敗: {e}")


def notify_applicant_completed(request_obj, request=None):
    """
    通知申請人簽章已完成
    
    Args:
        request_obj: SigningRequest 物件
        request: Django HttpRequest 物件
    """
    if not request_obj.applicant.email or not is_valid_email(request_obj.applicant.email):
        logger.warning(f"申請人 {request_obj.applicant} 沒有設定有效的郵件地址")
        return
    
    # 建立詳情頁 URL
    detail_url = ""
    if request:
        try:
            detail_path = reverse('evcodesigning:request_detail', kwargs={'pk': request_obj.pk})
            detail_url = request.build_absolute_uri(detail_path)
        except Exception:
            pass
    
    applicant_name = request_obj.applicant.get_full_name() or request_obj.applicant.username
    admin_name = ""
    if request_obj.assigned_admin:
        admin_name = request_obj.assigned_admin.user.get_full_name() or \
                     request_obj.assigned_admin.user.username
    
    subject = f'[EV Code Signing] 簽章完成：{request_obj.title}'
    message = f'''您好，{applicant_name}，

您的 EV Code Signing 簽章申請已完成處理：

申請標題：{request_obj.title}
處理人員：{admin_name}
完成時間：{request_obj.completed_at.strftime('%Y-%m-%d %H:%M') if request_obj.completed_at else ''}
檔案數量：{request_obj.file_count} 個

{f'請點擊以下連結下載簽章後的檔案：{detail_url}' if detail_url else '請登入系統下載簽章後的檔案。'}

---
此為系統自動發送的通知信件，請勿直接回覆。
'''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=get_system_email(),
            recipient_list=[request_obj.applicant.email],
            fail_silently=False,
        )
        logger.info(f"已發送完成通知給申請人 {request_obj.applicant}")
    except Exception as e:
        logger.error(f"發送完成通知失敗: {e}")


def notify_applicant_rejected(request_obj, request=None):
    """
    通知申請人申請已被退回
    
    Args:
        request_obj: SigningRequest 物件
        request: Django HttpRequest 物件
    """
    if not request_obj.applicant.email or not is_valid_email(request_obj.applicant.email):
        logger.warning(f"申請人 {request_obj.applicant} 沒有設定有效的郵件地址")
        return
    
    # 建立詳情頁 URL
    detail_url = ""
    if request:
        try:
            detail_path = reverse('evcodesigning:request_detail', kwargs={'pk': request_obj.pk})
            detail_url = request.build_absolute_uri(detail_path)
        except Exception:
            pass
    
    applicant_name = request_obj.applicant.get_full_name() or request_obj.applicant.username
    admin_name = ""
    if request_obj.assigned_admin:
        admin_name = request_obj.assigned_admin.user.get_full_name() or \
                     request_obj.assigned_admin.user.username
    
    subject = f'[EV Code Signing] 申請已退回：{request_obj.title}'
    message = f'''您好，{applicant_name}，

很抱歉，您的 EV Code Signing 簽章申請已被退回：

申請標題：{request_obj.title}
處理人員：{admin_name}

退回原因：
{request_obj.reject_reason}

如有疑問，請聯繫簽章管理員或修改後重新提交申請。

{f'申請詳情：{detail_url}' if detail_url else ''}

---
此為系統自動發送的通知信件，請勿直接回覆。
'''
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=get_system_email(),
            recipient_list=[request_obj.applicant.email],
            fail_silently=False,
        )
        logger.info(f"已發送退回通知給申請人 {request_obj.applicant}")
    except Exception as e:
        logger.error(f"發送退回通知失敗: {e}")
