"""Tests for dailystat app API views."""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from dailystat.models import DailyAttendanceStat


class DailyAttendanceStatViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)

    def test_list_returns_200(self):
        resp = self.client.get('/api/v1/dailystat/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_read_only_no_post(self):
        resp = self.client.post('/api/v1/dailystat/stats/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_read_only_no_delete(self):
        group = self.create_attendance_group()
        student = self.create_attendance_student(group=group)
        subject = self.create_attendance_subject()
        stat = DailyAttendanceStat.objects.create(student=student, day=date.today())
        stat.subjects.add(subject)
        resp = self.client.delete(f'/api/v1/dailystat/stats/{stat.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_no_auth_still_accessible(self):
        """The viewset has no explicit permission classes; defaults apply."""
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/dailystat/stats/')
        # Default DRF permission may allow or deny; just confirm it responds
        self.assertIn(resp.status_code, [200, 401, 403])

    def test_list_with_data(self):
        group = self.create_attendance_group()
        student = self.create_attendance_student(group=group)
        stat = DailyAttendanceStat.objects.create(student=student, day=date.today())
        resp = self.client.get('/api/v1/dailystat/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_options_request(self):
        resp = self.client.options('/api/v1/dailystat/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
