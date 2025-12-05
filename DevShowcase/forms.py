from django import forms
from django.core.exceptions import ValidationError
from .models import Achievement, Comment, Category


class AchievementForm(forms.ModelForm):
    class Meta:
        model = Achievement
        fields = ['name', 'category', 'summary', 'video', 'url', 'documentation', 'developers']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入成果名稱'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': 200,
                'placeholder': '請輸入200字以內的簡介'
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'developers': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 8
            }),
        }

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            # 檢查檔案大小 (100MB = 104857600 bytes)
            if video.size > 104857600:
                raise ValidationError('影片檔案大小不能超過 100MB')
            
            # 檢查副檔名
            allowed_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
            ext = video.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f'不支援的影片格式。支援的格式：{", ".join(allowed_extensions)}')
        
        return video

    def clean_summary(self):
        summary = self.cleaned_data.get('summary')
        if len(summary) > 200:
            raise ValidationError('簡介不能超過200字')
        return summary


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '請輸入您的問題或建議...'
            })
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 5:
            raise ValidationError('留言內容至少需要5個字')
        return content


class CategoryForm(forms.ModelForm):
    """分類表單"""
    class Meta:
        model = Category
        fields = ['name', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入分類名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '請輸入分類說明（選填）'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '排序數字（數字越小越靠前）'
            }),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name.strip()) < 2:
            raise ValidationError('分類名稱至少需要2個字')
        return name

