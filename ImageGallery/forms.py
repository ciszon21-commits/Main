from django import forms
from django.core.validators import FileExtensionValidator
from .models import Image, ImageCategory


class ImageUploadForm(forms.ModelForm):
    """圖片上傳表單"""

    class Meta:
        model = Image
        fields = ['title', 'description', 'image', 'category', 'location', 'taken_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入圖片標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '請輸入圖片描述（可選）',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/gif,image/webp'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入拍攝地點（可選）'
            }),
            'taken_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': '請選擇拍攝時間（可選）'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].validators.append(
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        )
        self.fields['category'].queryset = ImageCategory.objects.all()

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # 檢查檔案大小（10MB = 10 * 1024 * 1024 bytes）
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError('圖片檔案大小不能超過 10MB')
        return image


class CategoryForm(forms.ModelForm):
    """分類建立表單"""
    
    class Meta:
        model = ImageCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入分類名稱'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if ImageCategory.objects.filter(name=name).exists():
            raise forms.ValidationError('此分類名稱已存在')
        return name


class BulkUploadForm(forms.Form):
    """批量上傳表單 - 用於後端驗證"""
    # 不設置 widget，因為前端使用自定義的文件輸入框（支援 multiple）
    # 這個 form 主要用於後端驗證，實際文件從 request.FILES.getlist() 獲取
    images = forms.FileField(
        required=False,  # 在 view 中手動驗證
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
        ]
    )

    def clean(self):
        cleaned_data = super().clean()
        # 從 request.FILES 獲取多個文件進行驗證
        # 注意：self.files 在 form 初始化時由 Django 自動設置
        images = self.files.getlist('images')

        if not images:
            raise forms.ValidationError('請至少上傳一張圖片')

        for image in images:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError(f'圖片 {image.name} 大小超過 10MB')

        return cleaned_data


class ImageBatchEditForm(forms.ModelForm):
    """批量編輯表單"""
    class Meta:
        model = Image
        fields = ['title', 'category', 'description', 'location', 'taken_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '地點'}),
            'taken_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ImageCategory.objects.all()


class ImageEditForm(forms.ModelForm):
    """單張圖片編輯表單"""
    class Meta:
        model = Image
        fields = ['title', 'description', 'category', 'location', 'taken_at']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入圖片標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '請輸入圖片描述（可選）',
                'rows': 4
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入拍攝地點（可選）'
            }),
            'taken_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': '請選擇拍攝時間（可選）'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ImageCategory.objects.all()
