from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SiteConfig(models.Model):
    """全域設定（單例模型）"""
    endorsement_threshold = models.PositiveIntegerField(
        default=50, verbose_name="附議成案門檻"
    )
    package_choices = models.JSONField(
        default=list, blank=True, verbose_name="研發專案套件清單",
        help_text='["套件A","套件B"]'
    )
    group_choices = models.JSONField(
        default=list, blank=True, verbose_name="指定組別清單",
        help_text='[{"value":"engineering","label":"工程組"}]'
    )
    manager_emails = models.JSONField(
        default=list, blank=True, verbose_name="主管信箱名單",
        help_text='["email@example.com"]'
    )
    board_admins = models.JSONField(
        default=dict, blank=True, verbose_name="各版板主",
        help_text='{"petition":[1,2],"rnd":[3]}'
    )

    class Meta:
        verbose_name = "系統設定"
        verbose_name_plural = "系統設定"

    def __str__(self):
        return "系統設定"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Post(models.Model):
    """統一貼文模型 — 研發專案 / 跳蚤市場 / 七嘴八舌"""

    TYPE_CHOICES = [
        ('rnd', '研發專案'),
        ('market', '跳蚤市場'),
        ('gossip', '七嘴八舌'),
    ]

    CATEGORY_CHOICES = [
        ('bug', 'Bug報修'),
        ('feature', '功能建議'),
        ('announcement', '最新公告'),
    ]

    STATUS_RND_CHOICES = [
        ('pending', '待確認'),
        ('scheduled', '已排定'),
        ('in_progress', '處理中'),
        ('done', '已完成'),
    ]

    STATUS_MARKET_CHOICES = [
        ('on_sale', '出售中'),
        ('negotiating', '洽談中'),
        ('sold', '已售出'),
    ]



    # 基本欄位
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="類型")
    title = models.CharField(max_length=200, blank=True, verbose_name="標題")
    content = models.TextField(verbose_name="內容")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_posts', verbose_name="作者"
    )
    is_anonymous = models.BooleanField(default=False, verbose_name="匿名發布")
    display_name = models.CharField(
        max_length=50, blank=True, verbose_name="顯示名稱",
        help_text="留空則顯示預設的匿名，填入則以此名稱顯示"
    )

    # 研發專案欄位
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES,
        blank=True, verbose_name="分類"
    )
    status = models.CharField(max_length=20, blank=True, verbose_name="狀態")

    package_name = models.CharField(max_length=100, blank=True, verbose_name="指定套件")
    problem_type = models.CharField(max_length=100, blank=True, verbose_name="問題類型")
    assigned_group = models.CharField(
        max_length=50, blank=True, verbose_name="指定組別"
    )

    # 官方回應（研發專案用）
    response_content = models.TextField(blank=True, verbose_name="回應內容")
    response_at = models.DateTimeField(null=True, blank=True, verbose_name="回應時間")
    response_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lhawish_post_responses', verbose_name="回應人"
    )

    # 跳蚤市場欄位
    price = models.IntegerField(null=True, blank=True, verbose_name="價格")
    price_label = models.CharField(max_length=50, blank=True, verbose_name="價格標籤")
    condition = models.CharField(
        max_length=100, blank=True, verbose_name="物品狀況"
    )
    image = models.ImageField(
        upload_to='lhawish/posts/%Y/%m/',
        null=True, blank=True, verbose_name="圖片"
    )
    images = models.JSONField(
        default=list, blank=True, verbose_name="多張圖片",
        help_text="存放 base64 或圖片路徑清單"
    )



    # 時間戳記
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "貼文"
        verbose_name_plural = "貼文"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_type_display()}] {self.title or self.content[:30]}"

    @property
    def like_count(self):
        return self.interactions.filter(liked=True).count()

    @property
    def save_count(self):
        return self.interactions.filter(saved=True).count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def status_display(self):
        """根據 type 返回對應的狀態顯示文字"""
        if self.type == 'rnd':
            return dict(self.STATUS_RND_CHOICES).get(self.status, self.status)
        elif self.type == 'market':
            return dict(self.STATUS_MARKET_CHOICES).get(self.status, self.status)
        return self.status

    @property
    def status_css_class(self):
        """狀態對應的 CSS class"""
        css_map = {
            'pending': 'badge-pending',
            'scheduled': 'badge-scheduled',
            'in_progress': 'badge-progress',
            'done': 'badge-done',
            'on_sale': 'badge-sale',
            'negotiating': 'badge-negotiating',
            'sold': 'badge-sold',
        }
        return css_map.get(self.status, '')

    @property
    def condition_display(self):
        return self.condition or ''

    @property
    def price_display(self):
        if self.price is None:
            return self.price_label or '面議'
        if self.price == 0:
            return '免費贈送'
        label = f'${self.price:,}'
        if self.price_label:
            label += f' ({self.price_label})'
        return label
