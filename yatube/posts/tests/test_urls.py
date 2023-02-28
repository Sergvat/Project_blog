import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from posts.tests.constants import (AUTHOR_USERNAME, GROUP_DESCRIPTION,
                                   GROUP_SLUG, GROUP_TITLE, POST_EDIT_URL_NAME,
                                   POST_TEXT, USER_USERNAME)

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=POST_TEXT,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username=USER_USERNAME)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_post = Client()
        self.author_post.force_login(self.author)

    def test_urls_uses_correct(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author.username}/',
            f'/posts/{self.post.pk}/',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_uses_correct(self):
        """Страница /create/ доступна авторизованному
        пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_authorized(self):
        """Страница /post_edit/ доступна автору поста."""
        response = self.author_post.get(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """Несуществующая страница /unexisting_page/ вернёт ошибку 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
