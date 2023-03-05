import tempfile
import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            username='test_form_user',
        )
        cls.user_other = User.objects.create_user(
            username='test_form_user_comment',
        )
        cls.group = Group.objects.create(
            title='test_form_group',
            slug='test_form_slug',
            description='Test description of test_form_group',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Text_form',
            image=image_test,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_other,
            text='Test_comment',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_other = Client()
        self.authorized_client_other.force_login(self.user_other)

    def test_post_create(self):
        """Проверка формы создания поста."""
        Post.objects.all().delete()
        test_gif_post = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image_test = SimpleUploadedFile(
            name='test_image.gif',
            content=test_gif_post,
            content_type='image_test/gif',
        )
        form_data = {
            'text': 'Text_test_form_create',
            'group': self.group.id,
            'image': image_test,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_image = image_test.name
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(f'posts/{post_image}', f'posts/{post_image}')

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

    def test_comment_create_authorized_client(self):
        """Создание комментария авторизованным клиентом."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'Test_comment',
        }
        self.authorized_client_other.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])

    def test_comment_create_guest_client(self):
        """Создание комментария неавторизованным клиентом."""
        Comment.objects.all().delete()
        form_data = {
            'text': 'Test_comment',
        }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)
