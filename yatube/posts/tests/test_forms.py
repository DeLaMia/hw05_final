import shutil
import tempfile

from http import HTTPStatus

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import PostForm
from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.group = Group.objects.create(
            title='test-text',
            slug='test-slug',
            description='test_description',)
        cls.new_group = Group.objects.create(
            title='new-group',
            slug='new-group-slug',
            description='test_description',)
        cls.post = Post.objects.create(
            author=cls.user,
            text='test-post-text',
            group=cls.group)
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """создает запись в Post."""
        post_count = Post.objects.count()

        form_data = {
            'text': '',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'New-test-text',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_post = Post.objects.all().order_by('pub_date').last()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group, self.group)
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )

    def test_post_edit(self):
        """Изменяет запись в Post."""
        form_data_1 = {
            'text': 'New-text',
            'group': self.new_group.pk
        }
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(self.post.id,)),
            data=form_data_1,
            follow=True
        )
        post_edit = Post.objects.get(pk=self.post.id)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text, form_data_1['text'])
        self.assertEqual(post_edit.group.pk, form_data_1['group'])

    def test_post_create_not_authorized(self):
        """Неавторизованный пользоватекль не может создать запись."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'not authorized',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_comment_create_not_authorized(self):
        """Неавторизованный пользоватекль не может создать комментарий."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'text_comment',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )

    def test_comment_create(self):
        """создает Comment, Comment отоброжается."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'text_comment',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )

        last_comment = self.post.comments.order_by('pub_date').last()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(last_comment.text, form_data['text'])


