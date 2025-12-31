from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Topic(models.Model):
    name = models.CharField(max_length=255, verbose_name="主題名稱")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "主題"
        verbose_name_plural = "主題"
        ordering = ['-created_at']

class Keyword(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='keywords', verbose_name="所屬主題")
    word = models.CharField(max_length=255, verbose_name="關鍵字")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return f"{self.topic.name} - {self.word}"

    class Meta:
        verbose_name = "關鍵字"
        verbose_name_plural = "關鍵字"

class NewsItem(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='news_items', verbose_name="所屬主題")
    title = models.CharField(max_length=500, verbose_name="標題")
    date = models.DateTimeField(verbose_name="發布日期")
    url = models.URLField(max_length=1000, verbose_name="網址")
    source = models.CharField(max_length=255, verbose_name="資料來源")
    content = models.TextField(blank=True, verbose_name="新聞內容")
    summary = models.TextField(blank=True, verbose_name="新聞摘要")
    fetched_at = models.DateTimeField(auto_now_add=True, verbose_name="抓取時間")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "新聞項目"
        verbose_name_plural = "新聞項目"
        ordering = ['-date']

class DailySummary(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='daily_summaries', verbose_name="所屬主題")
    summary = models.TextField(verbose_name="摘要內容")
    news_source_html = models.TextField(blank=True, verbose_name="新聞來源HTML")
    date = models.DateField(default=timezone.now, verbose_name="摘要日期")
    news_count = models.IntegerField(default=0, verbose_name="新聞數量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return f"{self.topic.name} - {self.date}"

    class Meta:
        verbose_name = "每日摘要"
        verbose_name_plural = "每日摘要"
        ordering = ['-date']
        unique_together = ['topic', 'date']

class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='news_subscriptions', verbose_name="訂閱使用者")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="訂閱主題")
    email = models.EmailField(verbose_name="接收信箱")
    is_active = models.BooleanField(default=True, verbose_name="啟用狀態")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="訂閱時間")

    def __str__(self):
        return f"{self.user.username} - {self.topic.name}"

    class Meta:
        verbose_name = "訂閱"
        verbose_name_plural = "訂閱"
        unique_together = ['user', 'topic']
        ordering = ['-created_at']

class OpenAIResponse(models.Model):
    request_id = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    content = models.TextField()
    created = models.DateTimeField()
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    total_tokens = models.IntegerField()
    tag = models.CharField(default='NA',max_length=100)
    
    def __str__(self):
        return f"{self.model} @ {self.created}"