from django.db import models
from django.contrib.auth.models import User
import os

class Project(models.Model):
    STATUS_CHOICES = [
        ('PREPARING', '籌備中'),
        ('ONGOING', '進行中'),
        ('FINISHED', '已結案'),
    ]
    name = models.CharField(max_length=255, verbose_name="標案名稱")
    code = models.CharField(max_length=50, unique=True, verbose_name="標案編號")
    description = models.TextField(blank=True, verbose_name="標案說明")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="建立者", related_name='created_projects')
    responsible_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="標案管理員", related_name='responsible_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PREPARING', verbose_name="標案狀態")

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "標案"
        verbose_name_plural = "標案"

class Discipline(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='disciplines', verbose_name="標案")
    code = models.CharField(max_length=10, verbose_name="專業代碼", default='01')
    name = models.CharField(max_length=100, verbose_name="專業名稱")
    is_overall = models.BooleanField(default=False, verbose_name="是否為整合專業")
    responsible_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="專業管理員", related_name='responsible_disciplines')
    members = models.ManyToManyField(User, related_name='discipline_members', blank=True, verbose_name="專業成員")
    budget_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="預算管理員", related_name='managed_budgets')
    budget_members = models.ManyToManyField(User, related_name='budget_memberships', blank=True, verbose_name="預算成員")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")

    def __str__(self):
        return f"{self.project.name} - [{self.code}] {self.name}"
    
    class Meta:
        verbose_name = "專業分組"
        verbose_name_plural = "專業分組"
        ordering = ['project', 'code']
        unique_together = ('project', 'code')

class BaseFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name="標案")
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, null=True, blank=True, verbose_name="專業分組")
    file = models.FileField(upload_to='budget_review/%Y/%m/%d/', verbose_name="檔案")
    file_name = models.CharField(max_length=255, verbose_name="原始檔名")
    version = models.IntegerField(default=1, verbose_name="版本號")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="上傳者")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="上傳時間")
    description = models.TextField(blank=True, verbose_name="版本說明")
    is_latest = models.BooleanField(default=True, verbose_name="是否為最新版本")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.file_name and self.file:
            self.file_name = os.path.basename(self.file.name)
        
        # When saving a new version, mark previous versions as not latest
        if self.pk is None:
            # This is a bit tricky for abstract models, we handles it in the actual model OR use a generic way
            pass
        super().save(*args, **kwargs)

class QuantityFile(BaseFile):
    class Meta:
        verbose_name = "數量計算書"
        verbose_name_plural = "數量計算書"

class PriceInquiryFile(BaseFile):
    class Meta:
        verbose_name = "訪價資料"
        verbose_name_plural = "訪價資料"

class BudgetFile(BaseFile):
    BUDGET_TYPE_CHOICES = [
        ('GROUP', '分組預算'),
        ('EXTERNAL', '外部門預算'),
    ]
    budget_type = models.CharField(max_length=20, choices=BUDGET_TYPE_CHOICES, default='GROUP', verbose_name="預算類型")

    class Meta:
        verbose_name = "分組預算"
        verbose_name_plural = "分組預算"

class FinalBudgetFile(BaseFile):
    FILE_TYPE_CHOICES = [
        ('INTEGRATED', '整合預算'),
        ('BLANK_TENDER', '空白標單'),
    ]
    is_confidential = models.BooleanField(default=False, verbose_name="是否為保密版")
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='INTEGRATED', verbose_name="檔案類型")

    class Meta:
        verbose_name = "整合版預算"
        verbose_name_plural = "整合版預算"

class PriceAdjustment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='price_adjustments', verbose_name="標案")
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, null=True, blank=True, verbose_name="專業分組")
    item_code = models.CharField(max_length=100, verbose_name="項目代碼")
    item_name = models.CharField(max_length=255, verbose_name="項目名稱")
    original_price = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="原始單價")
    adjusted_price = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="調整後單價")
    reason = models.TextField(verbose_name="調整原因")
    adjusted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="調整者")
    adjusted_at = models.DateTimeField(auto_now_add=True, verbose_name="調整時間")

    class Meta:
        verbose_name = "單價調整紀錄"
        verbose_name_plural = "單價調整紀錄"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', '建立'),
        ('UPDATE', '更新'),
        ('DELETE', '刪除'),
        ('DOWNLOAD', '下載'),
        ('UPLOAD', '上傳'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="操作者")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="操作類型")
    model_name = models.CharField(max_length=100, verbose_name="資料模型名稱")
    object_id = models.PositiveIntegerField(null=True, verbose_name="物件ID")
    detail = models.JSONField(default=dict, verbose_name="操作詳情")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="時間點")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP位址")

    class Meta:
        verbose_name = "操作紀錄"
        verbose_name_plural = "操作紀錄"
