from django import forms
from django.utils import timezone
from django.utils.timezone import now
from .models import Expense, ExpenseCategory, Participant, ExpenseSplit


class ExpenseForm(forms.ModelForm):
    """記帳表單"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="日期"  # Removed initial value to retain original date during editing
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial=now().time,  # Keep initial time for new entries
        label="時間"
    )
    split_participants = forms.ModelMultipleChoiceField(
        queryset=Participant.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label="分攤者"
    )

    class Meta:
        model = Expense
        fields = ['date', 'time', 'item_name', 'category', 'amount', 'note', 'paid_by']
        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '品項名稱'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '備註 (選填)'}),
            'paid_by': forms.Select(attrs={'class': 'form-select'}),
        }


class CategoryForm(forms.ModelForm):
    """類型表單"""
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'icon', 'color', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-tag'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ParticipantForm(forms.ModelForm):
    """參與者表單"""
    class Meta:
        model = Participant
        fields = ['name', 'email', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ExpenseFilterForm(forms.Form):
    """篩選表單"""
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="起始日期"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="結束日期"
    )
    category = forms.ModelChoiceField(
        queryset=ExpenseCategory.objects.all(),
        required=False,
        empty_label="全部類型",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="類型"
    )
    keyword = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '搜尋品項或備註...'}),
        label="關鍵字"
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-date', '日期 (新到舊)'),
            ('date', '日期 (舊到新)'),
            ('-amount', '金額 (高到低)'),
            ('amount', '金額 (低到高)'),
            ('category__name', '類型 (A-Z)'),
        ],
        required=False,
        initial='-date',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="排序"
    )
