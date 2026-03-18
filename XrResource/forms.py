from django import forms
from .models import EquipmentCategory, XrEquipment, GoProAccessory, VrComputer, XrSupportRecord, GoProRentalRecord

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
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class GoProAccessoryForm(forms.ModelForm):
    class Meta:
        model = GoProAccessory
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'rented_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class VrComputerForm(forms.ModelForm):
    class Meta:
        model = VrComputer
        fields = '__all__'
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'local_account': forms.TextInput(attrs={'class': 'form-control'}),
            'local_password': forms.TextInput(attrs={'class': 'form-control'}),
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
