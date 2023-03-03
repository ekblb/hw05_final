from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост'),
            'image': _('Изображение в новом посте'),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {
            'text': _('Текст нового комментария'),
        }