class Comment(models.Model):
    """留言模型"""
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='comments', verbose_name="貼文"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_comments', verbose_name="作者"
    )
    content = models.TextField(verbose_name="內容")
    is_official = models.BooleanField(default=False, verbose_name="官方回覆")
    is_anonymous = models.BooleanField(default=False, verbose_name="匿名留言")
    is_edited = models.BooleanField(default=False, verbose_name="已編輯")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "留言"
        verbose_name_plural = "留言"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author} 留言於 {self.post}"

    @property
    def like_count(self):
        return self.comment_likes.count()

    @property
    def display_author(self):
        if self.is_anonymous:
            return "匿名"
        return self.author.get_full_name() or self.author.username


class PostInteraction(models.Model):
    """貼文互動（按讚/收藏）"""
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name='interactions', verbose_name="貼文"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_interactions', verbose_name="使用者"
    )
    liked = models.BooleanField(default=False, verbose_name="已按讚")
    saved = models.BooleanField(default=False, verbose_name="已收藏")

    class Meta:
        verbose_name = "貼文互動"
        verbose_name_plural = "貼文互動"
        unique_together = ['post', 'user']

    def __str__(self):
        return f"{self.user} ↔ {self.post}"


# ========== 園路願望 ==========

class Petition(models.Model):
    """園路願望 — 提議模型"""

    GROUP_CHOICES = [
        ('engineering', '工程組'),
        ('urban_planning', '國土城規組'),
        ('sustainability', '國土永續中心'),
        ('other', '其他組'),
        ('management', '部門主管/副主管'),
    ]

    STATUS_CHOICES = [
        ('endorsing', '附議中'),
        ('established', '已成案'),
        ('withdrawn', '已撤案'),
        ('responded', '已回應'),
        ('hidden', '已隱藏'),
    ]

    title = models.CharField(max_length=200, verbose_name="提議標題")
    content = models.TextField(verbose_name="提議內容")
    proposer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_petitions', verbose_name="提議人"
    )
    # 匿名或自訂顯示名稱
    is_anonymous = models.BooleanField(default=False, verbose_name="匿名提議")
    display_name = models.CharField(
        max_length=50, blank=True, verbose_name="顯示名稱",
        help_text="留空則顯示真實姓名，填入則以此名稱顯示"
    )

    assigned_group = models.CharField(
        max_length=50, blank=True, verbose_name="指定執行組別"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='endorsing', verbose_name="狀態"
    )

    # 附議門檻
    endorsement_threshold = models.PositiveIntegerField(
        default=50, verbose_name="附議門檻",
        help_text="達到此數量即自動成案"
    )

    # 是否有修改
    is_edited = models.BooleanField(default=False, verbose_name="已修改內文")

    # 撤案
    withdraw_reason = models.TextField(blank=True, verbose_name="撤案理由")

    # 成案回應
    response_content = models.TextField(blank=True, verbose_name="回應內容")
    response_at = models.DateTimeField(null=True, blank=True, verbose_name="回應時間")
    response_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lhawish_responses', verbose_name="回應人"
    )
    deadline = models.DateTimeField(
        null=True, blank=True, verbose_name="回應期限",
        help_text="成案後自動設為 +2 個月"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    class Meta:
        verbose_name = "園路願望提議"
        verbose_name_plural = "園路願望提議"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_status_display()}] {self.title}"

    @property
    def endorsement_count(self):
        return self.endorsements.count()

    @property
    def endorsement_percent(self):
        if self.endorsement_threshold <= 0:
            return 100
        return min(100, int(self.endorsement_count / self.endorsement_threshold * 100))

    @property
    def comment_count(self):
        return self.petition_comments.count()

    @property
    def proposer_display(self):
        """顯示提議人名稱"""
        if self.is_anonymous:
            return "匿名"
        if self.display_name:
            return self.display_name
        return self.proposer.get_full_name() or self.proposer.username

    @property
    def is_overdue(self):
        """是否已逾期未回應"""
        if self.status == 'established' and self.deadline:
            return timezone.now() > self.deadline
        return False

    @property
    def days_remaining(self):
        """回應剩餘天數"""
        if self.deadline and self.status == 'established':
            delta = self.deadline - timezone.now()
            return max(0, delta.days)
        return None

    @property
    def title_display(self):
        """標題（含修改標記）"""
        if self.is_edited:
            return f"{self.title}（有修改）"
        return self.title


