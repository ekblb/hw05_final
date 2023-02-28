from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_mod_user',
        )
        cls.group = Group.objects.create(
            title='test_mod_group',
            slug='test_mod_slug',
            description='Test description of test_mod_group',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test_text_models',
            group=cls.group,
        )

    def test_models_have_correct_object_names(self):
        """Корректная работа __str__ у моделей."""
        str_post_group_models = {
            str(self.post): self.post.text[:15],
            str(self.group): self.post.group.title,
        }
        for model, result in str_post_group_models.items():
            with self.subTest(model=model):
                self.assertEqual(model, result)
