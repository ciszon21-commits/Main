from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count


class ImageCategory(models.Model):
    """圖片分類模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name='分類名稱')
    is_default = models.BooleanField(default=False, verbose_name='預設分類')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='建立者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')

    class Meta:
        verbose_name = '圖片分類'
        verbose_name_plural = '圖片分類'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name


class Image(models.Model):
    """圖片主體模型"""
    title = models.CharField(max_length=200, verbose_name='圖片標題')
    description = models.TextField(blank=True, verbose_name='圖片描述')
    image = models.ImageField(upload_to='gallery/%Y/%m/', verbose_name='圖片檔案')
    category = models.ForeignKey(
        ImageCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='images',
        verbose_name='分類'
    )
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='uploaded_images',
        verbose_name='上傳者'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上傳時間')
    view_count = models.PositiveIntegerField(default=0, verbose_name='瀏覽次數')

    class Meta:
        verbose_name = '圖片'
        verbose_name_plural = '圖片'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        """計算平均評分"""
        result = self.ratings.aggregate(avg=Avg('rating'))
        return round(result['avg'], 2) if result['avg'] else 0

    @property
    def total_ratings(self):
        """計算評分總數"""
        return self.ratings.count()

    def get_rating_distribution(self):
        """取得評分分布（包含數量和百分比）"""
        distribution = {}
        total = self.total_ratings

        # 初始化所有評分等級
        for i in range(1, 6):
            distribution[i] = {'count': 0, 'percentage': 0}

        # 統計各評分的數量
        ratings = self.ratings.values('rating').annotate(count=Count('rating'))
        for item in ratings:
            count = item['count']
            distribution[item['rating']]['count'] = count
            # 計算百分比
            if total > 0:
                distribution[item['rating']]['percentage'] = round((count / total) * 100, 1)

        return distribution

    def increment_view_count(self):
        """增加瀏覽次數"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class ImageRating(models.Model):
    """圖片評分模型"""
    image = models.ForeignKey(
        Image, 
        on_delete=models.CASCADE,
        related_name='ratings',
        verbose_name='圖片'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='image_ratings',
        verbose_name='評分者'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='評分'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='評分時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '圖片評分'
        verbose_name_plural = '圖片評分'
        unique_together = [['image', 'user']]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.image.title} - {self.rating}星'
