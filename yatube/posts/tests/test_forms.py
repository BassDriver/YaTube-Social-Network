import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from django import forms

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post, User

USERNAME = 'HasNoName'
USERNAME_NOT_AUTHOR = 'NoAuthor'
GROUP_TITLE = 'Тестовая группа'
GROUP_TITLE_ADD = 'Другая группа'
GROUP_DESCRIPTION = 'Тестовое описание'
GROUP_DESCRIPTION_ADD = 'Новое описание'
TEST_SLUG = 'test-slug'
TEST_SLUG_ADD = 'add_group'
POST_TEXT = 'Теcтовый пост один'
COMMENT = 'Тестовый комментарий'
POST_CREATE_URL = reverse('posts:post_create')
LOGIN_URL = reverse('users:login')
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
REDIRECT_NON_AUTHOR = (
    f'{LOGIN_URL}?next={POST_CREATE_URL}'
)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
IMAGE = Post.image.field.upload_to
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.noauthor = User.objects.create_user(username=USERNAME_NOT_AUTHOR)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=TEST_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.group_add = Group.objects.create(
            title=GROUP_TITLE_ADD,
            slug=TEST_SLUG_ADD,
            description=GROUP_DESCRIPTION_ADD,
        )
        # Создаем запись в базе данных для проверки сушествующего slug
        cls.post = Post.objects.create(
            text=POST_TEXT,
            group=cls.group,
            author=cls.user
        )
        # Создаем форму, если нужна проверка атрибутов
        cls.post_form = PostForm()
        cls.comment_form = CommentForm()
        cls.guest = Client()
        cls.author = Client()
        cls.another = Client()
        cls.author.force_login(cls.user)
        cls.another.force_login(cls.noauthor)
        cls.UPDATE_POST_URL = reverse('posts:update_post', args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.POST_COMMENT_URL = reverse(
            'posts:add_comment', args=[cls.post.id]
        )
        cls.REDIRECT_ANONYMOUS_POST_COMMENT = (
            f'{LOGIN_URL}?next={cls.POST_COMMENT_URL}'
        )
        cls.REDIRECT_ANONYMOUS_POST_EDIT = (
            f'{LOGIN_URL}?next={cls.UPDATE_POST_URL}'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_form_labels(self):
        """Проверка лейблов полей формы поста"""
        text_label = self.post_form.fields['text'].label
        group_label = self.post_form.fields['group'].label
        image_label = self.post_form.fields['image'].label
        self.assertEqual(text_label, 'Текст')
        self.assertEqual(group_label, 'Группа')
        self.assertEqual(image_label, 'Картинка')

    def test_post_form_help_text(self):
        """Проверка подсказок полей формы поста"""
        title_text_label = self.post_form.fields['text'].help_text
        title_group_label = self.post_form.fields['group'].help_text
        title_image_label = self.post_form.fields['image'].help_text
        self.assertEqual(title_text_label, 'Введите текст.')
        self.assertEqual(title_group_label, 'Выберите группу')
        self.assertEqual(title_image_label, 'Выберите картинку')

    def test_comment_form_labels(self):
        """Проверка лейблов поля формы коммента"""
        text_label = self.comment_form.fields['text'].label
        self.assertEqual(text_label, 'Текст')

    def test_comment_form_help_text(self):
        """Проверка подсказок поля формы коммента"""
        title_text_label = self.comment_form.fields['text'].help_text
        self.assertEqual(title_text_label, 'Введите текст комментария')

    def test_can_create_post_with_group(self):
        """Проверка создания поста через форму и перенаправления"""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        posts = set(Post.objects.all())
        response = self.author.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, PROFILE_URL)
        posts = set(Post.objects.all()) - posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, f'{IMAGE}{uploaded.name}')

    def test_can_update_post_with_group(self):
        """Обновление поста через форму работает корректно"""
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Обновленный пост',
            'group': self.group_add.id,
            'image': uploaded,
        }
        response = self.author.post(
            self.UPDATE_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        post = response.context.get('post')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, f'{IMAGE}{uploaded.name}')

    def test_can_add_comment_to_existing_post(self):
        """Добавление комментария к посту через форму работает корректно"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': COMMENT,
        }
        response = self.author.post(
            self.POST_COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comments = self.post.comments.all()
        self.assertEqual(len(comments),1)
        comment = self.post.comments.all()[0]
        self.assertEqual(comment.post, self.post)
        

    def test_anonymous_create_post_with_group(self):
        """Аноним не может создать пост через форму"""
        posts = set(Post.objects.all())
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.guest.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(set(Post.objects.all()), posts)
        self.assertRedirects(response, REDIRECT_NON_AUTHOR)

    def test_anonymous_add_comment_to_existing_post(self):
        """Аноним не может добавить комментарий к посту через форму"""
        comments = set(Comment.objects.all())
        form_data = {
            'text': COMMENT,
        }
        response = self.guest.post(
            self.POST_COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(set(Comment.objects.all()),comments)
        self.assertRedirects(response, self.REDIRECT_ANONYMOUS_POST_COMMENT)

    def test_anonymous_update_post_with_group(self):
        """Аноним/не автор не может обновить пост через форму"""
        cases = [
            [self.guest, self.REDIRECT_ANONYMOUS_POST_EDIT],
            [self.another, self.POST_DETAIL_URL],
        ]
        for client, redirect in cases:
            with self.subTest(client=get_user(client).username):
                post_count = Post.objects.count()
                uploaded = SimpleUploadedFile(
                    name='test.gif',
                    content=SMALL_GIF,
                    content_type='image/gif'
                )
                form_data = {
                    'text': 'Обновленный пост',
                    'group': self.group_add.id,
                    'image': uploaded,
                }
                response = client.post(
                    self.UPDATE_POST_URL,
                    data=form_data,
                    follow=True
                )
                self.assertEqual(Post.objects.count(), post_count)
                self.assertRedirects(response, redirect)
                post = Post.objects.get(pk=self.post.id)
                self.assertEqual(self.post.text, post.text)
                self.assertEqual(self.post.group.id, post.group.id)
                self.assertEqual(self.post.author, post.author)
                self.assertEqual(self.post.image, post.image)

    def test_create_and_edit_page_show_correct_context(self):
        """Шаблон поста сформирован с правильным контекстом."""
        urls = [POST_CREATE_URL, self.UPDATE_POST_URL]

        for url in urls:
            with self.subTest(url=url):
                response = self.author.get(url)
                self.assertIsInstance(response.context.get(
                    'form').fields.get('text'), forms.fields.CharField
                )
                self.assertIsInstance(response.context.get(
                    'form').fields.get('group'), forms.fields.ChoiceField
                )
                self.assertIsInstance(response.context.get(
                    'form').fields.get('image'), forms.fields.ImageField
                )

    def test_add_comment_show_correct_context(self):
        """Шаблон комментария с правильным контекстом."""
        response = self.author.get(self.POST_DETAIL_URL)
        self.assertIsInstance(response.context.get(
            'form').fields.get('text'), forms.fields.CharField
        )
