import shutil
import tempfile

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Comment, Group, Post, User

USERNAME = 'HasNoName'
USERNAME_NOT_AUTHOR = 'NoAuthor'
GROUP_TITLE = 'Тестовая группа'
GROUP_DESCRIPTION = 'Тестовое описание'
TEST_SLUG = 'test-slug'
POST_TEXT = 'Теcтовый пост один'
TEST_SLUG_ADD = 'slug-test'
GROUP_TITLE_ADD = 'Группа вторая'
GROUP_DESCRIPTION_ADD = 'Дополнительная группа'
HOMEPAGE_URL = reverse('posts:index')
FOLLOW_LIST_URL = reverse('posts:follow_index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_posts', args=[TEST_SLUG])
GROUP_ADD_URL = reverse('posts:group_posts', args=[TEST_SLUG_ADD])
PROFILE_URL = reverse('posts:profile', args=[USERNAME])
HOMEPAGE_URL_SECOND_PAGE = f'{HOMEPAGE_URL}?page=2'
PROFILE_URL_SECOND_PAGE = f'{PROFILE_URL}?page=2'
GROUP_URL_SECOND_PAGE = f'{GROUP_URL}?page=2'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.noauthor = User.objects.create_user(username=USERNAME_NOT_AUTHOR)
        cls.group_one = Group.objects.create(
            title=GROUP_TITLE,
            slug=TEST_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.group_two = Group.objects.create(
            title=GROUP_TITLE_ADD,
            slug=TEST_SLUG_ADD,
            description=GROUP_DESCRIPTION_ADD,
        )
        cls.post = Post.objects.create(
            text=POST_TEXT,
            author=cls.user,
            group=cls.group_one,
            image=cls.create_image('image')
        )
        cls.guest = Client()
        cls.authorized = Client()
        cls.another = Client()
        cls.authorized.force_login(cls.user)
        cls.another.force_login(cls.noauthor)
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=[cls.post.id]
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @staticmethod
    def create_image(filename):
        small_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_img = SimpleUploadedFile(
            name=f'{filename}.jpeg',
            content=small_img,
            content_type='image/jpeg'
        )
        return uploaded_img

    def test_post_is_correctly_displayed_in_pages(self):
        """Созданный пост корректно отражается на всех страницах."""
        cache.clear()
        url_context = [
            [HOMEPAGE_URL, 'page_obj'],
            [PROFILE_URL, 'page_obj'],
            [GROUP_URL, 'page_obj'],
            [self.POST_DETAIL_URL, 'post']
        ]
        for url, object in url_context:
            with self.subTest(url=url):
                response = self.authorized.get(url)
                if object != 'post':
                    self.assertEqual(len(response.context[object]), 1)
                    post = response.context[object][0]
                else:
                    post = response.context.get(object)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.group_one)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_post_for_another_group(self):
        """Созданный пост не попал в чужую группу"""
        response = (self.authorized.get(GROUP_ADD_URL))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_paginator_for_pages_with_posts(self):
        """Паджинатор корректно показывает страницы с постами"""
        cache.clear()
        POSTS_PER_PAGE_ONE = settings.MAX_NUM_POSTS_PER_PAGE
        NUM_POSTS_TO_CREATE = settings.MAX_NUM_POSTS_PER_PAGE + 2
        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'Тест пост {i+1}',
                group=self.group_one
            ) for i in range(NUM_POSTS_TO_CREATE)
        )
        posts_per_page_two = Post.objects.all().count() - POSTS_PER_PAGE_ONE

        url_posts = [
            [HOMEPAGE_URL, POSTS_PER_PAGE_ONE],
            [PROFILE_URL, POSTS_PER_PAGE_ONE],
            [GROUP_URL, POSTS_PER_PAGE_ONE],
            [HOMEPAGE_URL_SECOND_PAGE, posts_per_page_two],
            [PROFILE_URL_SECOND_PAGE, posts_per_page_two],
            [GROUP_URL_SECOND_PAGE, posts_per_page_two]
        ]

        for url, exp_num_posts in url_posts:
            with self.subTest(url=url):
                self.assertEqual(len(
                    self.client.get(url).context['page_obj']),
                    exp_num_posts
                )

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = (self.authorized.get(GROUP_URL))
        group = response.context.get('group')
        self.assertEqual(group.title, self.group_one.title)
        self.assertEqual(group.description, self.group_one.description)
        self.assertEqual(group.slug, self.group_one.slug)
        self.assertEqual(group.id, self.group_one.id)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        self.assertEqual(
            self.authorized.get(
                PROFILE_URL).context.get(
                    'author'), self.user
        )

    def test_post_details_page_show_correct_comment(self):
        """Комментарий появляется на странице поста."""
        comment_for_post = Comment.objects.create(
            post=self.post,
            author=self.noauthor,
            text='Новый коммент'
        )
        response = self.authorized.get(self.POST_DETAIL_URL)
        self.assertEqual(len(response.context['comments']), 1)
        self.assertEqual(
            response.context['comments'][0].text, comment_for_post.text
        )
        self.assertEqual(
            response.context['comments'][0].author, comment_for_post.author
        )

    def test_follow_author_works_correctly(self):
        """Проверка создания и удаление подписки на автора"""
        follow_count = Follow.objects.count()
        follower = Follow.objects.create(
            user=self.noauthor,
            author=self.post.author,
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(
            Post.objects.filter(author=follower.author).count(), 1
        )
        response = self.another.get(FOLLOW_LIST_URL)
        self.assertEqual(len(response.context['page_obj']), 1)
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, follower.author)
        self.assertEqual(post.group, self.group_one)
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.image, self.post.image)

        # Удаление подписки
        follower.delete()
        self.assertEqual(Follow.objects.count(), follow_count)
        response = self.another.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
