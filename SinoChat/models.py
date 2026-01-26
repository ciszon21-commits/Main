from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class ChatRoom(models.Model):
    """聊天室"""
    VISIBILITY_CHOICES = [
        ('public', '公開 - 所有人可加入'),
        ('private', '私人 - 僅邀請者可加入'),
    ]

    name = models.CharField(max_length=100, verbose_name='聊天室名稱')
    description = models.TextField(blank=True, null=True, verbose_name='描述')
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chatrooms',
        verbose_name='建立者'
    )
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='public',
        verbose_name='可見性'
    )
    avatar_color = models.CharField(
        max_length=7,
        default='#C41E3A',
        verbose_name='頭像顏色'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    is_active = models.BooleanField(default=True, verbose_name='是否啟用')

    class Meta:
        verbose_name = '聊天室'
        verbose_name_plural = '聊天室'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.filter(is_active=True).count()

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def can_user_access(self, user):
        """檢查用戶是否可以訪問此聊天室"""
        if user and user.is_superuser:
            return True
        if self.visibility == 'public':
            return True
        return self.creator == user or self.members.filter(user=user, is_active=True).exists()

    def can_user_view(self, user):
        """檢查用戶是否可以查看此聊天室"""
        if user and user.is_superuser:
            return True
        if self.visibility == 'public':
            return True
        return self.creator == user or self.members.filter(user=user, is_active=True).exists()


class ChatRoomMember(models.Model):
    """聊天室成員"""
    ROLE_CHOICES = [
        ('admin', '管理員'),
        ('member', '成員'),
    ]

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='聊天室'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_memberships',
        verbose_name='用戶'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name='角色'
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='加入時間')
    is_active = models.BooleanField(default=True, verbose_name='是否啟用')
    last_read_at = models.DateTimeField(default=timezone.now, verbose_name='最後讀取時間')

    class Meta:
        verbose_name = '聊天室成員'
        verbose_name_plural = '聊天室成員'
        unique_together = ['room', 'user']

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"

    @property
    def unread_count(self):
        return self.room.messages.filter(created_at__gt=self.last_read_at).exclude(sender=self.user).count()


class ChatMessage(models.Model):
    """聊天訊息"""
    MESSAGE_TYPE_CHOICES = [
        ('text', '文字'),
        ('image', '圖片'),
        ('file', '檔案'),
        ('system', '系統訊息'),
    ]

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='聊天室'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        verbose_name='發送者',
        null=True,
        blank=True
    )
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        verbose_name='訊息類型'
    )
    content = models.TextField(verbose_name='內容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='發送時間')
    is_deleted = models.BooleanField(default=False, verbose_name='是否刪除')

    class Meta:
        verbose_name = '聊天訊息'
        verbose_name_plural = '聊天訊息'
        ordering = ['created_at']

    def __str__(self):
        sender_name = self.sender.username if self.sender else '系統'
        return f"{sender_name}: {self.content[:30]}"


class ChatFile(models.Model):
    """聊天檔案附件"""
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='訊息'
    )
    file = models.FileField(upload_to='chat_files/%Y/%m/', verbose_name='檔案')
    original_name = models.CharField(max_length=255, verbose_name='原始檔名')
    file_size = models.PositiveIntegerField(default=0, verbose_name='檔案大小')
    file_type = models.CharField(max_length=50, blank=True, verbose_name='檔案類型')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上傳時間')

    class Meta:
        verbose_name = '聊天檔案'
        verbose_name_plural = '聊天檔案'

    def __str__(self):
        return self.original_name

    @property
    def file_size_display(self):
        """返回可讀的檔案大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def is_image(self):
        """判斷是否為圖片"""
        image_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        return self.file_type in image_types


class ChatFileDownloadLog(models.Model):
    file = models.ForeignKey(
        ChatFile,
        on_delete=models.CASCADE,
        related_name='download_logs',
        verbose_name='檔案'
    )
    downloaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_file_downloads',
        verbose_name='下載者'
    )
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name='下載時間')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, null=True, verbose_name='User Agent')

    class Meta:
        verbose_name = '檔案下載記錄'
        verbose_name_plural = '檔案下載記錄'
        ordering = ['-downloaded_at']

    def __str__(self):
        user_name = self.downloaded_by.get_full_name() if self.downloaded_by else '未知'
        return f"{user_name} - {self.file.original_name}"
