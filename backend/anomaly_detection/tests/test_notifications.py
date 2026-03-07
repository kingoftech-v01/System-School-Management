"""Tests for anomaly_detection notifications.

Note: notify_anomaly uses a lazy (local) import for send_html_email:
    from core.utils import send_html_email
So we must patch it at 'core.utils.send_html_email' (its source module),
NOT at 'anomaly_detection.notifications.send_html_email'.
"""

from unittest.mock import patch, MagicMock

from django.test import TestCase

from anomaly_detection.notifications import notify_anomaly
from tests.helpers import TestDataMixin


class NotifyAnomalyTest(TestDataMixin, TestCase):
    """Tests for the notify_anomaly function."""

    def _create_alert_with_roles(self, roles=None):
        """Create an anomaly alert with the given notify_roles."""
        at = self.create_anomaly_type(
            code='notify_test_type',
            domain='grade',
            notify_roles=roles or ['direction', 'admin'],
        )
        return self.create_anomaly_alert(anomaly_type=at)

    def test_no_recipients_logs_and_returns(self):
        """When no users match the roles, notify_anomaly returns without sending."""
        alert = self._create_alert_with_roles(roles=['nonexistent_role'])
        # Should not raise even though there are no matching users
        notify_anomaly(alert)
        alert.refresh_from_db()
        self.assertFalse(alert.email_sent)

    @patch('core.utils.send_html_email')
    def test_sends_email_to_matching_users(self, mock_send):
        """When matching users exist, sends email and marks email_sent=True."""
        # Create users with roles matching the anomaly type
        self.create_direction_user(email='director@test.com')
        self.create_admin_user(email='admin@test.com')

        alert = self._create_alert_with_roles(roles=['direction', 'admin'])
        notify_anomaly(alert)

        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args
        # Check that the email subject contains the severity and title
        subject = call_kwargs[1].get('subject') if call_kwargs[1] else call_kwargs[0][0]
        self.assertIn('Anomaly', subject)

        alert.refresh_from_db()
        self.assertTrue(alert.email_sent)

    @patch('core.utils.send_html_email')
    def test_excludes_users_with_empty_email(self, mock_send):
        """Users with empty email addresses are excluded from recipients."""
        self.create_direction_user(email='')
        alert = self._create_alert_with_roles(roles=['direction'])

        notify_anomaly(alert)
        # No email should have been sent because the only matching user has no email
        mock_send.assert_not_called()

    @patch('core.utils.send_html_email')
    def test_excludes_inactive_users(self, mock_send):
        """Inactive users are excluded from recipients."""
        self.create_direction_user(email='inactive@test.com', is_active=False)
        alert = self._create_alert_with_roles(roles=['direction'])

        notify_anomaly(alert)
        mock_send.assert_not_called()

    @patch('core.utils.send_html_email', side_effect=Exception('SMTP error'))
    def test_email_failure_does_not_raise(self, mock_send):
        """If email sending fails, the exception is caught and logged."""
        self.create_direction_user(email='director@test.com')
        alert = self._create_alert_with_roles(roles=['direction'])

        # Should not raise
        notify_anomaly(alert)
        alert.refresh_from_db()
        self.assertFalse(alert.email_sent)

    @patch('core.utils.send_html_email')
    def test_default_roles_when_notify_roles_empty(self, mock_send):
        """When notify_roles is empty, defaults to ['direction', 'admin']."""
        at = self.create_anomaly_type(
            code='default_roles',
            domain='grade',
            notify_roles=[],
        )
        alert = self.create_anomaly_alert(anomaly_type=at)

        # Create matching users for the default roles
        self.create_direction_user(email='default_dir@test.com')
        self.create_admin_user(email='default_admin@test.com')

        notify_anomaly(alert)
        mock_send.assert_called_once()
