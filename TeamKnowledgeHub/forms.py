from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import KnowledgeTeam, Topic, Category, KnowledgeItem, ItemComment


class KnowledgeTeamForm(forms.ModelForm):
    """知識團隊表單"""
    class Meta:
        model = KnowledgeTeam
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入團隊名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'ui textarea',
                'rows': 4,
                'placeholder': '請輸入團隊說明（選填）'
            }),
        }


class TopicForm(forms.ModelForm):
    """主題表單"""
    class Meta:
        model = Topic
        fields = ['name', 'description', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入主題名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'ui textarea',
                'rows': 3,
                'placeholder': '請輸入主題說明（選填）'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'ui input',
                'placeholder': '排序序號'
            }),
        }


class CategoryForm(forms.ModelForm):
    """分類表單"""
    class Meta:
        model = Category
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入分類名稱'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'ui input',
                'placeholder': '排序序號'
            }),
        }



class KnowledgeItemForm(forms.ModelForm):
    """知識項目表單"""
    class Meta:
        model = KnowledgeItem
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入標題'
            }),
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='extends'
            ),
        }


class ItemCommentForm(forms.ModelForm):
    """項目留言表單"""
    class Meta:
        model = ItemComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'ui textarea',
                'rows': 3,
                'placeholder': '請輸入留言內容...'
            }),
        }
