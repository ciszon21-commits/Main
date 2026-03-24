from django import forms
from .models import FoundationExcavation


class FoundationForm(forms.ModelForm):
    class Meta:
        model = FoundationExcavation
        fields = [
            'project_code', 'bridge_name', 'bridge_id',
            'column_base_el', 'h1_thickness', 'c_pc_thickness',
            'B1', 'B2', 'L1', 'L2',
            'el_l1_start', 'el_l1_end', 'el_l2_start', 'el_l2_end',
            'el_b1_start', 'el_b1_end', 'el_b2_start', 'el_b2_end',
            'offset_dist', 'd1_manual',
            'excavation_plan', 'excavation_section',
            'skew_angle', 'note',
        ]
        widgets = {
            'project_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '例：P2024-001'}),
            'bridge_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '例：某某橋'}),
            'bridge_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '例：F1-L'}),
            'column_base_el': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'h1_thickness': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'c_pc_thickness': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'B1': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'B2': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'L1': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'L2': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_l1_start': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_l1_end': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_l2_start': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_l2_end': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_b1_start': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_b1_end': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_b2_start': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'el_b2_end': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'offset_dist': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'd1_manual': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'excavation_plan': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '例：P-1'}),
            'excavation_section': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '例：S-1'}),
            'skew_angle': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'note': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': '備註說明'}),
        }


class CSVImportForm(forms.Form):
    project_code = forms.CharField(
        label="計畫編號（備用）",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'CSV無編號時使用'})
    )
    bridge_name = forms.CharField(
        label="橋梁名稱（備用）",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'CSV無橋名時使用'})
    )
    csv_file = forms.FileField(
        label="選擇 CSV 檔案",
        widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv'})
    )
