from django import forms
from django.core.exceptions import ValidationError
from .models import Course


class CourseForm(forms.ModelForm):
    """課程建立/編輯表單"""
    
    class Meta:
        model = Course
        fields = [
            'title',
            'description',
            'course_datetime',
            'registration_start',
            'registration_end',
            'pdf_file',
            'max_participants',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入課程標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '請輸入課程說明'
            }),
            'course_datetime': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'registration_start': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'registration_end': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'pdf_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '留空表示不限制人數',
                'min': '1'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        registration_start = cleaned_data.get('registration_start')
        registration_end = cleaned_data.get('registration_end')
        course_datetime = cleaned_data.get('course_datetime')
        
        if registration_start and registration_end:
            if registration_end <= registration_start:
                raise ValidationError('報名截止時間必須晚於報名開始時間')
        
        if course_datetime and registration_start:
            if course_datetime <= registration_start:
                raise ValidationError('上課時間應該晚於報名開始時間')
        
        return cleaned_data
