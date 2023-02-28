import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post
from posts.tests.constants import (AUTHOR_USERNAME, GROUP_DESCRIPTION,
                                   GROUP_SLUG, GROUP_TITLE, POST_TEXT)
from yatube.settings import NUM_TEXT

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.post = PostModelTest.post
        self.group = PostModelTest.group
        field_expected_object = {
            (str(self.post), self.post.text[:NUM_TEXT]),
            (str(self.group), self.group.title)
        }
        for value, expected_value in field_expected_object:
            with self.subTest(value=value):
                self.assertEqual(value, expected_value)
