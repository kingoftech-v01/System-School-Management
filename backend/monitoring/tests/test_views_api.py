"""
API view tests for the monitoring app.

Tests cover:
- DashboardStatsAPIView (direction-only)
- EnrollmentStatsAPIView (direction-only)
- LibraryStatsAPIView (direction-only)
- ExportDashboardAPIView (direction-only)
- Permission checks for non-direction users
- Unauthenticated access
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


class DashboardStatsAPIViewTests(TestDataMixin, TestCase):
    """Tests for DashboardStatsAPIView."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_dashboard_stats_unauthenticated(self):
        url = reverse('api:monitoring:dashboard-stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_dashboard_stats_forbidden_for_student(self):
        """Students do not have direction permissions."""
        self._auth(self.student)
        url = reverse('api:monitoring:dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_stats_as_admin(self):
        self._auth(self.admin)
        url = reverse('api:monitoring:dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)

    def test_dashboard_stats_as_direction(self):
        self._auth(self.direction)
        url = reverse('api:monitoring:dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EnrollmentStatsAPIViewTests(TestDataMixin, TestCase):
    """Tests for EnrollmentStatsAPIView."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student = self.create_student_user()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_enrollment_stats_unauthenticated(self):
        url = reverse('api:monitoring:enrollment-stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_enrollment_stats_forbidden_for_student(self):
        self._auth(self.student)
        url = reverse('api:monitoring:enrollment-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_enrollment_stats_as_admin(self):
        self._auth(self.admin)
        url = reverse('api:monitoring:enrollment-stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE))


class LibraryStatsAPIViewTests(TestDataMixin, TestCase):
    """Tests for LibraryStatsAPIView."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student = self.create_student_user()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_library_stats_unauthenticated(self):
        url = reverse('api:monitoring:library-stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_library_stats_forbidden_for_student(self):
        self._auth(self.student)
        url = reverse('api:monitoring:library-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_library_stats_as_admin(self):
        self._auth(self.admin)
        url = reverse('api:monitoring:library-stats')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE))


class ExportDashboardAPIViewTests(TestDataMixin, TestCase):
    """Tests for ExportDashboardAPIView."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student = self.create_student_user()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_export_dashboard_unauthenticated(self):
        url = reverse('api:monitoring:export-dashboard')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_export_dashboard_forbidden_for_student(self):
        self._auth(self.student)
        url = reverse('api:monitoring:export-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_export_dashboard_as_admin(self):
        self._auth(self.admin)
        url = reverse('api:monitoring:export-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('metrics', response.data)

    def test_export_dashboard_metrics_keys(self):
        """Export should include students, professors, parents counts."""
        self._auth(self.admin)
        url = reverse('api:monitoring:export-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('students', 'professors', 'parents'):
            self.assertIn(key, response.data['metrics'])

    def test_dashboard_stats_response_structure(self):
        """Dashboard stats should include users and gender_distribution."""
        self._auth(self.admin)
        url = reverse('api:monitoring:dashboard-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertIn('gender_distribution', response.data)

    def test_post_not_allowed_on_dashboard(self):
        """POST method should not be allowed on GET-only dashboard endpoint."""
        self._auth(self.admin)
        url = reverse('api:monitoring:dashboard-stats')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
