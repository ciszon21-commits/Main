"""碳排放計算服務"""
from decimal import Decimal
from .models import GlobalSettings, CarbonEmissionInput, CarbonEmissionResult


class CarbonEmissionCalculator:
    """碳排放計算器"""
    
    def __init__(self, input_data: CarbonEmissionInput):
        self.input_data = input_data
        self.settings = GlobalSettings.load()
    
    def calculate_private_vehicle_emission(self):
        """計算私人運具碳排量 (僅計算汽車與機車，電動車視為0)"""
        car = self.input_data.car_passenger_km * self.settings.car_factor
        electric_car = Decimal('0')
        motorcycle = self.input_data.motorcycle_passenger_km * self.settings.motorcycle_factor
        electric_motorcycle = Decimal('0')
        
        total = car + electric_car + motorcycle + electric_motorcycle
        
        return {
            'car': car,
            'electric_car': electric_car,
            'motorcycle': motorcycle,
            'electric_motorcycle': electric_motorcycle,
            'total': total
        }
    
    def calculate_public_transport_emission(self):
        """計算大眾運具碳排量"""
        bus = self.input_data.bus_passenger_km * self.settings.bus_factor
        intercity_bus = self.input_data.intercity_bus_passenger_km * self.settings.intercity_bus_factor
        metro = self.input_data.metro_passenger_km * self.settings.metro_factor
        railway = self.input_data.railway_passenger_km * self.settings.railway_factor
        
        total = bus + intercity_bus + metro + railway
        
        return {
            'bus': bus,
            'intercity_bus': intercity_bus,
            'metro': metro,
            'railway': railway,
            'total': total
        }
    
    def calculate_renewable_energy_reduction(self):
        """計算再生能源減碳量
        
        假設：
        - 太陽能板發電效率：每平方公尺約 0.15 kW
        - 風力發電效率：每平方公尺約 0.10 kW
        - 年度發電時數：8760 小時
        """
        # 太陽能年發電量 (kWh) = 面積 x 每平方公尺功率 x 容量因數 x 年度小時數
        solar_kwh = (self.input_data.solar_area * Decimal('0.15') * 
                     self.input_data.solar_capacity_factor * Decimal('8760'))
        solar_reduction = solar_kwh * self.settings.solar_factor
        
        # 風力年發電量 (kWh)
        wind_kwh = (self.input_data.wind_area * Decimal('0.10') * 
                    self.input_data.wind_capacity_factor * Decimal('8760'))
        wind_reduction = wind_kwh * self.settings.wind_factor
        
        total = solar_reduction + wind_reduction
        
        return {
            'solar': solar_reduction,
            'wind': wind_reduction,
            'total': total
        }
    
    def calculate_water_recycling_reduction(self):
        """計算回收水減碳量"""
        return self.input_data.recycled_water_volume * self.settings.water_recycling_factor
    
    def calculate_waste_recycling_reduction(self):
        """計算廢棄物回收減碳量"""
        return self.input_data.waste_recycled_volume * self.settings.waste_recycling_factor
    
    def calculate_mixed_trip_emission(self):
        """計算混合旅次產生量碳排
        
        說明：
        - 私人運具：使用 Trip Count * Private Ratio * Avg Distance * Car Factor
        - 大眾運具：使用 Trip Count * Public Ratio * Avg Distance * Bus Factor
        註：因無特定混合係數，暫用汽車與公車係數作為代表。
        """
        # 平均旅次長度 (km) - 強制轉為 Decimal
        avg_dist = Decimal(str(self.input_data.avg_trip_distance))
        
        # 私人旅次 (次)
        private_trips = self.input_data.trip_count * (self.input_data.private_transport_ratio / Decimal('100'))
        # 私人碳排 (kg CO2e) = 次數 * 距離 * 汽車係數
        # 強制轉為 Decimal 避免 TypeError
        car_factor = Decimal(str(self.settings.car_factor))
        mixed_private = private_trips * avg_dist * car_factor
        
        # 大眾旅次 (次)
        public_trips = self.input_data.trip_count * (self.input_data.public_transport_ratio / Decimal('100'))
        # 大眾碳排 (kg CO2e) = 次數 * 距離 * 公車係數
        bus_factor = Decimal(str(self.settings.bus_factor))
        mixed_public = public_trips * avg_dist * bus_factor
        
        total = mixed_private + mixed_public
        
        return {
            'private': mixed_private,
            'public': mixed_public,
            'total': total
        }

    def calculate_all(self):
        """執行所有計算並儲存結果"""
        # 計算混合旅次碳排 (新增)
        mixed_trip = self.calculate_mixed_trip_emission()

        # 計算私人運具碳排
        private_vehicle = self.calculate_private_vehicle_emission()
        
        # 計算大眾運具碳排
        public_transport = self.calculate_public_transport_emission()
        
        # 計算再生能源減碳
        renewable_energy = self.calculate_renewable_energy_reduction()
        
        # 計算回收水減碳
        water_reduction = self.calculate_water_recycling_reduction()
        
        # 計算廢棄物回收減碳
        waste_reduction = self.calculate_waste_recycling_reduction()
        
        # 總碳排量 (是否包含混合旅次？目前邏輯是分開展示，不重複加總)
        # 假設使用者會填寫詳細車種，混合旅次僅為參考或替代計算
        # 這裡維持原有總計邏輯，但儲存混合計算結果
        total_emission = private_vehicle['total'] + public_transport['total']
        
        # 總減碳量
        total_reduction = (renewable_energy['total'] + 
                          water_reduction + 
                          waste_reduction)
        
        # 淨碳排量
        net_emission = total_emission - total_reduction
        
        # 儲存結果
        result, created = CarbonEmissionResult.objects.update_or_create(
            input_data=self.input_data,
            defaults={
                # 混合旅次產生量 (新增)
                'mixed_private_emission': mixed_trip['private'],
                'mixed_public_emission': mixed_trip['public'],
                'mixed_total_emission': mixed_trip['total'],

                # 私人運具
                'car_emission': private_vehicle['car'],
                'electric_car_emission': private_vehicle['electric_car'],
                'motorcycle_emission': private_vehicle['motorcycle'],
                'electric_motorcycle_emission': private_vehicle['electric_motorcycle'],
                'private_vehicle_total': private_vehicle['total'],
                
                # 大眾運具
                'bus_emission': public_transport['bus'],
                'intercity_bus_emission': public_transport['intercity_bus'],
                'metro_emission': public_transport['metro'],
                'railway_emission': public_transport['railway'],
                'public_transport_total': public_transport['total'],
                
                # 再生能源
                'solar_reduction': renewable_energy['solar'],
                'wind_reduction': renewable_energy['wind'],
                'renewable_energy_total': renewable_energy['total'],
                
                # 其他減碳
                'water_recycling_reduction': water_reduction,
                'waste_recycling_reduction': waste_reduction,
                
                # 總計
                'total_emission': total_emission,
                'total_reduction': total_reduction,
                'net_emission': net_emission,
            }
        )
        
        return result
