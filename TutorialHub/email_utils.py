from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def get_from_email():
    """獲取有效的發件人郵件地址"""
    # 優先使用 SYSTEM_EMAIL
    system_email = getattr(settings, 'SYSTEM_EMAIL', None)
    if system_email:
        try:
            validate_email(system_email)
            return system_email
        except ValidationError:
            pass
    
    # 備選使用 DEFAULT_FROM_EMAIL
    default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    if default_from:
        try:
            validate_email(default_from)
            return default_from
        except ValidationError:
            pass
    
    # 都無效則返回 None
    return None


def send_question_notification(question):
    """
    當有新問題時，發送郵件通知所有教材維護者
    
    Args:
        question: Question 物件
    """
    from_email = get_from_email()
    if not from_email:
        print("郵件發送跳過: 沒有設定有效的發件人郵件地址 (SYSTEM_EMAIL 或 DEFAULT_FROM_EMAIL)")
        return
    
    tutorial = question.step.tutorial
    maintainers = tutorial.maintainers.all()
    
    # 獲取所有維護者的郵件地址
    recipient_emails = []
    for maintainer in maintainers:
        if maintainer.user.email:
            try:
                validate_email(maintainer.user.email)
                recipient_emails.append(maintainer.user.email)
            except ValidationError:
                pass
    
    if not recipient_emails:
        print("郵件發送跳過: 沒有有效的收件人郵件地址")
        return
    
    # 準備郵件內容
    subject = f'[TutorialHub] 新問題：{tutorial.title}'
    
    context = {
        'question': question,
        'tutorial': tutorial,
        'step': question.step,
        'asker': question.user,
    }
    
    # 暫時使用純文字郵件
    plain_message = f"""
您好，

在教材「{tutorial.title}」的步驟「{question.step.title}」中有新問題：

提問者：{question.user.get_full_name() or question.user.username}
問題內容：
{question.content}

請登入系統查看並回答：
{getattr(settings, 'SITE_URL', '')}{tutorial.get_absolute_url()}

---
TutorialHub 自動通知
"""
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=recipient_emails,
            fail_silently=False,
        )
        print(f"郵件發送成功: 通知 {len(recipient_emails)} 位維護者")
    except Exception as e:
        # 記錄錯誤但不中斷流程
        print(f"郵件發送失敗: {e}")


def send_answer_notification(answer):
    """
    當有新回答時，發送郵件通知提問者
    
    Args:
        answer: Answer 物件
    """
    from_email = get_from_email()
    if not from_email:
        print("郵件發送跳過: 沒有設定有效的發件人郵件地址")
        return
    
    question = answer.question
    asker = question.user
    
    if not asker.email:
        print("郵件發送跳過: 提問者沒有郵件地址")
        return
    
    try:
        validate_email(asker.email)
    except ValidationError:
        print(f"郵件發送跳過: 提問者郵件地址無效 ({asker.email})")
        return
    
    tutorial = question.step.tutorial
    
    # 準備郵件內容
    subject = f'[TutorialHub] 您的問題有新回答：{tutorial.title}'
    
    # 純文字郵件
    plain_message = f"""
您好 {asker.get_full_name() or asker.username}，

您在教材「{tutorial.title}」的步驟「{question.step.title}」中的問題有新回答：

回答者：{answer.user.get_full_name() or answer.user.username}{'（維護者）' if answer.is_from_maintainer else ''}
回答內容：
{answer.content}

請登入系統查看：
{getattr(settings, 'SITE_URL', '')}{tutorial.get_absolute_url()}

您的問題：
{question.content}

---
TutorialHub 自動通知
"""
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[asker.email],
            fail_silently=False,
        )
        print(f"郵件發送成功: 已通知提問者 {asker.email}")
    except Exception as e:
        # 記錄錯誤但不中斷流程
        print(f"郵件發送失敗: {e}")
