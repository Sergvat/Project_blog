import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post
from posts.tests.constants import (AUTHOR_USERNAME, GROUP_DESCRIPTION,
                                   GROUP_SLUG, GROUP_TITLE,
                                   POST_CREATE_URL_NAME, POST_DETAIL_URL_NAME,
                                   POST_EDIT_URL_NAME, POST_TEXT,
                                   PROFILE_URL_NAME)

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='test_image.gif',
            content=test_image,
            content_type='image/gif'
        )
        cls.author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text=POST_TEXT,
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_post = Client()
        self.author_post.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
            'image': self.post.image,
        }
        response = self.author_post.post(
            reverse(POST_CREATE_URL_NAME),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(PROFILE_URL_NAME,
                              kwargs={'username': self.author.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(**form_data).exists())

    def test_post_edit(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': POST_TEXT,
            'group': self.group.id,
        }
        response = self.author_post.post(
            reverse(POST_EDIT_URL_NAME, args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        self.assertRedirects(
            response, reverse(POST_DETAIL_URL_NAME,
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            Post.objects.get(id=self.post.id).text, POST_TEXT
        )
        self.assertEqual(
            Post.objects.get(id=self.group.id).group, self.group
        )
