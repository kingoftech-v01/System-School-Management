"""Tests for notices app API views."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from notices.models import Notice


class NoticeViewSetTest(TestDataMixin, TestCase):
    """Tests for the NoticeViewSet.

    Note: The notices API filters by request.tenant, which is not available in
    the test client by default. We test authentication, permissions, and basic
    connectivity here.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()

    def test_unauthenticated_denied(self):
        resp = self.client.get('/api/v1/notices/notices/')
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_authenticated_can_access(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get('/api/v1/notices/notices/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_active_action_requires_auth(self):
        resp = self.client.get('/api/v1/notices/notices/active/')
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_create_requires_auth(self):
        data = {'title': 'Test', 'content': 'Test content', 'priority': 'normal'}
        resp = self.client.post('/api/v1/notices/notices/', data, format='json')
        self.assertIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_notice_model_str(self):
        notice = Notice.objects.create(title='Test Notice', content='Content')
        self.assertEqual(str(notice), 'Test Notice')

    def test_notice_is_expired_no_expiry(self):
        notice = Notice.objects.create(title='No Expiry', content='Content')
        self.assertFalse(notice.is_expired())
