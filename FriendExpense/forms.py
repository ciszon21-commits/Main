from django import forms
from .models import ExpenseGroup, Member, Expense, ExpenseSplit, ExpenseCategory


class ExpenseGroupForm(forms.ModelForm):
    """群組表單"""
    class Meta:
        model = ExpenseGroup
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '輸入群組名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '群組說明（選填）',
                'rows': 3
            }),
        }


class MemberForm(forms.ModelForm):
    """成員表單"""
    class Meta:
        model = Member
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '輸入成員名稱'
            }),
        }


class ExpenseForm(forms.ModelForm):
    """消費記錄表單"""
    category_name = forms.CharField(
        required=False,
        label='分類',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'list': 'category-list',
            'placeholder': '選擇或輸入新分類'
        })
    )
    split_members = forms.ModelMultipleChoiceField(
        queryset=Member.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'member-checkbox'}),
        label='分攤對象',
        required=True
    )
    split_equally = forms.BooleanField(
        initial=True,
        required=False,
        label='平均分攤',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Expense
        fields = ['description', 'amount', 'paid_by', 'expense_date', 'receipt', 'notes']
        widgets = {
            'paid_by': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '例如：晚餐、計程車費'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01',
                'min': '0'
            }),
            'expense_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'receipt': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '備註（選填）',
                'rows': 2
            }),
        }

    def __init__(self, *args, group=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        if group:
            members = group.members.all()
            self.fields['paid_by'].queryset = members
            self.fields['split_members'].queryset = members
            # 預設選中所有成員
            if not self.instance.pk:
                self.fields['split_members'].initial = members
            elif self.instance.category:
                self.fields['category_name'].initial = self.instance.category.name

    def save(self, commit=True):
        expense = super().save(commit=False)
        category_name = self.cleaned_data.get('category_name')
        
        if category_name:
            category_name = category_name.strip()
            # 取得或建立分類 (針對該群組)
            # 因為我們在 init 將 group 存入 self.group，但 update 時可能從 instance 拿
            group = self.group or expense.group
            
            category, created = ExpenseCategory.objects.get_or_create(
                group=group,
                name=category_name
            )
            expense.category = category
        else:
            expense.category = None

        if commit:
            expense.save()
            self.save_m2m() # 確保多對多關係正確儲存
            
        return expense
