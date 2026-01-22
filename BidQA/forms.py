from django import forms
from .models import Bid, Committee, Question


class BidForm(forms.ModelForm):
    """標案表單"""
    class Meta:
        model = Bid
        fields = ['name', 'bid_number', 'bid_date', 'status', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '請輸入標案名稱'
            }),
            'bid_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '請輸入標案編號'
            }),
            'bid_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': '請輸入標案說明'
            }),
        }


class CommitteeForm(forms.ModelForm):
    """委員表單"""
    class Meta:
        model = Committee
        fields = ['name', 'organization', 'specialty', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '請輸入委員姓名'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '請輸入所屬單位'
            }),
            'specialty': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '請輸入專長領域'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': '備註'
            }),
        }


class QuestionForm(forms.ModelForm):
    """問答表單"""
    class Meta:
        model = Question
        fields = ['question', 'answer', 'reference', 'order']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': '請輸入委員提問內容'
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 6,
                'placeholder': '請輸入回答內容'
            }),
            'reference': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': '請輸入參考資料'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 0
            }),
        }


class CommitteeSelectForm(forms.Form):
    """選擇或新增委員表單"""
    committee = forms.ModelChoiceField(
        queryset=Committee.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="選擇現有委員"
    )
    new_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '或輸入新委員姓名'
        }),
        label="新增委員"
    )
    new_organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '所屬單位'
        }),
        label="所屬單位"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        committee = cleaned_data.get('committee')
        new_name = cleaned_data.get('new_name')
        
        if not committee and not new_name:
            raise forms.ValidationError("請選擇現有委員或輸入新委員姓名")
        
        return cleaned_data


class BidFileForm(forms.Form):
    """檔案上傳表單"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-input'}),
        label="選擇檔案"
    )
    description = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '檔案說明（選填）'
        }),
        label="說明"
    )

