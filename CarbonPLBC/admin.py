"""Django Admin 設定"""
from django.contrib import admin
from .models import GlobalSettings, CarbonEmissionInput, CarbonEmissionResult


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    """全域設定 Admin"""
    list_display = ['__str__', 'updated_at']
    fieldsets = (
        ('私人運具排放係數 (kg CO2e/延人公里)', {
            'fields': ('car_factor', 'electric_car_factor', 'motorcycle_factor', 'electric_motorcycle_factor')
        }),
        ('大眾運具排放係數 (kg CO2e/延人公里)', {
            'fields': ('bus_factor', 'intercity_bus_factor', 'metro_factor', 'railway_factor')
        }),
        ('再生能源減碳係數 (kg CO2e/kWh)', {
            'fields': ('solar_factor', 'wind_factor')
        }),
        ('其他減碳係數', {
            'fields': ('water_recycling_factor', 'waste_recycling_factor')
        }),
    )
    
    def has_add_permission(self, request):
        """禁止新增（Singleton）"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """禁止刪除（Singleton）"""
        return False


@admin.register(CarbonEmissionInput)
class CarbonEmissionInputAdmin(admin.ModelAdmin):
    """輸入數據 Admin"""
    list_display = ['name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本資訊', {
            'fields': ('name', 'description')
        }),
        ('混合旅次產生量', {
            'fields': ('trip_count', 'private_transport_ratio', 'public_transport_ratio', 'avg_trip_distance')
        }),
        ('私人運具旅次量 (次/年)', {
            'fields': ('car_trip_volume', 'motorcycle_trip_volume')
        }),
        ('大眾運具旅次量 (次/年)', {
            'fields': ('bus_trip_volume', 'intercity_bus_trip_volume', 
                      'metro_trip_volume', 'railway_trip_volume')
        }),
        ('私人運具延人公里', {
            'fields': ('car_passenger_km', 'electric_car_passenger_km', 
                      'motorcycle_passenger_km', 'electric_motorcycle_passenger_km')
        }),
        ('大眾運具延人公里', {
            'fields': ('bus_passenger_km', 'intercity_bus_passenger_km', 
                      'metro_passenger_km', 'railway_passenger_km')
        }),
        ('再生能源', {
            'fields': ('solar_area', 'solar_capacity_factor', 
                      'wind_area', 'wind_capacity_factor')
        }),
        ('其他', {
            'fields': ('recycled_water_volume', 'waste_recycled_volume')
        }),
    )


@admin.register(CarbonEmissionResult)
class CarbonEmissionResultAdmin(admin.ModelAdmin):
    """計算結果 Admin"""
    list_display = ['input_data', 'net_emission', 'total_emission', 'total_reduction', 'calculated_at']
    list_filter = ['calculated_at']
    search_fields = ['input_data__name']
    date_hierarchy = 'calculated_at'
    
    fieldsets = (
        ('關聯輸入數據', {
            'fields': ('input_data',)
        }),
        ('私人運具碳排量 (kg CO2e)', {
            'fields': ('car_emission', 'electric_car_emission', 
                      'motorcycle_emission', 'electric_motorcycle_emission', 
                      'private_vehicle_total')
        }),
        ('大眾運具碳排量 (kg CO2e)', {
            'fields': ('bus_emission', 'intercity_bus_emission', 
                      'metro_emission', 'railway_emission', 
                      'public_transport_total')
        }),
        ('再生能源減碳量 (kg CO2e)', {
            'fields': ('solar_reduction', 'wind_reduction', 'renewable_energy_total')
        }),
        ('其他減碳量 (kg CO2e)', {
            'fields': ('water_recycling_reduction', 'waste_recycling_reduction')
        }),
        ('總計 (kg CO2e)', {
            'fields': ('total_emission', 'total_reduction', 'net_emission')
        }),
    )
    
    def has_add_permission(self, request):
        """禁止直接新增（應透過計算產生）"""
        return False
