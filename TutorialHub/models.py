from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator


class Tutorial(models.Model):
    """教材模型"""
    title = models.CharField(max_length=200, verbose_name='教材標題')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL標識符')
    description = models.TextField(verbose_name='教材簡介')
    cover_image = models.ImageField(
        upload_to='tutorials/covers/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='封面圖片'
    )
    is_published = models.BooleanField(default=False, verbose_name='是否發布')
    view_count = models.PositiveIntegerField(default=0, verbose_name='瀏覽次數')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '教材'
        verbose_name_plural = '教材'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tutorialhub:tutorial_detail', kwargs={'slug': self.slug})

    @property
    def step_count(self):
        """步驟數量"""
        return self.steps.count()

    @property
    def image_count(self):
        """圖片數量"""
        return StepSnippet.objects.filter(
            step__tutorial=self,
            snippet_type='image'
        ).count()

    @property
    def code_count(self):
        """程式碼片段數量"""
        return StepSnippet.objects.filter(
            step__tutorial=self,
            snippet_type='code'
        ).count()

    @property
    def total_reading_time(self):
        """總閱讀時間（秒）"""
        total = self.reading_logs.aggregate(
            total=models.Sum('total_seconds')
        )['total']
        return total or 0

    @property
    def unique_readers(self):
        """獨特讀者數"""
        return self.reading_logs.count()


class TutorialMaintainer(models.Model):
    """教材維護者關聯模型"""
    ROLE_CHOICES = [
        ('creator', '創建者'),
        ('maintainer', '維護者'),
    ]

    tutorial = models.ForeignKey(
        Tutorial,
        on_delete=models.CASCADE,
        related_name='maintainers',
        verbose_name='教材'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutorial_contributions',
        verbose_name='使用者'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='maintainer',
        verbose_name='角色'
    )
    contribution_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='貢獻度分數',
        help_text='用於排序貢獻者'
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='加入時間')

    class Meta:
        verbose_name = '教材維護者'
        verbose_name_plural = '教材維護者'
        unique_together = [['tutorial', 'user']]
        ordering = ['-contribution_score', 'joined_at']

    def __str__(self):
        return f'{self.user.username} - {self.tutorial.title} ({self.get_role_display()})'


class TutorialStep(models.Model):
    """教材步驟模型"""
    tutorial = models.ForeignKey(
        Tutorial,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='教材'
    )
    title = models.CharField(max_length=200, verbose_name='步驟標題')
    order = models.PositiveIntegerField(default=0, verbose_name='排序順序')
    is_expanded_default = models.BooleanField(
        default=False,
        verbose_name='預設展開',
        help_text='預設是否展開此步驟'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '教材步驟'
        verbose_name_plural = '教材步驟'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.tutorial.title} - {self.title}'


class StepSnippet(models.Model):
    """步驟片段模型（文字/圖片/程式碼）"""
    SNIPPET_TYPE_CHOICES = [
        ('text', '文字'),
        ('image', '圖片'),
        ('code', '程式碼'),
    ]

    LANGUAGE_CHOICES = [
        ('plaintext', '純文字'),
        ('bash', 'Command Line / Bash'),
        ('python', 'Python'),
        ('csharp', 'C#'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('javascript', 'JavaScript'),
        ('sql', 'SQL'),
        ('java', 'Java'),
        ('cpp', 'C++'),
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('yaml', 'YAML'),
        ('markdown', 'Markdown'),
    ]

    step = models.ForeignKey(
        TutorialStep,
        on_delete=models.CASCADE,
        related_name='snippets',
        verbose_name='步驟'
    )
    snippet_type = models.CharField(
        max_length=10,
        choices=SNIPPET_TYPE_CHOICES,
        default='text',
        verbose_name='片段類型'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='排序順序')
    content = models.TextField(
        blank=True,
        null=True,
        verbose_name='內容',
        help_text='文字或程式碼內容'
    )
    image = models.ImageField(
        upload_to='tutorials/images/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='圖片'
    )
    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        default='plaintext',
        verbose_name='程式語言',
        help_text='僅用於程式碼片段'
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='說明文字'
    )

    class Meta:
        verbose_name = '步驟片段'
        verbose_name_plural = '步驟片段'
        ordering = ['order']

    def __str__(self):
        return f'{self.step.title} - {self.get_snippet_type_display()} #{self.order}'


class ReadingLog(models.Model):
    """閱讀記錄模型"""
    tutorial = models.ForeignKey(
        Tutorial,
        on_delete=models.CASCADE,
        related_name='reading_logs',
        verbose_name='教材'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutorial_reading_logs',
        verbose_name='使用者'
    )
    total_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name='總閱讀秒數'
    )
    first_read_at = models.DateTimeField(auto_now_add=True, verbose_name='首次閱讀時間')
    last_read_at = models.DateTimeField(auto_now=True, verbose_name='最後閱讀時間')

    class Meta:
        verbose_name = '閱讀記錄'
        verbose_name_plural = '閱讀記錄'
        unique_together = [['tutorial', 'user']]
        ordering = ['-last_read_at']

    def __str__(self):
        return f'{self.user.username} - {self.tutorial.title} ({self.total_seconds}s)'

    @property
    def reading_time_display(self):
        """格式化顯示閱讀時間"""
        minutes = self.total_seconds // 60
        seconds = self.total_seconds % 60
        if minutes > 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f'{hours}小時{minutes}分鐘'
        elif minutes > 0:
            return f'{minutes}分鐘'
        else:
            return f'{seconds}秒'


class Question(models.Model):
    """提問模型"""
    step = models.ForeignKey(
        TutorialStep,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='步驟'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutorial_questions',
        verbose_name='提問者'
    )
    content = models.TextField(verbose_name='問題內容')
    is_resolved = models.BooleanField(default=False, verbose_name='是否已解決')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        verbose_name = '提問'
        verbose_name_plural = '提問'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.step.title} ({self.created_at.strftime("%Y-%m-%d")})'


class Answer(models.Model):
    """回答模型"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='問題'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tutorial_answers',
        verbose_name='回答者'
    )
    content = models.TextField(verbose_name='回答內容')
    is_from_maintainer = models.BooleanField(
        default=False,
        verbose_name='維護者回答',
        help_text='是否為教材維護者的回答'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        verbose_name = '回答'
        verbose_name_plural = '回答'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.user.username} 回答 {self.question.user.username} ({self.created_at.strftime("%Y-%m-%d")})'

    def save(self, *args, **kwargs):
        # 自動判斷是否為維護者回答
        if not self.pk:  # 只在新建時判斷
            tutorial = self.question.step.tutorial
            self.is_from_maintainer = TutorialMaintainer.objects.filter(
                tutorial=tutorial,
                user=self.user
            ).exists()
        super().save(*args, **kwargs)
