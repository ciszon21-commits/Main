from django import forms
from .models import EquipmentCategory, XrEquipment, XrSupportRecord, GoProRentalRecord, XrBulkItem, XrRentalRecord

class EquipmentCategoryForm(forms.ModelForm):
    class Meta:
        model = EquipmentCategory
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '如: VR 頭盔'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-headset'}),
        }

class XrEquipmentForm(forms.ModelForm):
    class Meta:
        model = XrEquipment
        fields = '__all__'
        widgets = {
            'section': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class XrSupportRecordForm(forms.ModelForm):
    class Meta:
        model = XrSupportRecord
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nature': forms.Select(attrs={'class': 'form-select'}),
            'equipment_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'support_people': forms.NumberInput(attrs={'class': 'form-control'}),
            'event_scale': forms.NumberInput(attrs={'class': 'form-control'}),
            'rented_equipments': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'}),
        }

class GoProRentalRecordForm(forms.ModelForm):
    class Meta:
        model = GoProRentalRecord
        fields = '__all__'
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'borrower': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'equipment': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class XrBulkItemForm(forms.ModelForm):
    class Meta:
        model = XrBulkItem
        fields = '__all__'
        widgets = {
            'section': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'total_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class XrRentalRecordForm(forms.ModelForm):
    class Meta:
        model = XrRentalRecord
        fields = [
            'activity_date', 'rental_start', 'rental_end', 
            'department', 'borrower_name', 'borrower_id', 
            'activity_name', 'reason', 'equipments', 'bulk_items'
        ]
        widgets = {
            'activity_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rental_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'rental_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '租借單位'}),
            'borrower_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '姓名'}),
            'borrower_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '員工編號'}),
            'activity_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '填寫活動或專案名稱'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '請簡述租借用途'}),
            'equipments': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'}),
            'bulk_items': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple'}),
        }
