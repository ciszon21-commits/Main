from django import forms
from .models import Scene, Asset3D, Panorama, InfoCard

class SceneForm(forms.ModelForm):
    new_background_image = forms.ImageField(required=False, label="直接上傳全景圖 (若選擇此項將忽略上方選單)")

    class Meta:
        model = Scene
        fields = ['title', 'description', 'background']

class Asset3DForm(forms.ModelForm):
    class Meta:
        model = Asset3D
        fields = ['title', 'file']

class PanoramaForm(forms.ModelForm):
    class Meta:
        model = Panorama
        fields = ['title', 'image']

class InfoCardForm(forms.ModelForm):
    class Meta:
        model = InfoCard
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }
