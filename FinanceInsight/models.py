from django.db import models
from django.utils import timezone


class NewsCategory(models.Model):
    """新聞分類"""
    CATEGORY_CHOICES = [
        ('TW_FINANCE', '台灣財經'),
        ('US_FINANCE', '美國財經'),
        ('INDUSTRY', '產業動態'),
        ('GLOBAL', '國際經濟'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="分類名稱")
    code = models.CharField(max_length=20, unique=True, choices=CATEGORY_CHOICES, verbose_name="分類代碼")
    description = models.TextField(blank=True, verbose_name="分類說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "新聞分類"
        verbose_name_plural = "新聞分類"
        ordering = ['name']


class FinancialNews(models.Model):
    """財經新聞"""
    category = models.ForeignKey(
        NewsCategory, 
        on_delete=models.CASCADE, 
        related_name='news_items',
        verbose_name="分類"
    )
    title = models.CharField(max_length=500, verbose_name="標題")
    content = models.TextField(blank=True, verbose_name="內容")
    source = models.CharField(max_length=255, verbose_name="來源")
    source_url = models.URLField(max_length=1000, blank=True, verbose_name="來源網址")
    published_at = models.DateTimeField(verbose_name="發布時間")
    fetched_at = models.DateTimeField(auto_now_add=True, verbose_name="抓取時間")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "財經新聞"
        verbose_name_plural = "財經新聞"
        ordering = ['-published_at']


class DailyNewsSummary(models.Model):
    """當日新聞摘要與總結"""
    category = models.ForeignKey(
        NewsCategory, 
        on_delete=models.CASCADE, 
        related_name='daily_summaries',
        verbose_name="新聞分類"
    )
    date = models.DateField(default=timezone.now, verbose_name="日期")
    summary = models.TextField(verbose_name="當日新聞摘要")
    conclusion = models.TextField(verbose_name="當日新聞總結")
    news_count = models.IntegerField(default=0, verbose_name="新聞數量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return f"{self.category.name} - {self.date}"

    class Meta:
        verbose_name = "當日新聞摘要"
        verbose_name_plural = "當日新聞摘要"
        ordering = ['-date']
        unique_together = ['category', 'date']


class StockMarket(models.Model):
    """股市類型"""
    MARKET_CHOICES = [
        ('TWSE', '台北股市'),
        ('NYSE', '紐約證券交易所'),
        ('NASDAQ', '那斯達克'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="股市名稱")
    code = models.CharField(max_length=20, unique=True, choices=MARKET_CHOICES, verbose_name="股市代碼")
    country = models.CharField(max_length=50, verbose_name="國家/地區")
    description = models.TextField(blank=True, verbose_name="說明")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "股市類型"
        verbose_name_plural = "股市類型"
        ordering = ['name']


class StockRecommendation(models.Model):
    """選股標的建議"""
    market = models.ForeignKey(
        StockMarket, 
        on_delete=models.CASCADE, 
        related_name='recommendations',
        verbose_name="股市"
    )
    stock_code = models.CharField(max_length=20, verbose_name="個股編號")
    stock_name = models.CharField(max_length=100, verbose_name="股票名稱")
    current_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="盤價"
    )
    price_change = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        verbose_name="漲跌"
    )
    price_change_percent = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0,
        verbose_name="漲跌幅(%)"
    )
    recommendation_date = models.DateField(default=timezone.now, verbose_name="建議日期")
    recommendation_reason = models.TextField(blank=True, verbose_name="推薦原因")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")

    def __str__(self):
        return f"{self.stock_code} - {self.stock_name}"

    class Meta:
        verbose_name = "選股建議"
        verbose_name_plural = "選股建議"
        ordering = ['-recommendation_date', 'stock_code']


class StockTrend(models.Model):
    """個股趨勢"""
    stock = models.ForeignKey(
        StockRecommendation, 
        on_delete=models.CASCADE, 
        related_name='trends',
        verbose_name="關聯股票"
    )
    trend_description = models.TextField(verbose_name="趨勢說明")
    analysis_date = models.DateField(default=timezone.now, verbose_name="分析日期")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return f"{self.stock.stock_name} - {self.analysis_date}"

    class Meta:
        verbose_name = "個股趨勢"
        verbose_name_plural = "個股趨勢"
        ordering = ['-analysis_date']
