from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil

from django.core.paginator import Page
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..forms import PostForm, CommentForm
from ..models import Comment, Group, Follow, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image_test = SimpleUploadedFile(
            name='test_image.gif',
            content=test_gif,
            content_type='image_test/gif',
        )
        cls.user = User.objects.create_user(
            username='test_page_user',
        )
        cls.group = Group.objects.create(
            title='test_page_group',
            slug='test_page_slug',
            description='Test description of test_page_group',
        )
        cls.other_group = Group.objects.create(
            title='text_group_title',
            slug='test_group_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Text_page',
            group=cls.group,
            image=image_test,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Test_comment',
        )

        cls.reverse_index = reverse('posts:index')
        cls.reverse_group = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug}
        )
        cls.reverse_group_other = reverse(
            'posts:group_list', kwargs={'slug': cls.other_group.slug}
        )
        cls.reverse_profile = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )
        cls.reverse_post_detail = reverse(
            'posts:post_detail', kwargs={'post_id': cls.post.pk}
        )
        cls.reverse_post_create = reverse('posts:post_create')
        cls.reverse_post_edit = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.pk}'}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_templates = {
            self.reverse_index: 'posts/index.html',
            self.reverse_group: 'posts/group_list.html',
            self.reverse_profile: 'posts/profile.html',
            self.reverse_post_detail: 'posts/post_detail.html',
            self.reverse_post_edit: 'posts/create_post.html',
            self.reverse_post_create: 'posts/create_post.html',
        }
        for page, template in pages_templates.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertTemplateUsed(response, template)

    def for_pages(self, context, is_page=True):
        if is_page:
            post_object = context.get('page_obj')
            self.assertIsInstance(post_object, Page)
            post = post_object[0]
        else:
            post = context.get('post')
        self.assertIsInstance(post, Post)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.image, self.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_index)
        context = response.context
        self.for_pages(context)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_group)
        context = response.context
        post_group = response.context.get('group')
        self.for_pages(context)
        self.assertEqual(post_group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_profile)
        context = response.context
        post_author = response.context.get('author')
        self.for_pages(context)
        self.assertEqual(post_author, self.user)

    def for_create_comment_correct_context(self, response):
        form_fields = {
            'text': forms.fields.CharField,
        }
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, CommentForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_post_detail)
        context = response.context
        self.for_pages(context, is_page=False)
        self.for_create_comment_correct_context(response)

    def for_create_edit_pages(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_post_create)
        self.for_create_edit_pages(response)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_post_edit)
        self.for_create_edit_pages(response)

    def test_post_added_correctly_user2(self):
        """Пост при создании не добавляется в другую группу."""
        response = self.authorized_client.get(self.reverse_group_other)
        context = response.context['page_obj']
        self.assertNotIn(self.post, context)


class PaginatorViewsTest(TestCase):
    NUMBER_POSTS_PAGE_2: int = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_paginator_username')
        cls.group = Group.objects.create(
            title='test_paginator_group',
            slug='test_paginator_slug'
        )
        cls.reverse_index = reverse('posts:index')
        cls.reverse_group = reverse(
            'posts:group_list', kwargs={'slug': cls.group.slug}
        )
        cls.reverse_profile = reverse(
            'posts:profile', kwargs={'username': cls.user.username}
        )

    def setUp(self):
        self.guest_client_other = Client()
        self.authorized_client_paginator = Client()
        self.authorized_client_paginator.force_login(self.user)
        bilk_post: list = []
        for i in range(settings.NUMBER_OF_POST + self.NUMBER_POSTS_PAGE_2):
            bilk_post.append(Post(text=f'test_text{i}',
                                  group=self.group,
                                  author=self.user))
        Post.objects.bulk_create(bilk_post)

    def test_paginator_for_first_second_page(self):
        '''Проверка количества постов на первой и второй страницах.'''
        pages: list = [
            self.reverse_index,
            self.reverse_profile,
            self.reverse_group
        ]
        for page in pages:
            response_page_1 = self.guest_client_other.get(page)
            response_page_2 = self.guest_client_other.get(page + '?page=2')
        self.assertEqual(
            len(response_page_1.context['page_obj']),
            settings.NUMBER_OF_POST
        )
        self.assertEqual(
            len(response_page_2.context['page_obj']),
            self.NUMBER_POSTS_PAGE_2,
        )


class CachePageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_page_user',
        )
        cls.group = Group.objects.create(
            title='test_page_group',
            slug='test_page_slug',
            description='Test description of test_page_group',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Text_page',
            group=cls.group,
        )
        cls.reverse_index = reverse('posts:index')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()

    def test_index_page_have_cache(self):
        '''Проверка работы кеша на главной странице.'''
        posts_before = self.authorized_client.get(self.reverse_index).content
        Post.objects.create(
            author=self.user,
            text='Text_page',
            group=self.group,
        )
        posts_with_new_post = self.authorized_client.get(
            self.reverse_index).content
        self.assertEqual(posts_with_new_post, posts_before)
        cache.clear()
        posts_clear_cache = self.authorized_client.get(
            self.reverse_index).content
        self.assertNotEqual(posts_with_new_post, posts_clear_cache)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(
            username='test_user_follower',
        )
        cls.user_following = User.objects.create_user(
            username='test_user_following',
        )
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Text_page',
        )
        cls.post_other = Post.objects.create(
            author=cls.user_following,
            text='Text_page_other',
        )
        cls.group = Group.objects.create(
            title='test_url_group',
            slug='test_url_slug',
            description='Test description of test_url_group',
        )
        cls.follow = Follow.objects.create(
            user=cls.user_follower,
            author=cls.user_following,
        )

        cls.reverse_profile_follow = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user_following.username}
        )
        cls.reverse_index_follow = reverse('posts:follow_index')
        cls.reverse_profile_unfollow = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user_following.username}
        )

    def setUp(self):
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_following = Client()
        self.authorized_client_following.force_login(self.user_following)

    def test_follow_authorized_client(self):
        '''Авторизованный пользователь может подписываться
        на других пользователей.'''
        Follow.objects.all().delete()
        self.authorized_client_follower.get(
            self.reverse_profile_follow
        )
        self.assertTrue(Follow.objects.filter(
            author=self.user_following,
            user=self.user_follower,
        ).exists())

    def test_delete_follow_authorized_client(self):
        '''Авторизованный пользователь может удалять подписки.'''
        self.authorized_client_follower.get(self.reverse_profile_unfollow)
        self.assertFalse(Follow.objects.filter(
            author=self.user_following,
            user=self.user_follower,
        ).exists())

    def test_follow_new_post(self):
        '''Пост появляется на странице избранного у подписчика.'''
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following,
        )
        new_post = Post.objects.create(
            author=self.user_following,
            text='Text_new_post',
        )
        response = self.authorized_client_follower.get(
            self.reverse_index_follow
        )
        self.assertIn(new_post, response.context['page_obj'])

    def test_follow_new_post(self):
        '''Пост не попадает в подписку к пользователям,
        не подписанным на автора.'''
        new_post_other = Post.objects.create(
            author=self.user_following,
            text='Text_new_post',
        )
        response = self.authorized_client_following.get(
            self.reverse_index_follow
        )
        self.assertNotIn(new_post_other, response.context['page_obj'])
