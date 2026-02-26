from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import QuestionSet, Question, PracticeResponse


class QuestionSetForm(forms.ModelForm):
    class Meta:
        model = QuestionSet
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python Basics'}),
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'difficulty', 'tags', 'order']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Question text...'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. algorithms, strings'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class PracticeResponseForm(forms.ModelForm):
    class Meta:
        model = PracticeResponse
        fields = ['response_text']
        widgets = {
            'response_text': forms.Textarea(attrs={
                'rows': 8,
                'class': 'form-control',
                'placeholder': 'Type your answer here...',
            }),
        }
