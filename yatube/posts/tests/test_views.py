import shutil
import tempfile

from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User, Follow

TOTAL_POSTS: int = 20
POSTS_AUTHOR_USER: int = 13
POSTS_WITH_GROUP: int = 17
POST_IN_PAGE: int = 10

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostVievsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Создается 2 обьекта юзер, 20 постов,
        # 13 с одним автором и 7 со вторым, 17 с одной группой
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_another = User.objects.create_user(username='I_is_not_NoName')
        cls.group = Group.objects.create(
            title='test-text',
            slug='test-slug',
            description='test_description',
        )
        for i in range(3):
            cls.post = Post.objects.create(
                author=cls.user_another,
                text='test-post-text',)
        for i in range(4):
            cls.post = Post.objects.create(
                author=cls.user_another,
                text='test-post-text',
                group=cls.group)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        posts: list = []
        for i in range(1, 14):
            cls.post = Post(
                id=Post.objects.latest('id').id + i,
                author=cls.user,
                text='test-post-text',
                group=cls.group,
                image=cls.uploaded)
            posts.append(cls.post)
        Post.objects.bulk_create(posts)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_client = Client()
        self.another_client.force_login(self.user_another)

    def post_test(self, response):
        """Тест поста"""
        post_object = response.context['page_obj'][0]
        self.assertEqual(post_object.author.username, self.user.username)
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.image, self.post.image)

    def post_card_test(self, response):
        """Тест поста на странице post_detail"""
        post_object = response.context['post']
        self.assertEqual(post_object.author.username, self.user.username)
        self.assertEqual(post_object.text, self.post.text)
        self.assertEqual(post_object.group.title, self.group.title)
        self.assertEqual(post_object.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'NoName'}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.post_test(response)

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug'}))
        self.post_test(response)
        self.assertEqual(response.context['group'], self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'NoName'}))
        self.post_test(response)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context['post_count'],
                         self.user.posts.count())

    def test_first_page_contains_ten_records(self):
        """Тест паджинатора"""
        pages_names = {
            reverse('posts:index'): TOTAL_POSTS,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): POSTS_WITH_GROUP,
            reverse('posts:profile',
                    kwargs={'username':
                            self.user.username}): POSTS_AUTHOR_USER,
        }
        for reverse_name in pages_names.keys():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 POST_IN_PAGE)
        for reverse_name, post_count in pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 post_count - POST_IN_PAGE)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.id})))
        self.post_card_test(response)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_show_correct_group(self):
        """ post при создании с группой отображается на всех страницах
            и не попадает в другую группу."""
        self.new_group = Group.objects.create(
            title='new',
            slug='new-test-slug',
            description='new-test_description',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='new-test-post-text',
            group=self.new_group,)
        checks = {reverse('posts:index'),
                  reverse('posts:group_list',
                          kwargs={'slug': 'new-test-slug'}),
                  reverse('posts:profile', kwargs={'username': 'NoName'}),
                  }
        for reverse_name in checks:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.author.username, 'NoName')
                self.assertEqual(first_object.text, 'new-test-post-text')
                self.assertEqual(first_object.group.title, 'new')

    def test_cache(self):
        """При удалении запись остается в кэше index"""
        self.post_last = Post.objects.create(
            author=self.user,
            text='text_deleted',
            group=self.group,)
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.post_last.delete()
        last_post_deleted = response.context['page_obj'][0]
        self.assertEqual(first_object, last_post_deleted)

    def test_follows(self):
        """Авторизованный пользователь может подписываться на других
        пользователей"""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_another}))
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_another}))
        self.assertEqual(Follow.objects.all().count(), 1)
        self.assertEqual(Follow.objects.last().user, self.user)
        self.assertEqual(Follow.objects.last().author, self.user_another)

    def test_unfollows(self):
        """Авторизованный пользователь может удалять из подписок других
        пользователей."""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_another}))
        self.another_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user}))
        self.assertEqual(Follow.objects.all().count(), 2)
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user_another}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_on_author(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан"""
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user_another}))
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']),
                         TOTAL_POSTS - POSTS_AUTHOR_USER)
