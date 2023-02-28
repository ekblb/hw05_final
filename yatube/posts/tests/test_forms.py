from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_form_user',
        )
        cls.group = Group.objects.create(
            title='test_form_group',
            slug='test_form_slug',
            description='Test description of test_form_group',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Text_form',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Проверка формы создания поста."""
        Post.objects.all().delete()
        form_data = {
            'text': 'Text_test_form_create',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])

    def test_post_edit(self):
        """Проверка формы редактирования поста."""
        post_count = Post.objects.count()
        form_edit_data = {
            'text': 'Text_test_form_edit',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_edit_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(Post.objects.count(), post_count)
        post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(post.text, form_edit_data['text'])
        self.assertEqual(post.group.pk, form_edit_data['group'])
