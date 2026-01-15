from django import forms
from .models import Project, Scene

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'cover_image', 'city', 'district', 'address_detail', 'latitude', 'longitude']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control', 'id': 'id_city'}),
            'district': forms.Select(attrs={'class': 'form-control', 'id': 'id_district'}),
            'address_detail': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': '例如：信義路五段7號',
                'id': 'id_address_detail' # Add explicit ID for JS
            }),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'id': 'id_latitude'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'id': 'id_longitude'}),
        }

class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ['title', 'image', 'pitch', 'yaw', 'hfov']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'pitch': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'yaw': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'hfov': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        }
