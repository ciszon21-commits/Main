from django.db import models


class WeatherStation(models.Model):
    """氣象站資訊模型"""
    station_code = models.CharField(max_length=20, unique=True, verbose_name='站碼')
    name = models.CharField(max_length=100, verbose_name='站名')
    city = models.CharField(max_length=50, blank=True, verbose_name='縣市')
    address = models.TextField(blank=True, verbose_name='地址')
    region = models.CharField(max_length=50, blank=True, verbose_name='區域')
    latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='緯度')
    longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, verbose_name='經度')
    altitude = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='高度(公尺)')
    established_date = models.DateField(null=True, blank=True, verbose_name='設站日期')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '氣象站'
        verbose_name_plural = '氣象站'
        ordering = ['station_code']

    def __str__(self):
        return f"{self.name} ({self.station_code})"


class MonthlyReport(models.Model):
    """月報表資料模型 - 逐日氣象資料"""
    station = models.ForeignKey(
        WeatherStation, 
        on_delete=models.CASCADE, 
        related_name='monthly_reports',
        verbose_name='氣象站'
    )
    obs_date = models.DateField(verbose_name='觀測日期')
    
    # 氣壓資料
    station_pressure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='測站氣壓(hPa)')
    sea_level_pressure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='海平面氣壓(hPa)')
    max_station_pressure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='最高測站氣壓(hPa)')
    min_station_pressure = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='最低測站氣壓(hPa)')
    
    # 氣溫資料
    temperature = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='平均氣溫(°C)')
    max_temperature = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='最高氣溫(°C)')
    max_temp_time = models.CharField(max_length=50, blank=True, verbose_name='最高氣溫時間')
    min_temperature = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='最低氣溫(°C)')
    min_temp_time = models.CharField(max_length=50, blank=True, verbose_name='最低氣溫時間')
    
    # 濕度資料
    relative_humidity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='相對濕度(%)')
    min_humidity = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='最小相對濕度(%)')
    
    # 風速風向資料
    wind_speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='平均風速(m/s)')
    wind_direction = models.CharField(max_length=20, blank=True, verbose_name='平均風向')
    max_wind_speed = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='最大陣風(m/s)')
    max_wind_direction = models.CharField(max_length=20, blank=True, verbose_name='最大陣風風向')
    
    # 降水資料
    precipitation = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='降水量(mm)')
    precipitation_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='降水時數(hr)')
    
    # 日照資料
    sunshine_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='日照時數(hr)')
    
    # 原始完整資料
    raw_data = models.JSONField(default=dict, blank=True, verbose_name='原始資料')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')

    class Meta:
        verbose_name = '月報表資料'
        verbose_name_plural = '月報表資料'
        ordering = ['-obs_date']
        unique_together = ['station', 'obs_date']

    def __str__(self):
        return f"{self.station.name} - {self.obs_date}"
