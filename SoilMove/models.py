from django.db import models

class SoilMove(models.Model):
    # Mapping: id=ID -> site_id
    site_id = models.CharField(max_length=100, unique=True, verbose_name="ID")
    
    # Mapping: dumpname=名稱 -> name
    name = models.CharField(max_length=255, verbose_name="名稱")
    
    # Mapping: city=縣市 -> city
    city = models.CharField(max_length=100, verbose_name="縣市")
    
    # Mapping: remain=B1~B7剩餘填埋量 -> remain_capacity
    remain_capacity = models.FloatField(null=True, blank=True, verbose_name="B1~B7剩餘填埋量")
    
    # Mapping: coord_status=轉換狀態 -> coord_status
    coord_status = models.CharField(max_length=100, null=True, blank=True, verbose_name="轉換狀態")
    
    # Mapping: typename=類型 -> site_type
    site_type = models.CharField(max_length=100, verbose_name="類型")
    
    # Mapping: controlId=流向編號 -> control_id
    control_id = models.CharField(max_length=100, null=True, blank=True, verbose_name="流向編號")
    
    # Mapping: x=經度 -> longitude
    longitude = models.FloatField(null=True, blank=True, verbose_name="經度")
    
    # Mapping: y=緯度 -> latitude
    latitude = models.FloatField(null=True, blank=True, verbose_name="緯度")
    
    # Mapping: area=面積 -> area
    area = models.FloatField(null=True, blank=True, verbose_name="面積")
    
    # Mapping: maxbury=B1~B7核准填埋量 -> max_capacity
    max_capacity = models.FloatField(null=True, blank=True, verbose_name="B1~B7核准填埋量")
    
    # Mapping: applydate=申報日期 -> apply_date
    # Keeping as CharField initially to handle potential format variations safely
    apply_date = models.CharField(max_length=100, null=True, blank=True, verbose_name="申報日期")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="資料更新時間")

    STATUS_CHOICES = (
        ('正常', '正常'),
        ('停止', '停止'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='正常', verbose_name="狀態")

    def __str__(self):
        return f"{self.name} ({self.city})"

    class Meta:
        verbose_name = "土方暫置場"
        verbose_name_plural = "土方暫置場"
