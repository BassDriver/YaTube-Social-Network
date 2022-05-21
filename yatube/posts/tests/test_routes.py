from django.test import TestCase
from django.urls import reverse

USERNAME = 'HasNoName'
POST_ID = 1
SLUG = 'test-slug'
CASES = [
    ['/', 'index', None],
    ['/create/', 'post_create', None],
    [f'/group/{SLUG}/', 'group_posts', [SLUG]],
    [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
    [f'/posts/{POST_ID}/', 'post_detail', [POST_ID]],
    [f'/posts/{POST_ID}/edit/', 'update_post', [POST_ID]],
    [f'/posts/{POST_ID}/comment/', 'add_comment', [POST_ID]],
    ['/follow/', 'follow_index', None],
    [f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]],
    [f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]]
]


class PostURLTests(TestCase):
    def test_posts_page_routes_works_as_intended(self):
        """Проверяем корректность маршрута страниц приложения posts"""
        for url, view_name, param in CASES:
            response = reverse(f'posts:{view_name}', args=param)
            with self.subTest(url=url):
                self.assertEqual(url, response)
