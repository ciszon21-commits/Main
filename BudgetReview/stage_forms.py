from django import forms
from django.contrib.auth.models import User
from .models import Project, Discipline, Stage

class StageForm(forms.ModelForm):
    """標案階段表單"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果是編輯模式且有 deadline，格式化為 datetime-local 需要的格式
        if self.instance and self.instance.pk and self.instance.deadline:
            # 將 UTC 時間轉換為本地時區（台灣 UTC+8）
            from django.utils import timezone
            import pytz
            
            # 取得 Django 設定的時區
            local_tz = pytz.timezone('Asia/Taipei')
            local_deadline = self.instance.deadline.astimezone(local_tz)
            
            # datetime-local 需要格式: YYYY-MM-DDTHH:MM
            self.initial['deadline'] = local_deadline.strftime('%Y-%m-%dT%H:%M')
    
    class Meta:
        model = Stage
        fields = ['name', 'order', 'deadline', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'datetime-input'
            }),
        }
        labels = {
            'name': '階段名稱',
            'order': '階段順序',
            'deadline': '檔案提送截止時間',
            'description': '階段說明',
        }
