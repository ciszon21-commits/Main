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

class ProjectMapSearchForm(forms.Form):
    """專案地圖搜尋表單"""
    search_query = forms.CharField(
        label='專案名稱',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜尋專案名稱...',
        })
    )
    
    city = forms.ChoiceField(
        label='縣市',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    address = forms.CharField(
        label='地址',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '搜尋地址關鍵字...',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate city choices from Project model
        from .models import Project
        cities = Project.objects.exclude(city='').values_list('city', flat=True).distinct().order_by('city')
        city_choices = [('', '--- 全部縣市 ---')] + [(city, city) for city in cities]
        self.fields['city'].choices = city_choices
