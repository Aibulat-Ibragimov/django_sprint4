import datetime

from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_date'].initial = datetime.datetime.now(
        ).strftime('%Y-%m-%d %H:%M')

    class Meta:
        model = Post
        fields = (
            'title', 'text', 'pub_date', 'image',
            'location', 'category', 'is_published',
        )
        widgets = {
            'text': forms.Textarea({'cols': '22', 'rows': '5'}),
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%d %H:%M',
                attrs={'type': 'datetime-local',
                       'class': 'form-control'}
            ),
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
