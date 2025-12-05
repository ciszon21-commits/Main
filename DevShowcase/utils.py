from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_comment_notification(achievement, comment):
    """
    當有新留言時，發送郵件通知所有開發者
    """
    developers = achievement.get_all_developers()
    developer_emails = [dev.email for dev in developers if dev.email]
    
    if not developer_emails:
        return
    
    subject = f'[開發成果] {achievement.name} 有新留言'
    
    message = f"""
您好，

您參與開發的成果「{achievement.name}」有新的留言：

留言者：{comment.user.get_full_name() or comment.user.username}
留言時間：{comment.created_at.strftime('%Y-%m-%d %H:%M')}
留言內容：
{comment.content}

請前往查看：{settings.SITE_URL if hasattr(settings, 'SITE_URL') else ''}/showcase/achievement/{achievement.id}/

此為系統自動發送的郵件，請勿直接回覆。
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else settings.EMAIL_HOST_USER,
            recipient_list=developer_emails,
            fail_silently=False,
        )
    except Exception as e:
        print(f"郵件發送失敗: {e}")


def validate_video_duration(video_file, max_duration=600):
    """
    驗證影片時長（可選功能，需要安裝 moviepy）
    max_duration: 最大時長（秒），預設600秒（10分鐘）
    """
    try:
        from moviepy.editor import VideoFileClip
        
        clip = VideoFileClip(video_file.temporary_file_path())
        duration = clip.duration
        clip.close()
        
        if duration > max_duration:
            return False, f"影片時長 {int(duration/60)} 分 {int(duration%60)} 秒，超過限制的 {int(max_duration/60)} 分鐘"
        
        return True, None
    except ImportError:
        # 如果沒有安裝 moviepy，跳過時長檢查
        return True, None
    except Exception as e:
        # 其他錯誤，記錄但不阻止上傳
        print(f"影片驗證錯誤: {e}")
        return True, None
