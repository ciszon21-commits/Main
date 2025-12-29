from django import forms
from django.forms import inlineformset_factory
from .models import Tutorial, TutorialStep, StepSnippet


class TutorialForm(forms.ModelForm):
    """教材基本資料表單"""
    class Meta:
        model = Tutorial
        fields = ['title', 'description', 'cover_image', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '輸入教材標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '教材簡介，說明此教材的內容和目標'
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': '教材標題',
            'description': '教材簡介',
            'cover_image': '封面圖片（選填）',
            'is_published': '發布教材（勾選後其他人可看到）',
        }


class TutorialStepForm(forms.ModelForm):
    """教材步驟表單"""
    class Meta:
        model = TutorialStep
        fields = ['title', 'order', 'is_expanded_default']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control step-title-input',
                'placeholder': '步驟標題'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control order-input',
                'min': 0,
                'style': 'width: 80px;'
            }),
            'is_expanded_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': '步驟標題',
            'order': '順序',
            'is_expanded_default': '預設展開',
        }


class StepSnippetForm(forms.ModelForm):
    """步驟片段表單"""
    class Meta:
        model = StepSnippet
        fields = ['snippet_type', 'order', 'content', 'image', 'language', 'caption', 'link_url', 'link_text']
        widgets = {
            'snippet_type': forms.Select(attrs={
                'class': 'form-control snippet-type-select',
                'onchange': 'toggleSnippetFields(this)'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'style': 'width: 80px;'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control snippet-content',
                'rows': 6,
                'placeholder': '輸入文字內容或程式碼...'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control snippet-image-input',
                'accept': 'image/*'
            }),
            'language': forms.Select(attrs={
                'class': 'form-control snippet-language-select'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '說明文字（選填）'
            }),
            'link_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '輸入連結網址 (例如: https://example.com)'
            }),
            'link_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '輸入顯示的連結文字'
            }),
        }
        labels = {
            'snippet_type': '類型',
            'order': '順序',
            'content': '內容',
            'image': '圖片',
            'language': '程式語言',
            'caption': '說明文字',
            'link_url': '連結網址',
            'link_text': '連結文字',
        }


# 步驟 Formset
TutorialStepFormSet = inlineformset_factory(
    Tutorial,
    TutorialStep,
    form=TutorialStepForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)

# 片段 Formset
StepSnippetFormSet = inlineformset_factory(
    TutorialStep,
    StepSnippet,
    form=StepSnippetForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)
