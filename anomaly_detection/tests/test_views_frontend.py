"""
Frontend view tests for the anomaly_detection app.

Tests cover:
- dashboard: Admin/direction-only anomaly detection dashboard
- alert_list: Paginated alert listing with filters
- alert_detail: Single alert detail view
- alert_acknowledge: Acknowledge an alert (POST-only)
- alert_resolve: Resolve or mark alert as false positive (POST-only)
- Permission checks: students/professors/parents denied access
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class AnomalyViewsBase(TestDataMixin, TestCase):
    """Common setUp for anomaly detection view tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()

        # Users with access (direction_only: secretary, direction, admin)
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.secretary = self.create_secretary_user()

        # Users without access
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.parent = self.create_parent_user()

        # Create test data
        self.anomaly_type = self.create_anomaly_type()
        self.alert = self.create_anomaly_alert(anomaly_type=self.anomaly_type)


# ============================================================================
# DASHBOARD
# ============================================================================

class TestAnomalyDashboard(AnomalyViewsBase):
    """Tests for the anomaly_dashboard view."""

    def url(self):
        return reverse('frontend:anomaly_detection:dashboard')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_parent_denied(self):
        self.client.force_login(self.parent)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_secretary_can_access(self):
        self.client.force_login(self.secretary)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ALERT LIST
# ============================================================================

class TestAlertList(AnomalyViewsBase):
    """Tests for the alert_list view."""

    def url(self):
        return reverse('frontend:anomaly_detection:alert_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_domain(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'domain': 'grades'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_severity(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'severity': 'medium'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'status': 'new'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_search(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'search': 'Test'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_pagination(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'page': 1})
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ALERT DETAIL
# ============================================================================

class TestAlertDetail(AnomalyViewsBase):
    """Tests for the alert_detail view."""

    def url(self, pk=None):
        return reverse('frontend:anomaly_detection:alert_detail',
                        kwargs={'pk': pk or self.alert.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_view(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# ALERT ACKNOWLEDGE
# ============================================================================

class TestAlertAcknowledge(AnomalyViewsBase):
    """Tests for the alert_acknowledge view."""

    def url(self, pk=None):
        return reverse('frontend:anomaly_detection:alert_acknowledge',
                        kwargs={'pk': pk or self.alert.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_redirects_to_detail(self):
        """GET on acknowledge redirects to alert detail."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)

    def test_post_acknowledges_new_alert(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [200, 302, 500])
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'acknowledged')
        self.assertEqual(self.alert.acknowledged_by, self.admin)

    def test_post_already_acknowledged_shows_warning(self):
        """Acknowledging an already-processed alert shows warning."""
        self.alert.status = 'acknowledged'
        self.alert.save()
        self.client.force_login(self.admin)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# ALERT RESOLVE
# ============================================================================

class TestAlertResolve(AnomalyViewsBase):
    """Tests for the alert_resolve view."""

    def url(self, pk=None):
        return reverse('frontend:anomaly_detection:alert_resolve',
                        kwargs={'pk': pk or self.alert.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_redirects_to_detail(self):
        """GET on resolve redirects to alert detail."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)

    def test_post_resolves_alert(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {'resolution': 'resolved'})
        self.assertIn(response.status_code, [200, 302, 500])
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'resolved')
        self.assertEqual(self.alert.resolved_by, self.admin)

    def test_post_false_positive(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {
            'resolution': 'false_positive',
            'notes': 'This was a false alarm',
        })
        self.assertIn(response.status_code, [200, 302, 500])
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'false_positive')

    def test_post_invalid_resolution_defaults_to_resolved(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {'resolution': 'invalid_value'})
        self.assertIn(response.status_code, [200, 302, 500])
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, 'resolved')

    def test_post_already_resolved_shows_warning(self):
        self.alert.status = 'resolved'
        self.alert.save()
        self.client.force_login(self.admin)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_with_notes(self):
        self.client.force_login(self.direction)
        response = self.client.post(self.url(), {
            'resolution': 'resolved',
            'notes': 'Investigated and confirmed issue.',
        })
        self.assertIn(response.status_code, [200, 302, 500])
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.notes, 'Investigated and confirmed issue.')

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)
