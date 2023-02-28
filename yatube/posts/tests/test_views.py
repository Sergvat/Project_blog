import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post
from posts.tests.constants import (AUTHOR_USERNAME, COMMENT_CREATE_URL_NAME,
                                   COMMENT_TEXT, GROUP_DESCRIPTION,
                                   GROUP_LIST_TEMPLATE, GROUP_LIST_URL_NAME,
                                   GROUP_SLUG, GROUP_TITLE, INDEX_TEMPLATE,
                                   INDEX_URL_NAME, PAGE_404_TEMPLATE,
                                   POST_CREATE_TEMPLATE, POST_CREATE_URL_NAME,
                                   POST_DETAIL_TEMPLATE, POST_DETAIL_URL_NAME,
                                   POST_EDIT_URL_NAME, POST_TEXT,
                                   PROFILE_TEMPLATE, PROFILE_URL_NAME,
                                   USER_USERNAME)
from yatube.settings import NUM_OF_POSTS

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewTests(TestCase):
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
            group=cls.group,
            text=POST_TEXT,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            text=COMMENT_TEXT,
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
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(INDEX_URL_NAME): INDEX_TEMPLATE,
            reverse(
                GROUP_LIST_URL_NAME, kwargs={'slug': GROUP_SLUG}
            ): GROUP_LIST_TEMPLATE,
            reverse(
                PROFILE_URL_NAME, kwargs={'username': AUTHOR_USERNAME}
            ): PROFILE_TEMPLATE,
            reverse(
                POST_DETAIL_URL_NAME, kwargs={'post_id': self.post.id}
            ): POST_DETAIL_TEMPLATE,
            reverse(
                POST_EDIT_URL_NAME, kwargs={'post_id': self.post.id}
            ): POST_CREATE_TEMPLATE,
            reverse(POST_CREATE_URL_NAME): POST_CREATE_TEMPLATE,
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_post.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_404_correct_template(self):
        """Cтраница 404 отдаёт кастомный шаблон."""
        response = self.client.get('/unexisting_page/')
        self.assertTemplateUsed(response, PAGE_404_TEMPLATE)

    def test_home_page_show_correct_context(self):
        """Список постов в шаблоне index
        сформирован с правильным контекстом."""
        response = self.client.get(reverse(INDEX_URL_NAME))
        expected_object = Post.objects.all()[0]
        self.assertEqual(response.context['page_obj'][0], expected_object)
        self.assertEqual(
            response.context['page_obj'][0].image,
            self.post.image
        )
        # self.assertContains(response, '<img')

    def test_list_post_group_show_correct_context(self):
        """Список постов в шаблоне group_list
        сформирован с правильным контекстом."""
        response = self.client.get(
            reverse(GROUP_LIST_URL_NAME, kwargs={'slug': self.group.slug})
        )
        expected_object = list(Post.objects.filter(group_id=self.group.id))
        self.assertEqual(list(response.context['page_obj']), expected_object)
        self.assertEqual(
            response.context['page_obj'][0].image,
            self.post.image
        )

    def test_post_profile_show_correct_context(self):
        """Список постов в шаблоне profile
        сформирован с правильным контекстом."""
        response = self.client.get(
            reverse(PROFILE_URL_NAME, kwargs={'username': self.author})
        )
        expected_object = list(Post.objects.filter(author=self.author))
        self.assertEqual(list(response.context['page_obj']), expected_object)
        self.assertEqual(
            response.context['page_obj'][0].image,
            self.post.image
        )

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован
        с правильным контекстом."""
        response = self.client.get(
            reverse(POST_DETAIL_URL_NAME, kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_create_author_post_id_show_correct_context(self):
        """Шаблон post_edit для автора поста
        сформирован с правильным контекстом."""
        response = self.author_post.get(
            reverse(POST_EDIT_URL_NAME, kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(POST_CREATE_URL_NAME))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_group_show_in_group(self):
        """Созданые посты отображаются на соответствующих страницах."""
        form_fields = {
            reverse(INDEX_URL_NAME): Post.objects.get(group=self.post.group),
            reverse(GROUP_LIST_URL_NAME, kwargs={'slug': self.group.slug}):
                Post.objects.get(group=self.post.group),
            reverse(PROFILE_URL_NAME, kwargs={'username': self.post.author}):
                Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_post_group_not_in_mistake_group(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.client.get(
            reverse(GROUP_LIST_URL_NAME, kwargs={'slug': self.group.slug})
        )
        expected_object = Post.objects.exclude(group=self.post.group)
        self.assertNotIn(expected_object, response.context['page_obj'])

    def test_form_comment_auth_user(self):
        """Проверка создания комментария авт. пользователем"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': COMMENT_TEXT,
        }
        response = self.authorized_client.post(
            reverse(COMMENT_CREATE_URL_NAME, kwargs={"post_id": self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(POST_DETAIL_URL_NAME,
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        exists = Comment.objects.filter(**form_data).exists()
        self.assertTrue(exists)

    def test_cache_index(self):
        """Проверка кеширования главной страницы index."""
        response_old = self.client.get(reverse('posts:index'))
        cache.clear()
        response_new = self.client.get(reverse('posts:index'))
        self.assertNotEqual(response_old, response_new)

    def test_profile_follow(self):
        """Проверка подписки на других пользователей."""
        url = reverse('posts:profile_follow',
                      kwargs={'username': AUTHOR_USERNAME})
        response = self.authorized_client.get(url)
        new_follow_exists = Follow.objects.filter(
            user=self.user,
            author=self.post.author).exists()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(new_follow_exists)

    def test_profile_unfollow(self):
        """Проверка отписки от других пользователей."""
        url = reverse(
            'posts:profile_unfollow',
            kwargs={'username': AUTHOR_USERNAME}
        )
        follow = Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client.get(url)
        follow_count = Follow.objects.filter(id=follow.id).count()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(follow_count, 0)

    def test_profile_follow_page(self):
        """Проверка новой записи в ленте тех, кто подписан."""
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        new_post = Post.objects.create(author=self.author)
        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)
        post_on_page = response.context['page_obj'][0]
        self.assertEqual(post_on_page, new_post)

    def test_profile_unfollow_page(self):
        """Пост не появляется в ленте у тех, кто не подписан."""
        Post.objects.create(author=self.author)
        url = reverse('posts:follow_index')
        response = self.authorized_client.get(url)
        post_count = len(response.context['page_obj'])

        self.assertEqual(post_count, 0)


class PaginatorViewsTest(TestCase):
    group = None
    author = None

    def setUp(self):
        self.author_post = Client()
        self.author_post.force_login(self.author)
        cache.clear()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        Post.objects.bulk_create(
            [
                Post(
                    text=f'{POST_TEXT} {i}', author=cls.author, group=cls.group
                ) for i in range(NUM_OF_POSTS + 1)
            ]
        )

    def test_paginator(self):
        """Шаблон страниц с Paginator сформирован с правильным контекстом."""
        urls_expected_post_number = {
            INDEX_URL_NAME: (
                {},
                Post.objects.all()[:NUM_OF_POSTS]
            ),
            GROUP_LIST_URL_NAME: (
                {'slug': self.group.slug},
                self.group.posts.all()[:NUM_OF_POSTS]
            ),
            PROFILE_URL_NAME: (
                {'username': self.author.username},
                self.author.posts.all()[:NUM_OF_POSTS]
            ),
        }
        for url_name, expected in urls_expected_post_number.items():
            kwargs, queryset = expected
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, kwargs=kwargs))
                self.assertEqual(response.status_code, HTTPStatus.OK)
                page_obj = response.context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    page_obj, queryset, transform=lambda x: x
                )
