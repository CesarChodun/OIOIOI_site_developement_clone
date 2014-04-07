import json
from django.core.urlresolvers import reverse
from django.test import TestCase

class TestNotifications(TestCase):
    fixtures = ['test_users']

    def test_notifications(self):
        self.client.login(username='test_user')
        url = reverse('notifications_authenticate')
        response = self.client.get(url)
        resp_obj = json.loads(response.content)
        self.assertEqual(resp_obj['status'], 'OK')
        self.assertEqual(resp_obj['user'], 'test_user')
        self.client.logout()
        response = self.client.get(url)
        resp_obj = json.loads(response.content)
        self.assertEqual(resp_obj['status'], 'UNAUTHORIZED')
