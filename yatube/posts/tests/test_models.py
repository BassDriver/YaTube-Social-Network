from django.conf import settings
from django.test import TestCase

from ..models import Comment, Follow, Group, Post, User

USERNAME = 'HasNoName'
NOAUTHOR = 'NoAuthor'
GROUP_TITLE = 'Тестовая группа'
GROUP_DESCRIPTION = 'Тестовое описание'
TEST_SLUG = 'test-slug'
POST_TEXT = 'Теcтовый пост один'
COMMENT = 'Тестовый комментарий'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.noauthor = User.objects.create_user(username=NOAUTHOR)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=TEST_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.noauthor,
            text=COMMENT,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        exp_group_name = self.group.title
        exp_post_text = self.post.text[:settings.MAX_NUM_CHARS_POST]
        exp_comment_text = self.comment.text[:settings.MAX_NUM_CHARS_POST]
        self.assertEqual(exp_group_name, str(self.group))
        self.assertEqual(exp_post_text, str(self.post))
        self.assertEqual(exp_comment_text, str(self.comment))

    def test_verbose_name_group(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'title': 'Название группы',
            'slug': 'уникальная часть URL группы',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Group._meta.get_field(field).
                    verbose_name, expected_value
                )

    def test_verbose_name_post(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).
                    verbose_name, expected_value
                )

    def test_verbose_name_comment(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Comment._meta.get_field(field).
                    verbose_name, expected_value
                )

    def test_verbose_name_follow(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Follow._meta.get_field(field).
                    verbose_name, expected_value
                )
