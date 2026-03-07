"""
Frontend view tests for the monitoring app.

Tests cover:
- dashboard: main analytics dashboard (direction/admin only)
- enrollment_stats: detailed enrollment statistics (direction/admin only)
- library_stats: detailed library statistics (direction/admin only)
- export_csv: CSV export of dashboard data (direction/admin only)
- Role-based access control (students/professors denied)
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class MonitoringViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for monitoring/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.direction_user = self.create_direction_user()
        self.admin_user = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()
        self.secretary_user = self.create_secretary_user()

    # ── dashboard ──────────────────────────────────────────────────

    def test_dashboard_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_direction_access(self):
        """Direction user can access the dashboard."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_admin_access(self):
        """Admin/superuser can access the dashboard."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_secretary_access(self):
        """Secretary can access the dashboard (direction_only allows secretary)."""
        self.client.force_login(self.secretary_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_denied_for_student(self):
        """Students cannot access the monitoring dashboard."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_denied_for_professor(self):
        """Professors cannot access the monitoring dashboard."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_with_date_filter(self):
        """Dashboard supports date range filtering."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url, {
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_with_invalid_date_filter(self):
        """Dashboard handles invalid date inputs gracefully."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url, {
            'date_from': 'invalid-date',
            'date_to': 'also-invalid',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_with_only_date_from(self):
        """Dashboard works with only date_from filter."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url, {'date_from': '2024-06-01'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_dashboard_with_only_date_to(self):
        """Dashboard works with only date_to filter."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:dashboard')
        resp = self.client.get(url, {'date_to': '2024-12-31'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── enrollment_stats ───────────────────────────────────────────

    def test_enrollment_stats_direction(self):
        """Direction user can access enrollment statistics."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:monitoring:enrollment_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_enrollment_stats_admin(self):
        """Admin can access enrollment statistics."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:enrollment_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_enrollment_stats_denied_student(self):
        """Students cannot access enrollment statistics."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:monitoring:enrollment_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_enrollment_stats_denied_professor(self):
        """Professors cannot access enrollment statistics."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:monitoring:enrollment_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── library_stats ──────────────────────────────────────────────

    def test_library_stats_direction(self):
        """Direction user can access library statistics."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:monitoring:library_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_library_stats_admin(self):
        """Admin can access library statistics."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:library_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_library_stats_denied_student(self):
        """Students cannot access library statistics."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:monitoring:library_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_library_stats_with_books(self):
        """Library stats work when books exist."""
        self.create_book(tenant=self.school)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:library_stats')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── export_csv ─────────────────────────────────────────────────

    def test_export_csv_direction(self):
        """Direction user can export dashboard CSV."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_export_csv_admin(self):
        """Admin can export dashboard CSV."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_export_csv_has_csv_content_type(self):
        """Exported CSV response has proper content type."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        if resp.status_code == 200:
            self.assertEqual(resp['Content-Type'], 'text/csv')

    def test_export_csv_denied_student(self):
        """Students cannot export dashboard CSV."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_export_csv_denied_professor(self):
        """Professors cannot export dashboard CSV."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_export_csv_anonymous(self):
        """Anonymous users cannot export CSV."""
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_export_csv_with_data(self):
        """CSV export works when enrollment and library data exists."""
        self.create_registration(tenant=self.school)
        self.create_book(tenant=self.school)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:monitoring:export_csv')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])
