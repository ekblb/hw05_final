from http import HTTPStatus
from django.core.cache import cache
from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_url_user',
        )
        cls.user_other = User.objects.create_user(
            username='other_user',
        )
        cls.group = Group.objects.create(
            title='test_url_group',
            slug='test_url_slug',
            description='Test description of test_url_group',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Text_url',
        )
        cls.post_other = Post.objects.create(
            author=cls.user_other,
            text='Text_url_other',
        )

        cls.page_post = f'/posts/{cls.post.id}/'
        cls.post_other = f'/posts/{cls.post_other.id}/'
        cls.redirect_page = '/auth/login/?next='
        cls.unexisting_page = '/unexisting_page/'
        cls.public_pages_template = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author.username}/': 'posts/profile.html',
            cls.page_post: 'posts/post_detail.html',
        }

        cls.private_pages_template = {
            f'{cls.page_post}edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.pages_template = {
            **cls.public_pages_template,
            **cls.private_pages_template
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location_authorized(self):
        """Доступность всех URL-адресов для авторизованных пользователей."""
        for url in self.pages_template:
            with self.subTest(url=url):
                responce = self.authorized_client.get(url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location(self):
        """Доступность public URL-адресов для неавторизованны
        пользователей."""
        for url in self.public_pages_template:
            with self.subTest(url=url):
                responce = self.guest_client.get(url)
                self.assertEqual(responce.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymous(self):
        """Редиректы для неавторизованных пользователей."""
        for url in self.private_pages_template:
            with self.subTest(url=url):
                responce = self.guest_client.get(url, follow=True)
                self.assertRedirects(responce, self.redirect_page + url)

    def test_urls_redirect(self):
        """Редирект для авторизованного пользователя при редактировании
         чужого поста."""
        responce = self.authorized_client.get(f'{self.post_other}edit/')
        self.assertRedirects(responce, f'{self.post_other}')

    def test_urls_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.pages_template.items():
            with self.subTest(url=url):
                responce = self.authorized_client.get(url)
                self.assertTemplateUsed(responce, template)

    def test_unexisting_page(self):
        """Ошибка 404 для несуществующей страницы."""
        responce = self.guest_client.get(self.unexisting_page)
        self.assertEqual(responce.status_code, HTTPStatus.NOT_FOUND)

    # def test_403_correct_templates(self):
    #     """Страница 403 использует соответствующий шаблон."""
    #     template = 'core/403.html'
    #     self.assertTemplateUsed(
    #         self.guest_client.get('???'), template
    #     )

    def test_404_correct_templates(self):
        """Страница 404 использует соответствующий шаблон."""
        template = 'core/404.html'
        self.assertTemplateUsed(
            self.guest_client.get(self.unexisting_page), template
        )
