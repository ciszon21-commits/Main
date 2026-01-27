from django import forms
from .models import Question, Quiz, Candidate, QuestionCategory

class QuestionForm(forms.ModelForm):
    # Custom widget for choices to make it easier to edit JSON
    choices_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4, 
            'placeholder': '每行輸入一個選項',
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
        }),
        required=False, 
        help_text="請每行輸入一個選項 (單選題必填)"
    )

    DIFFICULTY_CHOICES = [(i, f"{i} 分") for i in range(1, 6)]

    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES, 
        widget=forms.RadioSelect(attrs={'class': 'form-radio h-5 w-5 text-indigo-600'}),
        label="難度"
    )

    class Meta:
        model = Question
        fields = ['category', 'text', 'question_type', 'correct_answer', 'difficulty', 'points', 'is_active']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
            }),
            'question_type': forms.RadioSelect(attrs={'class': 'form-radio h-5 w-5 text-indigo-600'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-indigo-600'}),
            'points': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
            }),
             'correct_answer': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
            }),
            'category': forms.Select(attrs={
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.choices:
            self.fields['choices_text'].initial = '\n'.join(self.instance.choices)
        
        # Only set default class only if not already set (which we did above for most)
        # But we really want to ensure everything is text-lg
        
    def clean(self):
        cleaned_data = super().clean()
        choices_text = cleaned_data.get('choices_text')
        q_type = cleaned_data.get('question_type')
        
        if q_type == 'single' and not choices_text:
            self.add_error('choices_text', '單選題必須提供選項')
            
        if choices_text:
            cleaned_data['choices'] = [c.strip() for c in choices_text.split('\n') if c.strip()]
        else:
            cleaned_data['choices'] = []
            
        return cleaned_data


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ['title', 'description', 'time_limit_minutes', 'is_active']
        widgets = {
             'title': forms.TextInput(attrs={
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
             'description': forms.Textarea(attrs={
                 'rows': 3,
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
             'time_limit_minutes': forms.NumberInput(attrs={
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
             'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox h-5 w-5 text-indigo-600'}),
        }


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['name', 'email', 'phone', 'note']
        widgets = {
             'name': forms.TextInput(attrs={
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
              'email': forms.EmailInput(attrs={
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
             'phone': forms.TextInput(attrs={
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
             'note': forms.Textarea(attrs={
                 'rows': 3,
                 'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-lg'
             }),
        }
