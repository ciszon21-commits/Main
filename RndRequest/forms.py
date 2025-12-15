from django import forms
from .models import RndRequest


class RndRequestForm(forms.ModelForm):
    """研發需求提案表單"""
    
    class Meta:
        model = RndRequest
        fields = [
            'title',
            'demand_quantity',
            'data_source',
            'processing_flow',
            'expected_outcome',
            'priority_level',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入需求主題'
            }),
            'demand_quantity': forms.Textarea(attrs={
                'class': 'ui textarea',
                'rows': 4,
                'placeholder': '例如：每周預計使用 4 小時，需求人數約 10 人'
            }),
            'data_source': forms.Textarea(attrs={
                'class': 'ui textarea',
                'rows': 4,
                'placeholder': '例如：資料來自 ERP 系統的出貨報表'
            }),
            'expected_outcome': forms.Textarea(attrs={
                'class': 'ui textarea',
                'rows': 4,
                'placeholder': '例如：可節省每周 5 小時人工作業時間'
            }),
            'priority_level': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 設定必填欄位標籤
        self.fields['title'].required = True
        self.fields['demand_quantity'].required = True
        self.fields['data_source'].required = True
        self.fields['processing_flow'].required = True
