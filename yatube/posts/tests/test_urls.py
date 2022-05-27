from django.core.cache import cache
from django.contrib.auth import get_user
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

USERNAME = 'HasNoName'
USERNAME_NOT_AUTHOR = 'NoAuthor'
GROUP_TITLE = 'Тестовая группа'
GROUP_DESCRIPTION = 'Тестовое описание'
TEST_SLUG = 'test-slug'
POST_TEXT = 'Теcтовый пост один'
HOMEPAGE_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_posts', args=[TEST_SLUG])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
LOGIN_URL = reverse('users:login')
FOLLOW_LIST_URL = reverse('posts:follow_index')
FOLLOW_URL = reverse('posts:profile_follow', args=[USERNAME])
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USERNAME])
REDIRECT_NON_AUTHOR = f'{LOGIN_URL}?next={POST_CREATE_URL}'
REDIRECT_ANONYMOUS_FOLLOW_LIST = f'{LOGIN_URL}?next={FOLLOW_LIST_URL}'
REDIRECT_ANONYMOUS_FOLLOW = f'{LOGIN_URL}?next={FOLLOW_URL}'
REDIRECT_ANONYMOUS_UNFOLLOW = f'{LOGIN_URL}?next={UNFOLLOW_URL}'
OK = 200
REDIRECT = 302
NOT_AVAILABLE = 404


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user_2 = User.objects.create_user(
            username=USERNAME_NOT_AUTHOR
        )
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=TEST_SLUG,
            description=GROUP_DESCRIPTION
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=[cls.post.id]
        )
        cls.POST_EDIT_URL = reverse(
            'posts:update_post', args=[cls.post.id]
        )
        cls.REDIRECT_ANONYMOUS_POST_EDIT = (
            f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'
        )
        cls.guest = Client()
        cls.author = Client()
        cls.another = Client()
        cls.author.force_login(cls.user)
        cls.another.force_login(cls.user_2)

    # Проверяем доступность страниц
    def test_url_exists_at_desired_location(self):
        """Проверяем доступность URL для всех пользователей и автора"""
        url_client = [
            [HOMEPAGE_URL, self.guest, OK],
            [GROUP_URL, self.guest, OK],
            [PROFILE_URL, self.guest, OK],
            [self.POST_DETAIL_URL, self.guest, OK],
            [self.POST_EDIT_URL, self.author, OK],
            [POST_CREATE_URL, self.author, OK],
            [FOLLOW_LIST_URL, self.author, OK],
            [FOLLOW_LIST_URL, self.another, OK],
            [FOLLOW_URL, self.author, REDIRECT],
            [FOLLOW_URL, self.another, REDIRECT],
            [UNFOLLOW_URL, self.author, NOT_AVAILABLE],
            [UNFOLLOW_URL, self.another, REDIRECT],
            [POST_CREATE_URL, self.guest, REDIRECT],
            [self.POST_EDIT_URL, self.another, REDIRECT],
            [self.POST_EDIT_URL, self.guest, REDIRECT],
            [FOLLOW_LIST_URL, self.guest, REDIRECT],
            [FOLLOW_URL, self.guest, REDIRECT],
            [UNFOLLOW_URL, self.guest, REDIRECT],
        ]
        for url, client, status_code in url_client:
            with self.subTest(url=url, client=get_user(client).username):
                self.assertEqual(
                    client.get(url).status_code, status_code
                )

    def test_redirect_url_different_scenarios(self):
        """Случаи перенаправления корректно отрабатываются"""
        redirect_cases = [
            [self.POST_EDIT_URL, self.guest,
                self.REDIRECT_ANONYMOUS_POST_EDIT],
            [self.POST_EDIT_URL, self.another, self.POST_DETAIL_URL],
            [POST_CREATE_URL, self.guest, REDIRECT_NON_AUTHOR],
            [FOLLOW_LIST_URL, self.guest, REDIRECT_ANONYMOUS_FOLLOW_LIST],
            [FOLLOW_URL, self.guest, REDIRECT_ANONYMOUS_FOLLOW],
            [FOLLOW_URL, self.author, PROFILE_URL],
            [FOLLOW_URL, self.another, PROFILE_URL],
            [UNFOLLOW_URL, self.guest, REDIRECT_ANONYMOUS_UNFOLLOW],
            [UNFOLLOW_URL, self.another, PROFILE_URL],
        ]
        for url, client, redirect in redirect_cases:
            with self.subTest(url=url, client=get_user(client).username):
                self.assertRedirects(
                    client.get(url, follow=True),
                    redirect
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        # Шаблоны по адресам
        templates_url_names = {
            HOMEPAGE_URL: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
            FOLLOW_LIST_URL: 'posts/follow.html',
            'unexisting_page': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address, exp_template=template):
                self.assertTemplateUsed(
                    self.author.get(address), template
                )
