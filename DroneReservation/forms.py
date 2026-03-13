from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import DroneReservation, Announcement, SiteSettings, DroneReviewer, EmailTemplate, MissionRecord


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
            'usage_start_datetime': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            ),
            'usage_end_datetime': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
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
            # 結束日期不能早於開始日期（可以相同，表示只預約當天）
            if end_time < start_time:
                raise ValidationError('結束日期不能早於開始日期')

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
            'usage_start_datetime': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            ),
            'usage_end_datetime': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('usage_start_datetime')
        end_time = cleaned_data.get('usage_end_datetime')

        if start_time and end_time:
            # 結束日期不能早於開始日期（可以相同，表示只預約當天）
            if end_time < start_time:
                raise ValidationError('結束日期不能早於開始日期')

        return cleaned_data


class EmailTemplateForm(forms.ModelForm):
    """郵件模板編輯表單"""

    class Meta:
        model = EmailTemplate
        fields = ['subject_template', 'body_template']
        widgets = {
            'subject_template': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '郵件主旨'
            }),
            'body_template': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': '郵件內容'
            }),
        }
        labels = {
            'subject_template': '郵件主旨',
            'body_template': '郵件內容',
        }
        help_texts = {
            'body_template': '可用變數：{applicant_name}, {start_time}, {end_time}, {location}, {project_number}, {reason}, {reviewer_name}, {rejection_reason}, {old_start_time}, {old_end_time}',
        }


class MissionRecordForm(forms.ModelForm):
    """飛行任務紀錄表單"""
    
    # 選擇關聯的預約單（可選）
    reservation = forms.ModelChoiceField(
        queryset=DroneReservation.objects.filter(status='approved').select_related('applicant').order_by('-usage_start_datetime'),
        required=False,
        label="關聯預約單",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="選擇已核准的預約單可自動帶入部分欄位"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reservation'].label_from_instance = self._reservation_label

    @staticmethod
    def _reservation_label(obj):
        applicant_name = obj.applicant.get_full_name() or obj.applicant.username
        date_str = obj.usage_start_datetime.strftime('%Y/%m/%d')
        label = f"{applicant_name} - {date_str} - {obj.project_number}"
        
        # 檢查是否已經有建立過任務紀錄
        if obj.mission_records.exists():
            label += " [已建立紀錄]"
            
        return label

    class Meta:
        model = MissionRecord
        fields = [
            'reservation',
            'mission_start_date',
            'mission_end_date',
            'project_number',
            'project_short_name',
            'location_name',
            'latitude',
            'longitude',
            'mission_description',
            'drone_payload',
            'pilot',
            'result_location',
        ]
        widgets = {
            'mission_start_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            ),
            'mission_end_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            ),
            'project_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：0123B'
            }),
            'project_short_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：OOOOO計畫'
            }),
            'location_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：OO園區'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：24.1234',
                'step': 'any'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：120.5678',
                'step': 'any'
            }),
            'mission_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '請描述任務內容與需求，如照片影片、光達掃描'
            }),
            'drone_payload': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：SkyPro 2'
            }),
            'pilot': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '請輸入姓名'
            }),
            'result_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '檔案路徑或雲端連結'
            }),
        }
