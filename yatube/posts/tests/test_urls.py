from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Group, Post, User


class PostUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoName')
        cls.user_another = User.objects.create_user(username='I_is_not_NoName')
        cls.group = Group.objects.create(
            title='test-text',
            slug='test-slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test-post-text',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author.force_login(self.user_another)

    def test_url_exists_at_desired_location(self):
        """Страницы доступные любому пользователю."""
        url_names = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status_code in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_url_exists_at_desired_location_authorized(self):
        """Страницы недоступны гостю."""
        url_names = {
            '/create/': HTTPStatus.FOUND,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
        }
        for address, status_code in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_post_edit_url_exists_at_desired_location_author(self):
        """Страница /posts/<post_id>/edit/ доступна автору."""
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_not_author(self):
        """Страница /posts/<post_id>/edit/ перенаправляет не авторов."""
        clients = {
            self.guest_client:
                f'/auth/login/?next=/posts/{self.post.id}/edit/',
            self.authorized_client_not_author:
                f'/posts/{self.post.id}/',
        }
        for user_status, redirect in clients.items():
            with self.subTest(user_status=user_status):
                response = user_status.get(
                    f'/posts/{self.post.id}/edit/', follow=True)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template, in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
