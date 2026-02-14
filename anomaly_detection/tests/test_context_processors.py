"""Tests for anomaly_detection context processors."""

from unittest.mock import MagicMock

from django.test import TestCase, RequestFactory

from anomaly_detection.context_processors import anomaly_alert_count
from tests.helpers import TestDataMixin


class AnomalyAlertCountContextProcessorTest(TestDataMixin, TestCase):
    """Tests for the anomaly_alert_count context processor."""

    def setUp(self):
        self.factory = RequestFactory()

    def _make_request(self, user=None):
        """Create a request with an optional user."""
        request = self.factory.get('/')
        if user:
            request.user = user
        return request

    def test_unauthenticated_user_returns_zero(self):
        """Unauthenticated users get anomaly_alert_count=0."""
        request = self._make_request()
        request.user = MagicMock(is_authenticated=False)
        result = anomaly_alert_count(request)
        self.assertEqual(result['anomaly_alert_count'], 0)

    def test_no_user_attribute_returns_zero(self):
        """Request without a user attribute returns 0."""
        request = self.factory.get('/')
        # Remove user attribute if it exists
        if hasattr(request, 'user'):
            delattr(request, 'user')
        result = anomaly_alert_count(request)
        self.assertEqual(result['anomaly_alert_count'], 0)

    def test_student_role_returns_zero(self):
        """Student users are not privileged, so they get 0."""
        student = self.create_student_user()
        request = self._make_request(user=student)
        result = anomaly_alert_count(request)
        self.assertEqual(result['anomaly_alert_count'], 0)

    def test_direction_user_gets_new_alert_count(self):
        """Direction users see the count of 'new' alerts."""
        direction = self.create_direction_user()
        # Create some new alerts
        at = self.create_anomaly_type(code='ctx_test', domain='grade')
        self.create_anomaly_alert(anomaly_type=at, status='new')
        self.create_anomaly_alert(anomaly_type=at, status='new')
        self.create_anomaly_alert(anomaly_type=at, status='resolved')

        request = self._make_request(user=direction)
        result = anomaly_alert_count(request)
        self.assertEqual(result['anomaly_alert_count'], 2)

    def test_superuser_gets_alert_count(self):
        """Superusers see the count of 'new' alerts regardless of role."""
        admin = self.create_admin_user()
        at = self.create_anomaly_type(code='ctx_super', domain='payment')
        self.create_anomaly_alert(anomaly_type=at, status='new')

        request = self._make_request(user=admin)
        result = anomaly_alert_count(request)
        self.assertEqual(result['anomaly_alert_count'], 1)

    def test_privileged_roles_all_get_counts(self):
        """All privileged roles (direction, admin, accountant, professor,
        secretary, registrar) see alert counts."""
        at = self.create_anomaly_type(code='ctx_priv', domain='enrollment')
        self.create_anomaly_alert(anomaly_type=at, status='new')

        privileged_creators = [
            self.create_direction_user,
            self.create_professor_user,
            self.create_accountant_user,
            self.create_secretary_user,
            self.create_registrar_user,
        ]
        for create_fn in privileged_creators:
            user = create_fn()
            request = self._make_request(user=user)
            result = anomaly_alert_count(request)
            self.assertGreaterEqual(
                result['anomaly_alert_count'], 1,
                f"User with role '{user.role}' should see alert count",
            )
