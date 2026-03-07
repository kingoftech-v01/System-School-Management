"""Tests for admissions app API views."""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from admissions.models import AdmissionSession, AdmissionStudent


class AdmissionSessionViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = self.create_admission_session()

    def test_list_sessions_public(self):
        resp = self.client.get('/api/v1/admissions/sessions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_session(self):
        resp = self.client.get(f'/api/v1/admissions/sessions/{self.session.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_readonly_no_post(self):
        resp = self.client.post('/api/v1/admissions/sessions/', {'name': 'X'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_inactive_filtered_out(self):
        self.session.is_active = False
        self.session.save()
        resp = self.client.get('/api/v1/admissions/sessions/')
        ids = [s['id'] for s in (resp.data if isinstance(resp.data, list) else resp.data.get('results', []))]
        self.assertNotIn(self.session.pk, ids)


class AdmissionStudentViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.applicant = self.create_admission_student()

    def test_list_students(self):
        resp = self.client.get('/api/v1/admissions/applications/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/admissions/applications/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
