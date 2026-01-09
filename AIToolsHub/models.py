from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field


class Category(models.Model):
    """分類模型 - 公司/部門工具、外部工具"""
    CATEGORY_CHOICES = [
        ('internal', '公司/部門工具'),
        ('external', '外部工具'),
    ]

    name = models.CharField(max_length=100, verbose_name="分類名稱")
    slug = models.CharField(
        max_length=50,
        unique=True,
        choices=CATEGORY_CHOICES,
        verbose_name="分類代碼"
    )
    description = models.TextField(blank=True, verbose_name="分類說明")
    order = models.IntegerField(default=0, verbose_name="排序", help_text="數字越小越靠前")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "分類"
        verbose_name_plural = "分類"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """標籤模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="標籤名稱")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "標籤"
        verbose_name_plural = "標籤"
        ordering = ['name']

    def __str__(self):
        return self.name


class AITool(models.Model):
    """AI 工具模型"""
    name = models.CharField(max_length=200, verbose_name="工具名稱")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='tools',
        verbose_name="分類"
    )
    image = models.ImageField(
        upload_to='aitools/images/%Y/%m/',
        verbose_name="圖片"
    )
    url = models.URLField(blank=True, verbose_name="網址")
    summary = models.TextField(blank=True, max_length=500, verbose_name="簡介")
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='tools',
        verbose_name="標籤"
    )
    extra_info = CKEditor5Field(
        verbose_name="其他說明",
        config_name='extends',
        blank=True
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_aitools',
        verbose_name="建立者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    # 統計欄位（用於排序優化）
    favorite_count = models.IntegerField(default=0, verbose_name="收藏數")
    like_count = models.IntegerField(default=0, verbose_name="點讚數")
    view_count = models.IntegerField(default=0, verbose_name="瀏覽數")

    class Meta:
        verbose_name = "AI 工具"
        verbose_name_plural = "AI 工具"
        ordering = ['-favorite_count', '-created_at']

    def __str__(self):
        return self.name




class ViewLog(models.Model):
    """瀏覽記錄模型"""
    tool = models.ForeignKey(
        AITool,
        on_delete=models.CASCADE,
        related_name='view_logs',
        verbose_name="工具"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='aitool_views',
        verbose_name="使用者"
    )
    viewed_at = models.DateTimeField(auto_now_add=True, verbose_name="瀏覽時間")

    class Meta:
        verbose_name = "瀏覽記錄"
        verbose_name_plural = "瀏覽記錄"
        unique_together = ['tool', 'user']
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.tool.name}"


class Favorite(models.Model):
    """收藏模型"""
    tool = models.ForeignKey(
        AITool,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="工具"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='aitool_favorites',
        verbose_name="使用者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏時間")

    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = "收藏"
        unique_together = ['tool', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} 收藏 {self.tool.name}"


class Like(models.Model):
    """點讚模型"""
    tool = models.ForeignKey(
        AITool,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name="工具"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='aitool_likes',
        verbose_name="使用者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="點讚時間")

    class Meta:
        verbose_name = "點讚"
        verbose_name_plural = "點讚"
        unique_together = ['tool', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} 點讚 {self.tool.name}"


class Comment(models.Model):
    """留言模型 - 支援回覆、匿名、編輯、軟刪除"""
    tool = models.ForeignKey(
        AITool,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="工具"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='aitool_comments',
        verbose_name="使用者"
    )
    content = models.TextField(verbose_name="留言內容")
    is_anonymous = models.BooleanField(default=False, verbose_name="匿名發表")
    is_deleted = models.BooleanField(default=False, verbose_name="已刪除")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="父留言"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="留言時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言"
        ordering = ['created_at']

    def __str__(self):
        if self.is_deleted:
            return f"[已刪除] - {self.tool.name}"
        display_name = "匿名" if self.is_anonymous else (self.user.get_full_name() or self.user.username)
        if self.parent:
            return f"回覆: {display_name} - {self.tool.name}"
        return f"留言: {display_name} - {self.tool.name}"

    def is_reply(self):
        """是否為回覆"""
        return self.parent is not None

    def get_display_name(self):
        """取得顯示名稱（考慮匿名和刪除）"""
        if self.is_deleted:
            return ""
        if self.is_anonymous:
            return "匿名"
        return self.user.get_full_name() or self.user.username

    def get_display_content(self):
        """取得顯示內容（考慮刪除）"""
        if self.is_deleted:
            return "此留言已被刪除"
        return self.content

    def can_edit(self, user):
        """是否可以編輯（僅發表者且未刪除）"""
        return user.is_authenticated and user == self.user and not self.is_deleted

    def can_delete(self, user):
        """是否可以刪除（僅發表者且未刪除）"""
        return user.is_authenticated and user == self.user and not self.is_deleted


class CommentReaction(models.Model):
    """留言反應模型 - Emoji 反應"""
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😄'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😡'),
    ]

    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name="留言"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_reactions',
        verbose_name="使用者"
    )
    reaction_type = models.CharField(
        max_length=20,
        choices=REACTION_CHOICES,
        verbose_name="反應類型"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="反應時間")

    class Meta:
        verbose_name = "留言反應"
        verbose_name_plural = "留言反應"
        unique_together = ['comment', 'user', 'reaction_type']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()} - {self.comment_id}"

