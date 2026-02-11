"""
EngineerRPG Forms - 更新版本
添加技能樹和課程管理表單
"""

from django import forms
from .models import Question, SkillNode, Course, CharacterClass


class QuestionForm(forms.ModelForm):
    """題目表單"""
    
    # 額外欄位用於輸入選項
    option_a = forms.CharField(
        label='選項 A',
        required=False,
        widget=forms.TextInput(attrs={'class': 'rpg-input', 'placeholder': '選項 A'})
    )
    option_b = forms.CharField(
        label='選項 B',
        required=False,
        widget=forms.TextInput(attrs={'class': 'rpg-input', 'placeholder': '選項 B'})
    )
    option_c = forms.CharField(
        label='選項 C',
        required=False,
        widget=forms.TextInput(attrs={'class': 'rpg-input', 'placeholder': '選項 C'})
    )
    option_d = forms.CharField(
        label='選項 D',
        required=False,
        widget=forms.TextInput(attrs={'class': 'rpg-input', 'placeholder': '選項 D'})
    )
    answer = forms.CharField(
        label='正確答案',
        help_text='單選填 A/B/C/D，多選填 A,B,C，是非填 TRUE/FALSE',
        widget=forms.TextInput(attrs={'class': 'rpg-input', 'placeholder': '例如: A 或 A,B,C'})
    )
    
    class Meta:
        model = Question
        fields = ['content', 'question_type', 'explanation', 'difficulty', 'tags', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'rpg-input',
                'rows': 4,
                'placeholder': '請輸入題目內容...'
            }),
            'question_type': forms.Select(attrs={'class': 'rpg-input'}),
            'explanation': forms.Textarea(attrs={
                'class': 'rpg-input',
                'rows': 3,
                'placeholder': '答案解析...'
            }),
            'difficulty': forms.Select(attrs={'class': 'rpg-input'}),
            'tags': forms.TextInput(attrs={
                'class': 'rpg-input',
                'placeholder': '多個標籤用逗號分隔，例如：鋼筋,法規,職安'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'rpg-checkbox'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # 處理選項 - 轉換為 JSON
        options = {}
        if self.cleaned_data.get('option_a'):
            options['A'] = self.cleaned_data['option_a']
        if self.cleaned_data.get('option_b'):
            options['B'] = self.cleaned_data['option_b']
        if self.cleaned_data.get('option_c'):
            options['C'] = self.cleaned_data['option_c']
        if self.cleaned_data.get('option_d'):
            options['D'] = self.cleaned_data['option_d']
        
        instance.options = options
        
        # 處理答案 - 轉換為 JSON
        answer = self.cleaned_data['answer'].strip().upper()
        if ',' in answer:
            # 多選
            instance.correct_answer = [a.strip() for a in answer.split(',')]
        else:
            # 單選或是非
            instance.correct_answer = answer
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class QuestionImportForm(forms.Form):
    """題目批次匯入表單"""
    
    file = forms.FileField(
        label='選擇檔案',
        help_text='支援 CSV 或 Excel (.xlsx) 格式，檔案大小限制 5MB',
        widget=forms.FileInput(attrs={
            'class': 'rpg-input',
            'accept': '.csv,.xlsx'
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # 檢查檔案類型
            if not file.name.endswith(('.csv', '.xlsx')):
                raise forms.ValidationError('只支援 CSV 或 Excel (.xlsx) 格式')
            
            # 檢查檔案大小 (限制 5MB)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('檔案大小不能超過 5MB')
        
        return file


class SkillNodeForm(forms.ModelForm):
    """技能節點表單"""
    
    class Meta:
        model = SkillNode
        fields = [
            'name', 'description', 'node_type', 'character_class',
            'parent_skills', 'exp_reward', 'position_x', 'position_y'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'rpg-input',
                'placeholder': '技能名稱'
            }),
            'description': forms.Textarea(attrs={
                'class': 'rpg-input',
                'rows': 4,
                'placeholder': '技能描述...'
            }),
            'node_type': forms.Select(attrs={'class': 'rpg-input'}),
            'character_class': forms.Select(attrs={
                'class': 'rpg-input',
                'required': False
            }),
            'parent_skills': forms.CheckboxSelectMultiple(),
            'exp_reward': forms.NumberInput(attrs={
                'class': 'rpg-input',
                'min': 0
            }),
            'position_x': forms.NumberInput(attrs={
                'class': 'rpg-input',
                'placeholder': 'X 座標'
            }),
            'position_y': forms.NumberInput(attrs={
                'class': 'rpg-input',
                'placeholder': 'Y 座標'
            }),
        }
        labels = {
            'name': '技能名稱',
            'description': '技能描述',
            'node_type': '節點類型',
            'character_class': '所屬職業',
            'parent_skills': '前置技能',
            'exp_reward': '完成獎勵經驗值',
            'position_x': 'X 座標',
            'position_y': 'Y 座標',
        }
        help_texts = {
            'character_class': 'ROOT 類型可為空，表示所有職業共用',
            'parent_skills': '選擇此技能的前置技能（需先完成才能學習）',
        }


class CourseForm(forms.ModelForm):
    """課程表單"""
    
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'content_type', 'content_url',
            'content_file', 'skill_nodes', 'duration_minutes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'rpg-input',
                'placeholder': '課程標題'
            }),
            'description': forms.Textarea(attrs={
                'class': 'rpg-input',
                'rows': 3,
                'placeholder': '課程描述...'
            }),
            'content_type': forms.Select(attrs={'class': 'rpg-input'}),
            'content_url': forms.URLInput(attrs={
                'class': 'rpg-input',
                'placeholder': 'https://...'
            }),
            'content_file': forms.FileInput(attrs={'class': 'rpg-input'}),
            'skill_nodes': forms.CheckboxSelectMultiple(),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'rpg-input',
                'min': 1
            }),
        }
        labels = {
            'title': '課程標題',
            'description': '課程描述',
            'content_type': '內容類型',
            'content_url': '內容網址',
            'content_file': '內容檔案',
            'skill_nodes': '關聯技能',
            'duration_minutes': '課程時長（分鐘）',
        }


