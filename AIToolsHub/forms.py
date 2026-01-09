from django import forms
from django.core.exceptions import ValidationError
from .models import AITool, Comment, Tag


class AIToolForm(forms.ModelForm):
    """AI 工具表單"""
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '請輸入標籤，以逗號分隔（例如：AI, ChatGPT, 生產力）'
        }),
        label="標籤"
    )

    class Meta:
        model = AITool
        fields = ['name', 'category', 'image', 'url', 'summary', 'extra_info']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入工具名稱'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_category'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'maxlength': 500,
                'placeholder': '請輸入工具簡介（500字以內）'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是編輯模式，載入現有標籤
        if self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                tag.name for tag in self.instance.tags.all()
            )

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            # 檢查檔案大小 (5MB = 5242880 bytes)
            if hasattr(image, 'size') and image.size > 5242880:
                raise ValidationError('圖片檔案大小不能超過 5MB')

            # 檢查副檔名
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            if hasattr(image, 'name'):
                ext = image.name.split('.')[-1].lower()
                if ext not in allowed_extensions:
                    raise ValidationError(f'不支援的圖片格式。支援的格式：{", ".join(allowed_extensions)}')

        return image

    def clean_summary(self):
        summary = self.cleaned_data.get('summary')
        if summary and len(summary) > 500:
            raise ValidationError('簡介不能超過 500 字')
        return summary

    def save(self, commit=True):
        instance = super().save(commit=commit)

        if commit:
            # 處理標籤
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                tags = []
                for tag_name in tag_names:
                    tag, _ = Tag.objects.get_or_create(name=tag_name)
                    tags.append(tag)
                instance.tags.set(tags)
            else:
                instance.tags.clear()

        return instance


class CommentForm(forms.ModelForm):
    """留言表單"""
    class Meta:
        model = Comment
        fields = ['content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '請輸入您的問題或建議...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_anonymous': '匿名發表'
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 5:
            raise ValidationError('留言內容至少需要 5 個字')
        return content


class ReplyForm(forms.ModelForm):
    """回覆表單"""
    class Meta:
        model = Comment
        fields = ['content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '請輸入回覆...'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_anonymous': '匿名回覆'
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 2:
            raise ValidationError('回覆內容至少需要 2 個字')
        return content


class CommentEditForm(forms.ModelForm):
    """留言編輯表單"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            })
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 2:
            raise ValidationError('留言內容至少需要 2 個字')
        return content

