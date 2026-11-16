from django.contrib.auth import get_user_model
from django.urls import reverse

from app.tests import LocalTestCase, make_user

User = get_user_model()


class SignupTest(LocalTestCase):
    def test_signup_creates_user_and_redirects_to_login(self):
        response = self.client.post(reverse('signup'), {
            'username': 'new@example.com',
            'password1': 's3cret-pw',
            'password2': 's3cret-pw',
        })
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(email='new@example.com')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('s3cret-pw'))
        self.assertNotEqual(user.password, 's3cret-pw')


class LoginRememberTest(LocalTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(password='s3cret-pw')

    def test_login_without_remember_expires_at_browser_close(self):
        response = self.client.post(reverse('login'), {
            'username': self.user.email,
            'password': 's3cret-pw',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_with_remember_does_not_expire_at_browser_close(self):
        response = self.client.post(reverse('login'), {
            'username': self.user.email,
            'password': 's3cret-pw',
            'remember': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get_expire_at_browser_close())


class ChangePasswordTest(LocalTestCase):
    def setUp(self):
        super().setUp()
        self.user = make_user(password='old-pw')
        self.client.force_login(self.user)

    def test_wrong_old_password_rejected(self):
        response = self.client.post(reverse('change_password'), {
            'old_password': 'wrong-pw',
            'new_password1': 'new-pw',
            'new_password2': 'new-pw',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old-pw'))
        self.assertFalse(self.user.check_password('new-pw'))

    def test_correct_old_password_changes_password(self):
        response = self.client.post(reverse('change_password'), {
            'old_password': 'old-pw',
            'new_password1': 'new-pw',
            'new_password2': 'new-pw',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('new-pw'))
        self.client.logout()
        self.assertTrue(self.client.login(email=self.user.email, password='new-pw'))
