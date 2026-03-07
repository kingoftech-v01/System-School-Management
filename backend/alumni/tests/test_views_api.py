"""Tests for alumni app API views."""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from alumni.models import Alumni, AlumniEvent


class AlumniViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.alumni = self.create_alumni()

    def test_list_alumni(self):
        resp = self.client.get('/api/v1/alumni/alumni/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_alumni(self):
        resp = self.client.get(f'/api/v1/alumni/alumni/{self.alumni.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_inactive_filtered_out(self):
        self.alumni.is_active = False
        self.alumni.save()
        resp = self.client.get('/api/v1/alumni/alumni/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [a['id'] for a in (resp.data if isinstance(resp.data, list) else resp.data.get('results', []))]
        self.assertNotIn(self.alumni.pk, ids)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/alumni/alumni/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AlumniEventViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.event = self.create_alumni_event()

    def test_list_events(self):
        resp = self.client.get('/api/v1/alumni/events/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_event(self):
        resp = self.client.get(f'/api/v1/alumni/events/{self.event.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
