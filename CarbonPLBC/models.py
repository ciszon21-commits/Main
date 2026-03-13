from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class GlobalSettings(models.Model):
    """全域碳排放係數設定 (Singleton Pattern)"""
    
    # 私人運具排放係數 (kg CO2e/延人公里)
    car_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.120,
        verbose_name='汽車排放係數', help_text='kg CO2e/延人公里'
    )
    electric_car_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.055,
        verbose_name='電動車排放係數', help_text='kg CO2e/延人公里'
    )
    motorcycle_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.065,
        verbose_name='機車排放係數', help_text='kg CO2e/延人公里'
    )
    electric_motorcycle_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.025,
        verbose_name='電動機車排放係數', help_text='kg CO2e/延人公里'
    )
    
    # 大眾運具排放係數 (kg CO2e/延人公里)
    bus_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.045,
        verbose_name='公車排放係數', help_text='kg CO2e/延人公里'
    )
    intercity_bus_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.050,
        verbose_name='客運排放係數', help_text='kg CO2e/延人公里'
    )
    metro_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.020,
        verbose_name='捷運排放係數', help_text='kg CO2e/延人公里'
    )
    railway_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.018,
        verbose_name='鐵路排放係數', help_text='kg CO2e/延人公里'
    )
    
    # 再生能源減碳係數 (kg CO2e/kWh)
    solar_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.450,
        verbose_name='太陽能減碳係數', help_text='kg CO2e/kWh'
    )
    wind_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.460,
        verbose_name='風力減碳係數', help_text='kg CO2e/kWh'
    )
    
    # 其他減碳係數
    water_recycling_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.152,
        verbose_name='自來水碳足跡', help_text='kg CO2e/m³'
    )
    waste_recycling_factor = models.DecimalField(
        max_digits=10, decimal_places=4, default=1.230,
        verbose_name='焚化爐碳足跡', help_text='kg CO2e/噸'
    )
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    
    class Meta:
        verbose_name = '全域碳排放係數設定'
        verbose_name_plural = '全域碳排放係數設定'
    
    def save(self, *args, **kwargs):
        """確保只有一筆設定記錄 (Singleton)"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """防止刪除"""
        pass
    
    @classmethod
    def load(cls):
        """載入全域設定，若不存在則建立預設值"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f'碳排放係數設定 (更新於 {self.updated_at})'


