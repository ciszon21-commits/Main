from django import forms
from django.utils import timezone
from .models import LunchOrder, Restaurant, MenuItem


class LunchOrderForm(forms.ModelForm):
    """訂單表單 - 直接顯示菜單，無需選店"""

    class Meta:
        model = LunchOrder
        fields = ['menu_item', 'quantity', 'employee_name', 'notes']
        widgets = {
            'menu_item': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'id': 'menu-item-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'employee_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入您的姓名'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '備註 (選填)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        # 直接載入所有可用品項（預設第一間店的菜單）
        default_restaurant = Restaurant.objects.filter(is_active=True).first()
        if default_restaurant:
            self.fields['menu_item'].queryset = MenuItem.objects.filter(
                restaurant=default_restaurant,
                is_available=True
            ).order_by('price')
        else:
            self.fields['menu_item'].queryset = MenuItem.objects.filter(is_available=True)
        
        self.fields['menu_item'].label = "選擇餐點"
        self.fields['quantity'].label = "數量"
        self.fields['employee_name'].label = "您的姓名"
        self.fields['notes'].label = "備註"
