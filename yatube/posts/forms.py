from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Введите текст.',
            'group': 'Выберите группу',
            'image': 'Выберите картинку',
        }


class CommentForm(ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Введите текст комментария',
        }
