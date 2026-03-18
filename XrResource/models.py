from django.db import models
from django.utils import timezone

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
    STATUS_CHOICES = [
        ('available', '在庫'),
        ('rented', '已出借'),
        ('maintenance', '維修中'),
        ('retired', '已退役'),
    ]
    category = models.ForeignKey(EquipmentCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='設備種類', related_name='equipments')
    name = models.CharField('設備名稱', max_length=100)
    serial_number = models.CharField('設備編號', max_length=50, unique=True)
    specifications = models.TextField('設備規格', blank=True)
    note = models.TextField('備註', blank=True)
    status = models.CharField('租用狀態', max_length=20, choices=STATUS_CHOICES, default='available')

    class Meta:
        verbose_name = 'XR設備'
        verbose_name_plural = 'XR設備清單'
        ordering = ['serial_number']

    def __str__(self):
        return f"{self.name} ({self.serial_number})"

class GoProAccessory(models.Model):
    name = models.CharField('配件名稱', max_length=100)
    stock_quantity = models.PositiveIntegerField('庫存數量', default=0)
    # 這裡使用者提到 "對應1-1表已出借數量"，通常這可以透過關聯計算或手動紀錄
    # 若要精確關聯，應有具體的出借單據。在此先提供欄位紀錄。
    rented_quantity = models.PositiveIntegerField('已出借數量', default=0)

    class Meta:
        verbose_name = 'GoPro配件'
        verbose_name_plural = 'GoPro配件庫存'

    def __str__(self):
        return self.name

class VrComputer(models.Model):
    serial_number = models.CharField('設備編號', max_length=50, unique=True)
    specifications = models.TextField('設備規格', blank=True)
    note = models.TextField('備註', blank=True)
    local_account = models.CharField('本機帳號', max_length=50, blank=True)
    local_password = models.CharField('本機密碼', max_length=50, blank=True)

    class Meta:
        verbose_name = 'VR專用電腦'
        verbose_name_plural = 'VR專用電腦清單'

    def __str__(self):
        return self.serial_number

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
    
    # 與租借設備FK多選關聯 (ManyToManyField)
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
    equipment = models.CharField('設備', max_length=100) # 若GoPro有獨立清單可改FK，目前依需求設為CharField
    note = models.TextField('備註', blank=True)

    class Meta:
        verbose_name = 'GoPro租借紀錄'
        verbose_name_plural = 'GoPro租借紀錄'
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.borrower} ({self.department})"
