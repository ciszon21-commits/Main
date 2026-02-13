from pathlib import Path

from django import forms

from .models import CompareProject


class ProjectForm(forms.ModelForm):
    class Meta:
        model = CompareProject
        fields = ('name', 'plan_number')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '例如：A1 棟新建工程'}),
            'plan_number': forms.TextInput(
                attrs={'class': 'form-input', 'placeholder': '例如：PRJ-2026-001'}
            ),
        }


class BudgetUploadForm(forms.Form):
    budget_xml = forms.FileField(label='預算書 XML')

    def clean_budget_xml(self):
        file = self.cleaned_data['budget_xml']
        suffix = Path(file.name).suffix.lower()
        if suffix != '.xml':
            raise forms.ValidationError('預算書請上傳 .xml 檔案。')
        return file


class QuantityUploadForm(forms.Form):
    quantity_sheet = forms.FileField(label='數量計算書 Excel')

    def clean_quantity_sheet(self):
        file = self.cleaned_data['quantity_sheet']
        suffix = Path(file.name).suffix.lower()
        if suffix not in {'.xlsx', '.xls'}:
            raise forms.ValidationError('數量計算書請上傳 .xlsx 或 .xls 檔案。')
        return file


class CompareOptionsForm(forms.Form):
    quantity_tolerance = forms.FloatField(
        label='數量容差',
        initial=0.01,
        min_value=0.0,
        help_text='差異小於等於此值視為數量一致。',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.001', 'min': '0'}),
    )
    fuzzy_threshold = forms.FloatField(
        label='模糊比對門檻',
        initial=0.8,
        min_value=0.0,
        max_value=1.0,
        help_text='名稱相似度門檻，範圍 0~1。',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0', 'max': '1'}),
    )
    weighted_threshold = forms.FloatField(
        label='加權門檻',
        initial=0.75,
        min_value=0.0,
        max_value=1.0,
        help_text='加權評分門檻，範圍 0~1。',
        widget=forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0', 'max': '1'}),
    )
