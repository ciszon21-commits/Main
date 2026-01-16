from django.db import models
from django.contrib.auth.models import User
from SinoFile.fields import SinoFileField
import os


def patent_certificate_path(instance, filename):
    """Generate file path for patent certificate uploads"""
    return f'patent_certificates/{instance.application.id}/{filename}'


class PatentApplication(models.Model):
    """專利申請項目"""
    STATUS_CHOICES = [
        ('PENDING', '申請中'),
        ('APPROVED', '通過'),
        ('REJECTED', '不通過'),
    ]
    
    CATEGORY_CHOICES = [
        ('INVENTION', '發明專利'),
        ('UTILITY_MODEL', '新型專利'),
        ('DESIGN', '設計專利'),
    ]
    
    plan_number = models.CharField(max_length=50, verbose_name="計畫編號")
    outsource_number = models.CharField(max_length=50, verbose_name="委外編號", blank=True)
    item_number = models.PositiveIntegerField(verbose_name="項次", default=1)
    name = models.CharField(max_length=255, verbose_name="申請專利項目名稱")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="申請專利項目類別")
    patent_firm = models.CharField(max_length=200, verbose_name="委託專利事務所名稱")
    firm_case_number = models.CharField(max_length=50, verbose_name="事務所案號", blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="狀態")
    is_public = models.BooleanField(default=False, verbose_name="是否公開")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name="建立者", related_name='patent_applications')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "專利申請"
        verbose_name_plural = "專利申請"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.plan_number} - {self.name}"
    
    @property
    def is_pending(self):
        return self.status == 'PENDING'
    
    @property
    def is_approved(self):
        return self.status == 'APPROVED'
    
    @property
    def is_rejected(self):
        return self.status == 'REJECTED'
    
    @property
    def rebuttal_count(self):
        return self.rebuttals.count()
    
    @property
    def total_rebuttal_fee(self):
        return self.rebuttals.aggregate(total=models.Sum('fee'))['total'] or 0


class PatentRebuttal(models.Model):
    """答辯記錄"""
    REBUTTAL_TYPE_CHOICES = [
        ('FIRST', '初次答辯'),
        ('SECOND', '二次答辯'),
        ('THIRD', '三次答辯'),
        ('OTHER', '其他答辯'),
    ]
    
    application = models.ForeignKey(PatentApplication, on_delete=models.CASCADE, 
                                    related_name='rebuttals', verbose_name="專利申請")
    rebuttal_type = models.CharField(max_length=20, choices=REBUTTAL_TYPE_CHOICES, 
                                     verbose_name="答辯類別")
    document_date = models.DateField(verbose_name="答辯單據日期")
    fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="費用", default=0)
    notes = models.TextField(verbose_name="備註", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    
    class Meta:
        verbose_name = "答辯記錄"
        verbose_name_plural = "答辯記錄"
        ordering = ['document_date']
    
    def __str__(self):
        return f"{self.application.name} - {self.get_rebuttal_type_display()}"


class GrantedPatent(models.Model):
    """已取得專利"""
    application = models.OneToOneField(PatentApplication, on_delete=models.CASCADE, 
                                       related_name='granted_patent', verbose_name="專利申請")
    patent_number = models.CharField(max_length=50, verbose_name="專利編號")
    patent_name = models.CharField(max_length=255, verbose_name="專利名稱")
    patent_period = models.CharField(max_length=50, verbose_name="專利期間", blank=True)
    description = models.TextField(verbose_name="專利簡述", blank=True)
    start_date = models.DateField(verbose_name="專利起始年月")
    end_date = models.DateField(verbose_name="專利結束年月")
    certificate = SinoFileField(upload_to=patent_certificate_path, verbose_name="專利證書", 
                                   blank=True, null=True)
    
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="取得時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        verbose_name = "已取得專利"
        verbose_name_plural = "已取得專利"
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"{self.patent_number} - {self.patent_name}"
    
    @property
    def granted_year(self):
        """取得專利的年度"""
        return self.start_date.year if self.start_date else None
    
    @property
    def certificate_filename(self):
        """取得證書檔案名稱"""
        if self.certificate:
            return os.path.basename(self.certificate.name)
        return None


class PatentAnnuity(models.Model):
    """專利年費核銷記錄"""
    granted_patent = models.ForeignKey(GrantedPatent, on_delete=models.CASCADE, 
                                       related_name='annuities', verbose_name="已取得專利")
    write_off_plan_number = models.CharField(max_length=50, verbose_name="核銷計畫編號")
    write_off_date = models.DateField(verbose_name="核銷年月")
    year = models.PositiveIntegerField(verbose_name="核銷年度")
    notes = models.TextField(verbose_name="備註", blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name="建立者", related_name='patent_annuities')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    
    class Meta:
        verbose_name = "專利年費核銷"
        verbose_name_plural = "專利年費核銷"
        ordering = ['-year', '-write_off_date']
        unique_together = ['granted_patent', 'year']
    
    def __str__(self):
        return f"{self.granted_patent.patent_name} - {self.year}年度核銷"


class PatentAdmin(models.Model):
    """專利管理員"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, 
                                 related_name='patent_admin', verbose_name="使用者")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="設定時間")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="設定者", related_name='created_patent_admins')
    
    class Meta:
        verbose_name = "專利管理員"
        verbose_name_plural = "專利管理員"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"專利管理員: {self.user.username}"


def is_patent_admin(user):
    """
    檢查使用者是否為專利管理員
    超級使用者或已設定為專利管理員者返回 True
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return PatentAdmin.objects.filter(user=user).exists()
