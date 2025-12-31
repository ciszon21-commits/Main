"""
EVCodeSigning Forms - 簽章管理表單
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import SigningRequest, SigningFile
from .validators import validate_signing_file, get_allowed_extensions_display


class SigningRequestForm(forms.ModelForm):
    """簽章申請表單"""
    
    class Meta:
        model = SigningRequest
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：專案 A 安裝程式簽章',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '請描述此次簽章申請的用途、專案名稱、預計發布時間等相關資訊...',
            }),
        }


class SignedFileUploadForm(forms.Form):
    """簽章後檔案上傳表單"""
    
    signed_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.exe,.msi,.dll,.cab,.ocx,.xpi,.axp,.jar,.air,.airi',
        }),
        label="簽章後檔案"
    )

    def clean_signed_file(self):
        """驗證簽章後的檔案"""
        signed_file = self.cleaned_data.get('signed_file')
        if signed_file:
            validate_signing_file(signed_file)
        return signed_file


class RejectForm(forms.Form):
    """退回申請表單"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '請說明退回原因，例如：檔案格式不正確、缺少必要資訊等...',
        }),
        label="退回原因",
        min_length=10,
        error_messages={
            'required': '請填寫退回原因',
            'min_length': '退回原因至少需要 10 個字元',
        }
    )
