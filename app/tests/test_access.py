from django.urls import reverse

from app.models import Destination
from app.tests import LocalTestCase, make_destination, make_user


class AnonymousAccessTest(LocalTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user('owner@example.com')
        self.destination = make_destination(self.owner)

    def anonymous_urls(self):
        return [
            reverse('destination_list'),
            reverse('configuration'),
            reverse('change_password'),
            reverse('destination_history', kwargs={'pk': self.destination.pk}),
            reverse('destination_edit', kwargs={'pk': self.destination.pk}),
            reverse('destination_delete', kwargs={'pk': self.destination.pk}),
            reverse('destination_new', kwargs={'content_type': 'destinationmoduleconfiggroup'}),
        ]

    def test_anonymous_get_redirects_to_login(self):
        login_url = reverse('login')
        for url in self.anonymous_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(login_url, response['Location'])


class DestinationAccessTest(LocalTestCase):
    def setUp(self):
        super().setUp()
        self.owner = make_user('owner@example.com')
        self.other = make_user('other@example.com')
        self.destination = make_destination(self.owner, title='Private')

    def test_owner_can_view_history(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('destination_history', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_open_edit(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('destination_edit', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 200)

    def test_other_user_history_private_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('destination_history', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 404)

    def test_shared_history_visible_to_other_user(self):
        self.destination.shared = True
        self.destination.save()
        self.client.force_login(self.other)
        response = self.client.get(reverse('destination_history', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 200)

    def test_other_user_edit_returns_404(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('destination_edit', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 404)

    def test_other_user_delete_post_returns_404_and_keeps_destination(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse('destination_delete', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Destination.objects.filter(pk=self.destination.pk).exists())

    def test_owner_delete_post_removes_destination(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('destination_delete', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Destination.objects.filter(pk=self.destination.pk).exists())

    def test_delete_view_has_no_get_handler(self):
        # DestinationDeleteView (SingleObjectMixin + View) only defines post(),
        # so GET falls through to View.http_method_not_allowed -> 405.
        self.client.force_login(self.owner)
        response = self.client.get(reverse('destination_delete', kwargs={'pk': self.destination.pk}))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Destination.objects.filter(pk=self.destination.pk).exists())
