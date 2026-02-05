"""表單定義"""
from django import forms
from .models import CarbonEmissionInput, GlobalSettings


class CarbonEmissionInputForm(forms.ModelForm):
    """碳排放輸入表單"""
    
    class Meta:
        model = CarbonEmissionInput
        fields = [
            'name', 'description', 
            'trip_count', 'private_transport_ratio', 'public_transport_ratio',
            'car_trip_volume', 'motorcycle_trip_volume',
            'bus_trip_volume', 'intercity_bus_trip_volume', 'metro_trip_volume', 'railway_trip_volume',
            'solar_area', 'solar_capacity_factor',
            'wind_area', 'wind_capacity_factor',
            'recycled_water_volume', 'waste_recycled_volume'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：台北市2026年碳排放計算'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '說明此次計算的目的或相關背景資訊'
            }),
            
            # BC1 混合旅次產生量
            'trip_count': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '1',
                'placeholder': '請輸入年份混合旅次量'
            }),
            'private_transport_ratio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'max': '100',
                'step': '0.01',
                'placeholder': '%'
            }),
            'public_transport_ratio': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'max': '100',
                'step': '0.01',
                'placeholder': '%'
            }),
            
            # 私人運具旅次量
            'car_trip_volume': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '請輸入年旅次量 (次/年)'
            }),
            'motorcycle_trip_volume': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '請輸入年旅次量 (次/年)'
            }),
            
            # 大眾運具旅次量
            'bus_trip_volume': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '請輸入年旅次量 (次/年)'
            }),
            'intercity_bus_trip_volume': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '請輸入年旅次量 (次/年)'
            }),
            'metro_trip_volume': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '請輸入年旅次量 (次/年)'
            }),
            'railway_trip_volume': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0', 
                'step': '0.01',
                'placeholder': '請輸入年旅次量 (次/年)'
            }),
            
            # 再生能源
            'solar_area': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'solar_capacity_factor': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '1', 'step': '0.0001'}),
            'wind_area': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'wind_capacity_factor': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '1', 'step': '0.0001'}),
            
            # 其他
            'recycled_water_volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'waste_recycled_volume': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }


class GlobalSettingsForm(forms.ModelForm):
    """全域設定表單"""
    
    class Meta:
        model = GlobalSettings
        exclude = ['updated_at']
        widgets = {
            'car_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'electric_car_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'motorcycle_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'electric_motorcycle_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'bus_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'intercity_bus_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'metro_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'railway_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'solar_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'wind_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'water_recycling_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'waste_recycling_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
        }
