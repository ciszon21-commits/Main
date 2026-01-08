from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from SinoFile.fields import SinoFileField


class MLModel(models.Model):
    """機器學習模型管理"""
    MODEL_TYPE_CHOICES = [
        ('xgboost', 'XGBoost 模型'),
        ('pca', 'PCA 模型'),
        ('embedding_map', 'Embedding Map'),
    ]
    
    model_type = models.CharField(
        max_length=20,
        choices=MODEL_TYPE_CHOICES,
        verbose_name='模型類型'
    )
    file = SinoFileField(
        upload_to='ml_models/',
        verbose_name='模型檔案'
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name='啟用中'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='上傳時間'
    )
    description = models.TextField(
        blank=True,
        verbose_name='說明'
    )
    
    class Meta:
        db_table = 'ml_model'
        verbose_name = '機器學習模型'
        verbose_name_plural = '機器學習模型'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['model_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.get_model_type_display()} - {'啟用' if self.is_active else '未啟用'}"
    
    def save(self, *args, **kwargs):
        """儲存時確保同類型只有一個啟用的模型"""
        if self.is_active:
            # 將同類型的其他模型設為未啟用
            MLModel.objects.filter(
                model_type=self.model_type,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class ClashReport(models.Model):
    """Navisworks 碰撞報告模型"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='clash_reports',
        verbose_name='上傳者'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='報告標題'
    )
    html_file = SinoFileField(
        upload_to='clash_reports/html/%Y/%m/%d/',
        verbose_name='HTML 檔案'
    )
    csv_file = SinoFileField(
        upload_to='clash_reports/csv/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='CSV 檔案'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='上傳時間'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='已刪除'
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='刪除時間'
    )

    class Meta:
        db_table = 'clash_report'
        verbose_name = '碰撞報告'
        verbose_name_plural = '碰撞報告'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def soft_delete(self):
        """軟刪除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()


class ClassificationResult(models.Model):
    """分類結果模型"""
    STATUS_CHOICES = [
        (0, '已解決'),
        (1, '作用中'),
        (2, '新'),
    ]

    PREDICTION_CHOICES = [
        (0, '不是碰撞'),
        (1, '是碰撞'),
    ]

    report = models.ForeignKey(
        ClashReport,
        on_delete=models.CASCADE,
        related_name='classifications',
        verbose_name='所屬報告'
    )
    row_index = models.IntegerField(
        verbose_name='資料行索引'
    )
    
    # 碰撞資訊
    distance = models.FloatField(
        verbose_name='碰撞距離'
    )
    
    # 項目 1 資訊
    item1_id = models.CharField(
        max_length=50,
        verbose_name='項目1 ID'
    )
    item1_system = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='項目1 系統'
    )
    item1_type = models.CharField(
        max_length=255,
        verbose_name='項目1 類型'
    )
    item1_count = models.IntegerField(
        verbose_name='項目1 出現次數'
    )
    
    # 項目 2 資訊
    item2_id = models.CharField(
        max_length=50,
        verbose_name='項目2 ID'
    )
    item2_system = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='項目2 系統'
    )
    item2_type = models.CharField(
        max_length=255,
        verbose_name='項目2 類型'
    )
    item2_count = models.IntegerField(
        verbose_name='項目2 出現次數'
    )
    
    # 狀態與分類結果
    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=1,
        verbose_name='狀態'
    )
    predicted_class = models.IntegerField(
        choices=PREDICTION_CHOICES,
        verbose_name='預測分類'
    )
    confidence = models.FloatField(
        verbose_name='信心度'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='建立時間'
    )

    class Meta:
        db_table = 'classification_result'
        verbose_name = '分類結果'
        verbose_name_plural = '分類結果'
        ordering = ['report', 'row_index']
        indexes = [
            models.Index(fields=['report', 'row_index']),
            models.Index(fields=['predicted_class']),
        ]

    def __str__(self):
        return f"Report {self.report.id} - Row {self.row_index}"
