from django import forms
from django.contrib.auth.models import User
from .models import (
    DevTeam, Program, ProgramDatabase, FileLocation,
    DatabaseDesignDoc, DesignTable, DesignField, DatabaseServer,
    PlatformApi, ProgramApiUsage
)


class DevTeamForm(forms.ModelForm):
    """開發團隊表單"""
    class Meta:
        model = DevTeam
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入團隊名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'ui textarea',
                'placeholder': '請輸入團隊說明（選填）',
                'rows': 3
            }),
        }


class DatabaseServerForm(forms.ModelForm):
    """資料庫伺服器表單"""
    class Meta:
        model = DatabaseServer
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '例如：SQL-PROD-01'
            }),
            'description': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '伺服器說明（選填）'
            }),
        }


class ProgramForm(forms.ModelForm):
    """程式表單"""
    class Meta:
        model = Program
        fields = [
            'name', 'program_type', 'english_name', 'url',
            'dev_tool', 'git_url', 'developers', 'maintainers'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入程式名稱'
            }),
            'program_type': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'english_name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入英文名稱（選填）'
            }),
            'url': forms.URLInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入網址（選填）'
            }),
            'dev_tool': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入開發工具，例如：Visual Studio 2022'
            }),
            'git_url': forms.URLInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入 Git 網址（選填）'
            }),
            'developers': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '開發者，多位請用逗號分隔'
            }),
            'maintainers': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '維運者，多位請用逗號分隔'
            }),
        }


class ProgramDatabaseForm(forms.ModelForm):
    """程式使用資料庫表單"""
    class Meta:
        model = ProgramDatabase
        fields = ['server', 'database_name', 'table_name', 'access_permission']
        widgets = {
            'server': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'database_name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入資料庫名稱'
            }),
            'table_name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入資料表名稱'
            }),
            'access_permission': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
        }


class FileLocationForm(forms.ModelForm):
    """存取檔案位置表單"""
    class Meta:
        model = FileLocation
        fields = ['path', 'description']
        widgets = {
            'path': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入檔案路徑'
            }),
            'description': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '說明（選填）'
            }),
        }


class DatabaseDesignDocForm(forms.ModelForm):
    """資料庫設計文件表單"""
    class Meta:
        model = DatabaseDesignDoc
        fields = ['name', 'doc_type', 'description', 'django_model_code', 'mermaid_content']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入文件名稱'
            }),
            'doc_type': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'description': forms.Textarea(attrs={
                'class': 'ui textarea',
                'placeholder': '請輸入說明（選填）',
                'rows': 2
            }),
            'django_model_code': forms.Textarea(attrs={
                'class': 'ui textarea code-editor',
                'placeholder': '貼上 Django Model 程式碼（Django Model 模式使用）',
                'rows': 15,
                'style': 'font-family: monospace;'
            }),
            'mermaid_content': forms.Textarea(attrs={
                'class': 'ui textarea code-editor',
                'placeholder': '貼上 Mermaid ER Diagram 程式碼（Mermaid 模式使用）',
                'rows': 15,
                'style': 'font-family: monospace;'
            }),
        }


class DesignTableForm(forms.ModelForm):
    """設計資料表表單"""
    class Meta:
        model = DesignTable
        fields = ['table_name', 'description', 'order']
        widgets = {
            'table_name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '請輸入資料表名稱'
            }),
            'description': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '說明（選填）'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'ui input',
                'style': 'width: 80px;'
            }),
        }


class DesignFieldForm(forms.ModelForm):
    """設計欄位表單"""
    fk_reference_table = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'ui input',
            'placeholder': '外鍵參考表'
        })
    )
    
    class Meta:
        model = DesignField
        fields = [
            'field_name', 'data_type', 'description',
            'is_primary_key', 'is_foreign_key', 'fk_reference_table',
            'is_nullable', 'default_value', 'order'
        ]
        widgets = {
            'field_name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '欄位名稱'
            }),
            'data_type': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'description': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '說明'
            }),
            'default_value': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '預設值'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'ui input',
                'style': 'width: 60px;'
            }),
        }


# Formsets for inline editing
ProgramDatabaseFormSet = forms.inlineformset_factory(
    Program, ProgramDatabase, form=ProgramDatabaseForm,
    extra=1, can_delete=True
)

FileLocationFormSet = forms.inlineformset_factory(
    Program, FileLocation, form=FileLocationForm,
    extra=1, can_delete=True
)

DesignTableFormSet = forms.inlineformset_factory(
    DatabaseDesignDoc, DesignTable, form=DesignTableForm,
    extra=1, can_delete=True
)

DesignFieldFormSet = forms.inlineformset_factory(
    DesignTable, DesignField, form=DesignFieldForm,
    extra=1, can_delete=True
)


class PlatformApiForm(forms.ModelForm):
    """平台 API 表單"""
    class Meta:
        model = PlatformApi
        fields = ['name', 'api_endpoint', 'description', 'auth_type', 'documentation_url']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '例如：PMIS API、ERP API'
            }),
            'api_endpoint': forms.URLInput(attrs={
                'class': 'ui input',
                'placeholder': '例如：https://api.example.com'
            }),
            'description': forms.Textarea(attrs={
                'class': 'ui textarea',
                'placeholder': '平台 API 說明（選填）',
                'rows': 2
            }),
            'auth_type': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'documentation_url': forms.URLInput(attrs={
                'class': 'ui input',
                'placeholder': 'API 文件連結（選填）'
            }),
        }


class ProgramApiUsageForm(forms.ModelForm):
    """程式使用平台 API 表單"""
    class Meta:
        model = ProgramApiUsage
        fields = ['platform_api', 'api_path', 'access_type', 'description']
        widgets = {
            'platform_api': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'api_path': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '例如：/api/v1/projects'
            }),
            'access_type': forms.Select(attrs={
                'class': 'ui dropdown'
            }),
            'description': forms.TextInput(attrs={
                'class': 'ui input',
                'placeholder': '說明（選填）'
            }),
        }


ProgramApiUsageFormSet = forms.inlineformset_factory(
    Program, ProgramApiUsage, form=ProgramApiUsageForm,
    extra=1, can_delete=True
)
