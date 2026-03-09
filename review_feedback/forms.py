from django import forms
from django.contrib.auth import get_user_model
from .models import ReviewFeedback, Project

User = get_user_model()


class ReviewFeedbackForm(forms.ModelForm):
    IS_CORRECT_CHOICES = [
        ("", ""),
        ("true", "分類正確"),
        ("false", "分類錯誤"),
    ]

    is_correct = forms.ChoiceField(
        choices=IS_CORRECT_CHOICES,
        required=False,
        label="分類判定",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = ReviewFeedback
        fields = ["is_correct", "correct_classification", "feedback_reason", "additional_description"]
        widgets = {
            "correct_classification": forms.TextInput(attrs={
                "class": "fb-text",
                "placeholder": "請輸入正確的分類名稱",
            }),
            "feedback_reason": forms.Textarea(attrs={
                "class": "fb-textarea",
                "rows": 2,
                "placeholder": "備註說明（選填）…",
            }),
            "additional_description": forms.Textarea(attrs={
                "class": "fb-textarea",
                "rows": 2,
                "placeholder": "補充手段描述，以利後續資料訓練…",
            }),
        }
        labels = {
            "correct_classification": "正確分類",
            "feedback_reason": "備註說明",
            "additional_description": "手段描述擴充",
        }

    def clean_is_correct(self):
        val = self.cleaned_data.get("is_correct")
        if val == "true":
            return True
        elif val == "false":
            return False
        return None


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError(self.error_messages["required"])
            return []
        single_clean = super().clean
        return [single_clean(f, initial) for f in data]


class ComparisonFileUploadForm(forms.Form):
    """前端上傳 JSON 比對結果檔"""
    json_file = MultipleFileField(
        label="JSON 比對檔",
        widget=MultipleFileInput(attrs={
            "accept": ".json",
            "class": "file-input",
            "id": "id_json_file",
            "multiple": True,
        }),
        help_text="請選擇 *-paged_filter_entities.json 格式的檔案（可多選）",
    )


class ProjectCreateForm(forms.ModelForm):
    """新增專案，含管理員與專家設定（由前端搜尋介面選取，以隱藏欄位提交）"""
    admins = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label="專案管理員",
    )
    experts = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label="專家審查員",
    )

    class Meta:
        model = Project
        fields = ["name", "description", "admins", "experts"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "輸入專案名稱",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "輸入專案說明（選填）",
            }),
        }
        labels = {
            "name": "專案名稱",
            "description": "專案說明",
        }


class ProjectPdfUploadForm(forms.ModelForm):
    """上傳 / 更換專案的 PDF 報告書"""
    class Meta:
        model = Project
        fields = ["pdf_file"]
        widgets = {
            "pdf_file": forms.FileInput(attrs={
                "accept": ".pdf",
                "class": "file-input",
                "id": "id_pdf_file",
            }),
        }
        labels = {
            "pdf_file": "PDF 報告書",
        }