class Endorsement(models.Model):
    """園路願望 — 附議"""
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE,
        related_name='endorsements', verbose_name="提議"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_endorsements', verbose_name="附議人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="附議時間")

    class Meta:
        verbose_name = "附議"
        verbose_name_plural = "附議"
        unique_together = ['petition', 'user']

    def __str__(self):
        return f"{self.user} 附議 {self.petition.title}"


class PetitionComment(models.Model):
    """園路願望 — 留言"""
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE,
        related_name='petition_comments', verbose_name="提議"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_petition_comments', verbose_name="作者"
    )
    content = models.TextField(verbose_name="內容")
    is_anonymous = models.BooleanField(default=False, verbose_name="匿名留言")
    is_official = models.BooleanField(default=False, verbose_name="管理者留言")
    is_edited = models.BooleanField(default=False, verbose_name="已編輯")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    class Meta:
        verbose_name = "提議留言"
        verbose_name_plural = "提議留言"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author} 留言於 {self.petition.title}"

    @property
    def like_count(self):
        return self.comment_likes.count()

    @property
    def display_author(self):
        if self.is_anonymous:
            return "匿名"
        return self.author.get_full_name() or self.author.username


class PetitionSave(models.Model):
    """園路願望 — 收藏"""
    petition = models.ForeignKey(
        Petition, on_delete=models.CASCADE,
        related_name='saves', verbose_name="提議"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_petition_saves', verbose_name="使用者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏時間")

    class Meta:
        verbose_name = "提議收藏"
        verbose_name_plural = "提議收藏"
        unique_together = ['petition', 'user']

    def __str__(self):
        return f"{self.user} 收藏 {self.petition.title}"


class CommentLike(models.Model):
    """留言按讚（通用 — 涵蓋 Post 留言和 Petition 留言）"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='lhawish_comment_likes', verbose_name="使用者"
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, null=True, blank=True,
        related_name='comment_likes', verbose_name="貼文留言"
    )
    petition_comment = models.ForeignKey(
        PetitionComment, on_delete=models.CASCADE, null=True, blank=True,
        related_name='comment_likes', verbose_name="提議留言"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="按讚時間")

    class Meta:
        verbose_name = "留言按讚"
        verbose_name_plural = "留言按讚"

    def __str__(self):
        target = self.comment or self.petition_comment
        return f"{self.user} 讚 {target}"
