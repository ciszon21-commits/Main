from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class RentalNature(models.Model):
    name = models.CharField('性質名稱', max_length=50, unique=True)

    class Meta:
        verbose_name = '租借性質'
        verbose_name_plural = '租借性質管理'

    def __str__(self):
        return self.name

class EquipmentCategory(models.Model):
    name = models.CharField('種類名稱', max_length=50, unique=True)
    description = models.TextField('描述', blank=True)
    icon = models.CharField('圖示線索', max_length=50, default='fas fa-box', help_text='如: fas fa-laptop')

    class Meta:
        verbose_name = '設備種類'
        verbose_name_plural = '設備種類管理'

    def __str__(self):
        return self.name

class XrEquipment(models.Model):
    SECTION_CHOICES = [
        ('vr', 'VR 專區'),
        ('gopro', 'GoPro 專區'),
    ]
    STATUS_CHOICES = [
        ('available', '庫存'),
        ('reserved', '預約'),
        ('rented', '出借'),
        ('maintenance', '維修'),
        ('retired', '退役'),
    ]
    section = models.CharField('專區', max_length=20, choices=SECTION_CHOICES, default='vr')
    category = models.ForeignKey(EquipmentCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='設備種類', related_name='equipments')
    name = models.CharField('設備名稱', max_length=100)
    serial_number = models.CharField('設備編號', max_length=50, unique=True, blank=True, null=True)
    specifications = models.TextField('設備規格', blank=True)
    note = models.TextField('備註', blank=True)
    status = models.CharField('狀態', max_length=20, choices=STATUS_CHOICES, default='available')
    
    def update_status(self, exclude_ids=None):
        """
        根據關連的租借申請自動更新設備狀態。
        優先級：出借 (rented) > 預約 (reserved) > 庫存 (available)
        維修 (maintenance) 與 退役 (retired) 為手動狀態，不自動變動。
        
        :param exclude_ids: 排除在計算之外的 XrRentalRecord ID 列表 (常用於正在處理中的歸還/轉移)
        """
        if self.status in ['maintenance', 'retired']:
            return

        rentals = self.xrrentalrecord_set.all()
        if exclude_ids:
            rentals = rentals.exclude(id__in=exclude_ids)

        # 核心檢查：是否有其他活躍的單據
        if rentals.filter(status='approved').exists():
            new_status = 'rented'
        elif rentals.filter(status='pending').exists():
            new_status = 'reserved'
        else:
            new_status = 'available'

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

    class Meta:
        verbose_name = '資源設備'
        verbose_name_plural = '資源設備清單'
        ordering = ['serial_number']

    def __str__(self):
        if self.serial_number and str(self.serial_number).lower() != 'none':
            return f"{self.name} ({self.serial_number})"
        return self.name

class XrSupportRecord(models.Model):
    NATURE_CHOICES = [
        ('rental', '純租借'),
        ('support', '技術支援'),
        ('event', '活動配合'),
    ]
    date = models.DateField('日期', default=timezone.now)
    department = models.CharField('租借部門', max_length=100)
    reason = models.TextField('原因', blank=True)
    nature = models.CharField('租借性質', max_length=20, choices=NATURE_CHOICES)
    equipment_count = models.PositiveIntegerField('研資設備(台)', default=0)
    support_people = models.PositiveIntegerField('研資支援(人)', default=0)
    event_scale = models.PositiveIntegerField('活動規模(人)', default=0)
    
    rented_equipments = models.ManyToManyField(XrEquipment, verbose_name='租借設備', blank=True)

    class Meta:
        verbose_name = 'XR支援事務'
        verbose_name_plural = 'XR支援事務紀錄'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.department} ({self.get_nature_display()})"

class GoProRentalRecord(models.Model):
    date = models.DateField('日期', default=timezone.now)
    department = models.CharField('租借部門', max_length=100)
    borrower = models.CharField('租借人', max_length=50)
    reason = models.TextField('原因', blank=True)
    equipment = models.CharField('設備', max_length=100) 
    note = models.TextField('備註', blank=True)

    class Meta:
        verbose_name = 'GoPro租借紀錄'
        verbose_name_plural = 'GoPro租借紀錄'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.borrower} ({self.department})"

class XrBulkItem(models.Model):
    SECTION_CHOICES = XrEquipment.SECTION_CHOICES
    section = models.CharField('專區', max_length=20, choices=SECTION_CHOICES, default='vr')
    name = models.CharField('項目名稱', max_length=100)
    total_count = models.PositiveIntegerField('總數量', default=0)
    available_count = models.PositiveIntegerField('庫存數量', default=0)
    reserved_count = models.PositiveIntegerField('待扣數量', default=0)
    note = models.TextField('備註', blank=True)

    class Meta:
        verbose_name = '數量統計設備'
        verbose_name_plural = '數量統計設備'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.pk:
            # 新增項目的情況
            self.available_count = self.total_count
        else:
            # 如果是更新現有項目，要根據總數的變動調整庫存數
            old_obj = XrBulkItem.objects.get(pk=self.pk)
            diff = self.total_count - old_obj.total_count
            self.available_count += diff
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.available_count}/{self.total_count})"

class XrRentalRecord(models.Model):
    activity_date = models.DateField('活動日期')
    rental_start = models.DateField('租借起始日期')
    rental_end = models.DateField('租借結束日期')
    department = models.CharField('部門', max_length=100)
    borrower_name = models.CharField('租借人姓名', max_length=50)
    borrower_id = models.CharField('租借人員工編號', max_length=50)
    activity_name = models.CharField('活動名稱', max_length=200)
    reason = models.TextField('租借原因', blank=True)
    nature = models.ForeignKey(RentalNature, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='租借性質')
    
    STATUS_CHOICES = [
        ('pending', '待核准'),
        ('approved', '已核准'),
        ('rejected', '已拒絕'),
        ('returned', '已歸還'),
    ]
    status = models.CharField('單據狀態', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    equipments = models.ManyToManyField(XrEquipment, verbose_name='租借設備', blank=True)
    bulk_items = models.ManyToManyField(XrBulkItem, through='XrRentalBulkItem', verbose_name='租借配件', blank=True)
    
    return_notes = models.TextField('歸還備註', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '設備租借登記'
        verbose_name_plural = '設備租借登記'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_name} - {self.borrower_name} ({self.department})"

class XrRentalBulkItem(models.Model):
    rental_record = models.ForeignKey(XrRentalRecord, on_delete=models.CASCADE)
    bulk_item = models.ForeignKey(XrBulkItem, on_delete=models.CASCADE)
    count = models.PositiveIntegerField('租借數量', default=1)
    is_returned = models.BooleanField('是否已歸還', default=False)

    def __str__(self):
        status = "(已歸還)" if self.is_returned else ""
        return f"{self.bulk_item.name} x {self.count} {status}"

class XrUserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', '管理權限'),
        ('user', '一般使用者'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='xr_profile')
    role = models.CharField('權限角色', max_length=20, choices=ROLE_CHOICES, default='user')

    class Meta:
        verbose_name = '使用者權限設定'
        verbose_name_plural = '使用者權限管理'

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

# Signals 確保每個 User 都有 Profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        XrUserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'xr_profile'):
        XrUserProfile.objects.create(user=instance)
    instance.xr_profile.save()
