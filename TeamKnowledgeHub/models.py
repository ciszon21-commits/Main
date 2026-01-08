from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field
from SinoFile.fields import SinoFileField


class KnowledgeTeam(models.Model):
    """知識團隊模型"""
    name = models.CharField(max_length=200, verbose_name="團隊名稱")
    description = models.TextField(blank=True, verbose_name="團隊說明")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_knowledge_teams',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "知識團隊"
        verbose_name_plural = "知識團隊"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_member(self, user):
        """檢查使用者是否為團隊成員"""
        return self.members.filter(user=user).exists()

    def is_creator(self, user):
        """檢查使用者是否為團隊建立者"""
        return self.created_by == user

    def get_member_count(self):
        """取得成員數量"""
        return self.members.count()


class KnowledgeTeamMember(models.Model):
    """團隊成員模型"""
    ROLE_CHOICES = [
        ('creator', '建立者'),
        ('member', '成員'),
    ]

    team = models.ForeignKey(
        KnowledgeTeam,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name="團隊"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='knowledge_team_memberships',
        verbose_name="使用者"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name="角色"
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="加入時間")

    class Meta:
        verbose_name = "團隊成員"
        verbose_name_plural = "團隊成員"
        unique_together = ['team', 'user']
        ordering = ['role', 'joined_at']

    def __str__(self):
        return f"{self.team.name} - {self.user.get_full_name() or self.user.username}"


class Topic(models.Model):
    """主題模型"""
    team = models.ForeignKey(
        KnowledgeTeam,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name="所屬團隊"
    )
    name = models.CharField(max_length=200, verbose_name="主題名稱")
    description = models.TextField(blank=True, verbose_name="主題說明")
    order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "主題"
        verbose_name_plural = "主題"
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.team.name} - {self.name}"

    def get_item_count(self):
        """取得項目數量"""
        return self.items.count()

    def get_uncategorized_items(self):
        """取得未分類的項目"""
        return self.items.filter(category__isnull=True)


class Category(models.Model):
    """分類模型 - 位於主題與項目之間"""
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="所屬主題"
    )
    name = models.CharField(max_length=200, verbose_name="分類名稱")
    order = models.IntegerField(default=0, verbose_name="排序")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "分類"
        verbose_name_plural = "分類"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.topic.name} - {self.name}"

    def get_item_count(self):
        """取得項目數量"""
        return self.items.count()


class KnowledgeItem(models.Model):
    """知識項目模型"""
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="所屬主題"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        verbose_name="所屬分類"
    )
    title = models.CharField(max_length=300, verbose_name="標題")
    content = CKEditor5Field(
        verbose_name="內容",
        config_name='extends',
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_knowledge_items',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "知識項目"
        verbose_name_plural = "知識項目"
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def get_comment_count(self):
        """取得留言數量"""
        return self.comments.count()


class ItemComment(models.Model):
    """項目留言模型"""
    item = models.ForeignKey(
        KnowledgeItem,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="所屬項目"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='knowledge_comments',
        verbose_name="作者"
    )
    content = models.TextField(verbose_name="留言內容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username} - {self.content[:30]}"


# ===== Attachment Models =====

def item_attachment_path(instance, filename):
    """項目附件上傳路徑"""
    return f'knowledge/items/{instance.item.pk}/{filename}'


def comment_attachment_path(instance, filename):
    """留言附件上傳路徑"""
    return f'knowledge/comments/{instance.comment.pk}/{filename}'


class ActiveAttachmentManager(models.Manager):
    """只返回未刪除附件的 Manager"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class ItemAttachment(models.Model):
    """知識項目附件"""
    item = models.ForeignKey(
        KnowledgeItem,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="所屬項目"
    )
    file = SinoFileField(
        upload_to=item_attachment_path,
        verbose_name="檔案"
    )
    filename = models.CharField(max_length=255, verbose_name="原始檔名")
    file_size = models.PositiveIntegerField(default=0, verbose_name="檔案大小(bytes)")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_item_attachments',
        verbose_name="上傳者"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")
    is_deleted = models.BooleanField(default=False, verbose_name="已刪除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="刪除時間")
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_item_attachments',
        verbose_name="刪除者"
    )

    objects = models.Manager()  # Default manager
    active = ActiveAttachmentManager()  # Only non-deleted

    class Meta:
        verbose_name = "項目附件"
        verbose_name_plural = "項目附件"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.item.title} - {self.filename}"

    def get_file_extension(self):
        """取得檔案副檔名"""
        import os
        _, ext = os.path.splitext(self.filename)
        return ext.lower().lstrip('.')

    def get_file_icon(self):
        """根據檔案類型返回圖示"""
        ext = self.get_file_extension()
        icons = {
            'pdf': '📄',
            'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊',
            'ppt': '📽️', 'pptx': '📽️',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️',
            'zip': '📦', 'rar': '📦', '7z': '📦',
            'txt': '📃',
        }
        return icons.get(ext, '📎')

    def get_human_size(self):
        """返回人類可讀的檔案大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class CommentAttachment(models.Model):
    """留言附件"""
    comment = models.ForeignKey(
        ItemComment,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name="所屬留言"
    )
    file = SinoFileField(
        upload_to=comment_attachment_path,
        verbose_name="檔案"
    )
    filename = models.CharField(max_length=255, verbose_name="原始檔名")
    file_size = models.PositiveIntegerField(default=0, verbose_name="檔案大小(bytes)")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_comment_attachments',
        verbose_name="上傳者"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")
    is_deleted = models.BooleanField(default=False, verbose_name="已刪除")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="刪除時間")
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_comment_attachments',
        verbose_name="刪除者"
    )

    objects = models.Manager()
    active = ActiveAttachmentManager()

    class Meta:
        verbose_name = "留言附件"
        verbose_name_plural = "留言附件"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Comment #{self.comment.pk} - {self.filename}"

    def get_file_extension(self):
        import os
        _, ext = os.path.splitext(self.filename)
        return ext.lower().lstrip('.')

    def get_file_icon(self):
        ext = self.get_file_extension()
        icons = {
            'pdf': '📄',
            'doc': '📝', 'docx': '📝',
            'xls': '📊', 'xlsx': '📊',
            'ppt': '📽️', 'pptx': '📽️',
            'png': '🖼️', 'jpg': '🖼️', 'jpeg': '🖼️', 'gif': '🖼️',
            'zip': '📦', 'rar': '📦', '7z': '📦',
            'txt': '📃',
        }
        return icons.get(ext, '📎')

    def get_human_size(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# ===== Quick Note Model =====

class QuickNote(models.Model):
    """個人快速筆記模型 - 用於快速記錄，後續可移入團隊"""
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quick_notes',
        verbose_name="擁有者"
    )
    title = models.CharField(max_length=300, verbose_name="標題")
    content = CKEditor5Field(
        verbose_name="內容",
        config_name='extends',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    is_archived = models.BooleanField(default=False, verbose_name="已歸檔")

    class Meta:
        verbose_name = "快速筆記"
        verbose_name_plural = "快速筆記"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.owner.username} - {self.title}"