class CarbonEmissionInput(models.Model):
    """碳排放計算輸入數據"""
    
    # 基本資訊
    name = models.CharField(max_length=200, verbose_name='計算名稱')
    description = models.TextField(blank=True, verbose_name='說明')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='建立時間')
    
    # BC1 混合旅次產生量
    # 混合使用旅次量 (次/年)
    trip_count = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='混合使用旅次量', help_text='次/年'
    )
    
    # 私人運具與大眾運具之比例 (%)
    private_transport_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00,
        validators=[MinValueValidator(0)],
        verbose_name='私人運具比例', help_text='%'
    )
    public_transport_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, default=50.00,
        validators=[MinValueValidator(0)],
        verbose_name='大眾運具比例', help_text='%'
    )
    
    # 平均旅次距離 (km)
    avg_trip_distance = models.DecimalField(
        max_digits=10, decimal_places=2, default=5.00,
        validators=[MinValueValidator(0)],
        verbose_name='平均旅次距離', help_text='公里'
    )
    
    # 私人運具旅次量 (次/年)
    car_trip_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='汽車年旅次量', help_text='次/年'
    )
    motorcycle_trip_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='機車年旅次量', help_text='次/年'
    )
    
    # 大眾運具旅次量 (次/年)
    bus_trip_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='公車年旅次量', help_text='次/年'
    )
    intercity_bus_trip_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='客運年旅次量', help_text='次/年'
    )
    metro_trip_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='捷運年旅次量', help_text='次/年'
    )
    railway_trip_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='鐵路年旅次量', help_text='次/年'
    )
    
    # 計算後的延人公里 (由系統自動計算，不需使用者輸入)
    car_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='汽車延人公里', help_text='自動計算', editable=False
    )
    electric_car_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='電動車延人公里', help_text='自動計算', editable=False
    )
    motorcycle_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='機車延人公里', help_text='自動計算', editable=False
    )
    electric_motorcycle_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='電動機車延人公里', help_text='自動計算', editable=False
    )
    
    # 大眾運具延人公里 (由系統自動計算)
    bus_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='公車延人公里', help_text='自動計算', editable=False
    )
    intercity_bus_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='客運延人公里', help_text='自動計算', editable=False
    )
    metro_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='捷運延人公里', help_text='自動計算', editable=False
    )
    railway_passenger_km = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='鐵路延人公里', help_text='自動計算', editable=False
    )
    
    # 再生能源
    solar_area = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='太陽能板設置面積', help_text='m²'
    )
    solar_capacity_factor = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.15,
        validators=[MinValueValidator(0)],
        verbose_name='太陽能容量因數', help_text='0-1之間'
    )
    wind_area = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='風力發電設置面積', help_text='m²'
    )
    wind_capacity_factor = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.25,
        validators=[MinValueValidator(0)],
        verbose_name='風力容量因數', help_text='0-1之間'
    )
    
    # 回收水量
    recycled_water_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='回收水量', help_text='m³/年'
    )
    
    # 廢棄物處理量
    waste_recycled_volume = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        validators=[MinValueValidator(0)],
        verbose_name='廢棄物回收量', help_text='噸/年'
    )
    
    class Meta:
        verbose_name = '碳排放計算輸入'
        verbose_name_plural = '碳排放計算輸入'
        ordering = ['-created_at']
    
    def calculate_passenger_km(self):
        """根據旅次量和平均距離計算各運具的延人公里"""
        from decimal import Decimal
        
        # 確保平均旅次距離為 Decimal
        avg_dist = Decimal(str(self.avg_trip_distance)) if self.avg_trip_distance else Decimal('5.00')

        # 計算各私人運具的延人公里
        self.car_passenger_km = self.car_trip_volume * avg_dist
        self.motorcycle_passenger_km = self.motorcycle_trip_volume * avg_dist
        
        # 電動車欄位設為0（保留欄位但目前不計算）
        self.electric_car_passenger_km = Decimal('0')
        self.electric_motorcycle_passenger_km = Decimal('0')
        
        # 計算各大眾運具的延人公里
        self.bus_passenger_km = self.bus_trip_volume * avg_dist
        self.intercity_bus_passenger_km = self.intercity_bus_trip_volume * avg_dist
        self.metro_passenger_km = self.metro_trip_volume * avg_dist
        self.railway_passenger_km = self.railway_trip_volume * avg_dist
    
    def save(self, *args, **kwargs):
        """儲存前先計算延人公里"""
        self.calculate_passenger_km()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.name} ({self.created_at.strftime("%Y-%m-%d %H:%M")})'


class CarbonEmissionResult(models.Model):
    """碳排放計算結果"""
    
    input_data = models.OneToOneField(
        CarbonEmissionInput, on_delete=models.CASCADE,
        related_name='result', verbose_name='輸入數據'
    )
    
    # 混合旅次產生量 (kg CO2e)
    mixed_private_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='混合私人碳排量'
    )
    mixed_public_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='混合大眾碳排量'
    )
    mixed_total_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='混合總碳排量'
    )

    # 私人運具碳排量 (kg CO2e)
    car_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='汽車碳排量'
    )
    electric_car_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='電動車碳排量'
    )
    motorcycle_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='機車碳排量'
    )
    electric_motorcycle_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='電動機車碳排量'
    )
    private_vehicle_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='私人運具總碳排量'
    )
    
    # 大眾運具碳排量 (kg CO2e)
    bus_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='公車碳排量'
    )
    intercity_bus_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='客運碳排量'
    )
    metro_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='捷運碳排量'
    )
    railway_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='鐵路碳排量'
    )
    public_transport_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='大眾運具總碳排量'
    )
    
    # 碳減量 (kg CO2e)
    solar_reduction = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='太陽能減碳量'
    )
    wind_reduction = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='風力減碳量'
    )
    renewable_energy_total = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='再生能源總減碳量'
    )
    water_recycling_reduction = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='回收水減碳量'
    )
    waste_recycling_reduction = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='廢棄物回收減碳量'
    )
    
    # 總計
    total_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='總碳排量'
    )
    total_reduction = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='總減碳量'
    )
    net_emission = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name='淨碳排量'
    )
    
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name='計算時間')
    
    class Meta:
        verbose_name = '碳排放計算結果'
        verbose_name_plural = '碳排放計算結果'
    
    def __str__(self):
        return f'{self.input_data.name} 計算結果'
