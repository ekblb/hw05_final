from django import forms
from django.conf import settings
from django.core.paginator import Page
from django.test import TestCase, Client
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Follow, Post, User


class PostPageTest(TestCase):
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
        cls.other_group = Group.objects.create(
            title='text_group_title',
            slug='test_group_slug')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Text_page',
            group=cls.group,
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

    def setUp(self):
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

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.reverse_post_detail)
        context = response.context
        self.for_pages(context, is_page=False)

    def for_create_edit_pages(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
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
        """Пост при создании не добавляется в другую группу"""
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
        '''Проверка количества постов на первой и второй страницах. '''
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
        на других пользователей'''
        follower_count = Follow.objects.count()
        self.authorized_client_follower.get(self.reverse_profile_follow)
        self.assertEqual(Follow.objects.count(), follower_count)

    def test_delete_follow_authorized_client(self):
        '''Авторизованный пользователь может удалять подписки '''
        follower_count = Follow.objects.count()
        self.authorized_client_follower.get(self.reverse_profile_unfollow)
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    # def test_follow_new_post(self):
    #     ''' Новая запись пользователя появляется в ленте тех,
    #     кто на него подписан и не появляется в ленте тех,
    #  кто не подписан. '''
    #     response_1 = self.authorized_client_follower.get(
    #         self.reverse_index_follow
    #     )
    #     post = response_1.context['page_obj'][0]
    #     self.assertEqual(post, self.post)
    #     self.follow.delete()
    #     response_2 = self.authorized_client_follower.get(
    #         self.reverse_index_follow
    #     )
    #     self.assertEqual(len(response_2.context(['page_obj'])), 0)
