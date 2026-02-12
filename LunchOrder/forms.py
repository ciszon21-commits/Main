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


class MenuImageForm(forms.Form):
    """菜單圖片上傳表單"""
    image = forms.FileField(
        label="選擇菜單圖片",
        help_text="支援 JPG, PNG 格式",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        required=False  # 允許只更新菜單項目而不換圖
    )
    name = forms.CharField(
        label="餐廳名稱",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '餐廳名稱'})
    )
    phone = forms.CharField(
        label="電話",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '電話號碼'})
    )
    address = forms.CharField(
        label="地址",
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '餐廳地址'})
    )


class MenuItemForm(forms.ModelForm):
    """菜單項目表單"""
    class Meta:
        model = MenuItem
        fields = ['name', 'price', 'category', 'is_available']
        labels = {
            'name': '品項名稱',
            'price': '價格',
            'category': '分類',
            'is_available': '供應中',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '餐點名稱'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RestaurantCreateForm(forms.ModelForm):
    """新增便當店表單"""
    image = forms.FileField(
        label="菜單圖片",
        help_text="上傳菜單照片 (JPG, PNG)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        required=True
    )

    class Meta:
        model = Restaurant
        fields = ['name', 'phone', 'address']
        labels = {
            'name': '店名',
            'phone': '電話',
            'address': '地址',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入便當店名稱'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '選填'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '選填'}),
        }
