from django import forms
from .models import Post, Comment, User
from django.contrib.auth.forms import PasswordChangeForm


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'text': forms.Textarea({'cols': '22', 'rows': '5'}),
            'pub_date': forms.DateInput(
                format='%d%m%Y',
                attrs={'type': 'date', 'input_formats': ['%Y-%m-%d']}
            ),
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class UserInfoForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        label='Имя пользователя (username)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    first_name = forms.CharField(
        max_length=150,
        label='Имя',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        label='Фамилия',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вашу фамилию'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
