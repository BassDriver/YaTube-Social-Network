from django.core.cache import cache
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.cache import get_cache_key

from posts.views import index

KEY_PREFIX = 'index_page'


class PostCache(TestCase):
    def test_caches_index(self):
        """Проверка кеширования страницы index."""
        cache.clear()
        url = reverse('posts:index')
        request = RequestFactory().get(url)
        index(request)
        cache_key = get_cache_key(request, key_prefix=KEY_PREFIX)
        assert cache.get(cache_key) is not None
