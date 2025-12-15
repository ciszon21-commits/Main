from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_question_notification(question):
    """
    當有新問題時，發送郵件通知所有教材維護者
    
    Args:
        question: Question 物件
    """
    tutorial = question.step.tutorial
    maintainers = tutorial.maintainers.all()
    
    # 獲取所有維護者的郵件地址
    recipient_emails = []
    for maintainer in maintainers:
        if maintainer.user.email:
            recipient_emails.append(maintainer.user.email)
    
    if not recipient_emails:
        return  # 沒有郵件地址，直接返回
    
    # 準備郵件內容
    subject = f'[TutorialHub] 新問題：{tutorial.title}'
    
    context = {
        'question': question,
        'tutorial': tutorial,
        'step': question.step,
        'asker': question.user,
    }
    
    # 使用模板渲染 HTML 郵件（如果有的話）
    # html_message = render_to_string('tutorialhub/emails/question_notification.html', context)
    # plain_message = strip_tags(html_message)
    
    # 暫時使用純文字郵件
    plain_message = f"""
您好，

在教材「{tutorial.title}」的步驟「{question.step.title}」中有新問題：

提問者：{question.user.get_full_name() or question.user.username}
問題內容：
{question.content}

請登入系統查看並回答：
{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}{tutorial.get_absolute_url()}

---
TutorialHub 自動通知
"""
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.SYSTEM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )
    except Exception as e:
        # 記錄錯誤但不中斷流程
        print(f"郵件發送失敗: {e}")


def send_answer_notification(answer):
    """
    當有新回答時，發送郵件通知提問者
    
    Args:
        answer: Answer 物件
    """
    question = answer.question
    asker = question.user
    
    if not asker.email:
        return  # 沒有郵件地址，直接返回
    
    tutorial = question.step.tutorial
    
    # 準備郵件內容
    subject = f'[TutorialHub] 您的問題有新回答：{tutorial.title}'
    
    context = {
        'answer': answer,
        'question': question,
        'tutorial': tutorial,
        'step': question.step,
        'answerer': answer.user,
    }
    
    # 暫時使用純文字郵件
    plain_message = f"""
您好 {asker.get_full_name() or asker.username}，

您在教材「{tutorial.title}」的步驟「{question.step.title}」中的問題有新回答：

回答者：{answer.user.get_full_name() or answer.user.username}{'（維護者）' if answer.is_from_maintainer else ''}
回答內容：
{answer.content}

請登入系統查看：
{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}{tutorial.get_absolute_url()}

您的問題：
{question.content}

---
TutorialHub 自動通知
"""
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.SYSTEM_EMAIL,
            recipient_list=[asker.email],
            fail_silently=False,
        )
    except Exception as e:
        # 記錄錯誤但不中斷流程
        print(f"郵件發送失敗: {e}")
