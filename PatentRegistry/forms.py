from django import forms
from .models import PatentApplication, PatentRebuttal, GrantedPatent, PatentAnnuity


class PatentApplicationForm(forms.ModelForm):
    """專利申請表單"""
    class Meta:
        model = PatentApplication
        fields = ['plan_number', 'outsource_number', 'item_number', 'name', 
                  'category', 'patent_firm', 'firm_case_number', 'is_public']
        widgets = {
            'plan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入計畫編號'}),
            'outsource_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入委外編號'}),
            'item_number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入專利項目名稱'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'patent_firm': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入事務所名稱'}),
            'firm_case_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入事務所案號'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PatentRebuttalForm(forms.ModelForm):
    """答辯記錄表單"""
    class Meta:
        model = PatentRebuttal
        fields = ['rebuttal_type', 'document_date', 'fee', 'notes']
        widgets = {
            'rebuttal_type': forms.Select(attrs={'class': 'form-select'}),
            'document_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '請輸入備註'}),
        }


class GrantedPatentForm(forms.ModelForm):
    """已取得專利表單"""
    class Meta:
        model = GrantedPatent
        fields = ['patent_number', 'patent_name', 'patent_period', 'description', 
                  'start_date', 'end_date', 'certificate']
        widgets = {
            'patent_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入專利編號'}),
            'patent_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入專利名稱'}),
            'patent_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '例：20年'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '請輸入專利簡述'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'certificate': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError("專利結束年月必須晚於專利起始年月")
        
        return cleaned_data


class PatentAnnuityForm(forms.ModelForm):
    """專利年費核銷表單"""
    class Meta:
        model = PatentAnnuity
        fields = ['write_off_plan_number', 'write_off_date', 'year', 'notes']
        widgets = {
            'write_off_plan_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '請輸入核銷計畫編號'}),
            'write_off_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '請輸入備註'}),
        }
