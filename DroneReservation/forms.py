from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import DroneReservation, Announcement, SiteSettings, DroneReviewer


class ReservationForm(forms.ModelForm):
    """預約申請表單"""

    class Meta:
        model = DroneReservation
        fields = [
            'phone_extension',
            'project_number',
            'reason',
            'usage_start_datetime',
            'usage_end_datetime',
            'location',
            'notes'
        ]
        widgets = {
            'phone_extension': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：01234'
            }),
            'project_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入計畫編號'
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '請說明申請理由'
            }),
            'usage_start_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'usage_end_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入使用地點'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '其他需要說明的事項（選填）'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('usage_start_datetime')
        end_time = cleaned_data.get('usage_end_datetime')

        if start_time and end_time:
            # 結束時間必須在開始時間之後
            if end_time <= start_time:
                raise ValidationError('結束時間必須在開始時間之後')

            # 開始時間不能是過去的時間（新申請時）
            if not self.instance.pk and start_time < timezone.now():
                raise ValidationError('開始時間不能是過去的時間')

        return cleaned_data


class ReviewForm(forms.Form):
    """簽核表單"""
    ACTION_CHOICES = [
        ('approve', '核准'),
        ('reject', '拒絕'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="簽核結果"
    )
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '請說明拒絕理由'
        }),
        required=False,
        label="拒絕理由"
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')

        if action == 'reject' and not rejection_reason:
            raise ValidationError({'rejection_reason': '拒絕時必須說明理由'})

        return cleaned_data


class AnnouncementForm(forms.ModelForm):
    """公告表單"""

    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_pinned', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入公告標題'
            }),
            'content': CKEditor5Widget(
                attrs={'class': 'django_ckeditor_5'},
                config_name='extends'
            ),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': '標題',
            'content': '內容',
            'is_pinned': '置頂',
            'is_active': '啟用',
        }


class SiteSettingsForm(forms.ModelForm):
    """網站設定表單"""

    class Meta:
        model = SiteSettings
        fields = ['banner_subtitle']
        widgets = {
            'banner_subtitle': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '請輸入 Banner 副標題',
                'rows': 3
            }),
        }


class ReviewerCancelForm(forms.Form):
    """簽核人取消核准表單"""
    cancellation_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '請說明取消核准的理由'
        }),
        required=True,
        label="取消理由"
    )


class ReviewerTimeEditForm(forms.ModelForm):
    """審核人編輯預約時間表單"""

    class Meta:
        model = DroneReservation
        fields = ['usage_start_datetime', 'usage_end_datetime']
        widgets = {
            'usage_start_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60'
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'usage_end_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'step': '60'
                },
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('usage_start_datetime')
        end_time = cleaned_data.get('usage_end_datetime')

        if start_time and end_time:
            if end_time <= start_time:
                raise ValidationError('結束時間必須在開始時間之後')

        return cleaned_data
