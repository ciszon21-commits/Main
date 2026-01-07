from django.db import models
from django.contrib.auth.models import User
from django_ckeditor_5.fields import CKEditor5Field


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
