from django import forms
from django.contrib.auth.models import User
from .models import Project, Discipline, QuantityFile, PriceInquiryFile, BudgetFile, FinalBudgetFile, PriceAdjustment

class ProjectForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_choices = [(u.id, f"{u.get_full_name() or u.username} ({u.username})") for u in User.objects.all()]
        self.fields['admins'].choices = user_choices
        
    class Meta:
        model = Project
        fields = ['name', 'code', 'description', 'admins', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'admins': forms.SelectMultiple(attrs={'class': 'select-multiple searchable-select'}),
        }

class DisciplineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_choices = [(u.id, f"{u.get_full_name() or u.username} ({u.username})") for u in User.objects.all()]
        self.fields['responsible_user'].choices = [('', '---------')] + user_choices
        self.fields['members'].choices = user_choices
        self.fields['budget_members'].choices = user_choices
    
    class Meta:
        model = Discipline
        fields = ['name', 'code', 'responsible_user', 'members', 'budget_members']
        widgets = {
            'members': forms.SelectMultiple(attrs={'class': 'select-multiple searchable-select'}),
            'responsible_user': forms.Select(attrs={'class': 'searchable-select'}),
            'budget_members': forms.SelectMultiple(attrs={'class': 'select-multiple searchable-select'}),
        }

class FileUploadForm(forms.Form):
    file = forms.FileField(label="選擇檔案")
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, label="版本說明")

class PriceAdjustmentForm(forms.ModelForm):
    class Meta:
        model = PriceAdjustment
        fields = ['discipline', 'item_code', 'item_name', 'original_price', 'adjusted_price', 'reason']
        widgets = {
            'reason': forms.Textarea(attrs={'rows': 2}),
        }


class OverallDisciplineForm(forms.ModelForm):
    """整合專業專用表單 - 只能編輯預算管理員和預算成員"""
    
    class Meta:
        model = Discipline
        fields = ['budget_manager', 'budget_members']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 準備用戶選擇列表
        user_choices = [(user.id, f"{user.get_full_name() or user.username} ({user.username})") 
                       for user in User.objects.all().order_by('username')]
        
        # 配置 budget_manager 為可搜尋下拉選單
        self.fields['budget_manager'].widget = forms.Select(
            attrs={
                'class': 'searchable-select',
                'data-placeholder': '選擇預算管理員...'
            }
        )
        self.fields['budget_manager'].choices = [('', '選擇預算管理員...')] + user_choices
        
        # 配置 budget_members 為可搜尋下拉選單（多選）
        self.fields['budget_members'].widget = forms.SelectMultiple(
            attrs={
                'class': 'searchable-select',
                'data-placeholder': '選擇預算成員...',
                'multiple': 'multiple'
            }
        )
        self.fields['budget_members'].choices = user_choices