class UserLoginForm(forms.Form):
    """使用者登入表單"""
    username = forms.CharField(
        label='使用者名稱',
        widget=forms.TextInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請輸入使用者名稱'
        })
    )
    password = forms.CharField(
        label='密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請輸入密碼'
        })
    )


class UserRegistrationForm(forms.Form):
    """使用者註冊表單"""
    username = forms.CharField(
        label='使用者名稱',
        widget=forms.TextInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請輸入使用者名稱'
        })
    )
    email = forms.EmailField(
        label='電子郵件',
        widget=forms.EmailInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請輸入電子郵件'
        })
    )
    employee_id = forms.CharField(
        label='員工編號',
        widget=forms.TextInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請輸入員工編號'
        })
    )
    character_class = forms.ModelChoiceField(
        queryset=CharacterClass.objects.all(),
        label='選擇職業',
        widget=forms.RadioSelect(attrs={
            'class': 'rpg-input'
        }),
        empty_label=None
    )
    password = forms.CharField(
        label='密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請輸入密碼'
        })
    )
    confirm_password = forms.CharField(
        label='確認密碼',
        widget=forms.PasswordInput(attrs={
            'class': 'rpg-input',
            'placeholder': '請再次輸入密碼'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("兩次輸入的密碼不符")
        
        return cleaned_data
        
    def save(self):
        """儲存使用者與個人檔案"""
        from django.contrib.auth.models import User
        from .models import UserProfile
        
        # 建立使用者
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        
        # 建立個人檔案
        UserProfile.objects.create(
            user=user,
            employee_id=self.cleaned_data['employee_id'],
            character_class=self.cleaned_data['character_class']
        )
        
        return user


class UserProfileEditForm(forms.Form):
    """使用者資料編輯表單"""
    username = forms.CharField(
        label='使用者名稱',
        widget=forms.TextInput(attrs={
            'class': 'rpg-input',
            'placeholder': '使用者名稱'
        })
    )
    email = forms.EmailField(
        label='電子郵件',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'rpg-input',
            'placeholder': '電子郵件'
        })
    )
    employee_id = forms.CharField(
        label='員工編號',
        widget=forms.TextInput(attrs={
            'class': 'rpg-input',
            'placeholder': '員工編號'
        })
    )
    avatar_image = forms.ImageField(
        label='大頭照',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'rpg-input'
        })
    )
    avatar_index = forms.IntegerField(
        label='預設頭像索引',
        required=False,
        widget=forms.HiddenInput()
    )
    old_password = forms.CharField(
        label='目前密碼',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'rpg-input',
            'placeholder': '若要修改密碼請輸入舊密碼',
            'autocomplete': 'new-password'
        }),
        help_text='變更密碼時需輸入舊密碼以進行驗證'
    )
    new_password = forms.CharField(
        label='新密碼',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'rpg-input',
            'placeholder': '若不修改請留空'
        }),
        help_text='若不修改密碼請留空'
    )
    confirm_password = forms.CharField(
        label='確認新密碼',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'rpg-input',
            'placeholder': '再次輸入新密碼'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        old_password = cleaned_data.get("old_password")

        if password:
            if password != confirm_password:
                raise forms.ValidationError("兩次輸入的密碼不符")
            if not old_password:
                # Add error to specific field
                self.add_error('old_password', "變更密碼時必須輸入舊密碼")

        return cleaned_data
