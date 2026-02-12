"""Tests for anomaly_detection models: AnomalyType, AnomalyThreshold, AnomalyAlert."""

from django.test import TestCase

from anomaly_detection.models import AnomalyType, AnomalyThreshold, AnomalyAlert
from tests.helpers import TestDataMixin


class AnomalyTypeModelTest(TestDataMixin, TestCase):
    """Tests for the AnomalyType model."""

    def test_create_anomaly_type_defaults(self):
        """AnomalyType can be created with minimal fields."""
        at = AnomalyType.objects.create(
            code='test_code',
            name='Test Anomaly',
            domain='grade',
        )
        self.assertEqual(at.severity, 'medium')
        self.assertTrue(at.is_enabled)
        self.assertEqual(at.notify_roles, [])

    def test_str_representation(self):
        """AnomalyType.__str__ shows domain display and name."""
        at = AnomalyType.objects.create(
            code='grade_jump',
            name='Grade Jump',
            domain='grade',
        )
        result = str(at)
        self.assertIn('Grade', result)
        self.assertIn('Grade Jump', result)

    def test_domain_choices(self):
        """All DOMAIN_CHOICES values are valid."""
        valid_domains = [d[0] for d in AnomalyType.DOMAIN_CHOICES]
        for domain in ('grade', 'payment', 'enrollment', 'login', 'academic'):
            self.assertIn(domain, valid_domains)

    def test_severity_choices(self):
        """All SEVERITY_CHOICES values are valid."""
        valid_severities = [s[0] for s in AnomalyType.SEVERITY_CHOICES]
        for severity in ('low', 'medium', 'high', 'critical'):
            self.assertIn(severity, valid_severities)

    def test_ordering(self):
        """AnomalyType orders by domain, severity, code."""
        AnomalyType.objects.create(code='z_code', name='Z', domain='payment', severity='high')
        AnomalyType.objects.create(code='a_code', name='A', domain='grade', severity='low')
        types = list(AnomalyType.objects.values_list('code', flat=True))
        # grade < payment alphabetically
        self.assertEqual(types[0], 'a_code')

    def test_unique_code_constraint(self):
        """AnomalyType.code must be unique."""
        AnomalyType.objects.create(code='unique_test', name='First', domain='grade')
        with self.assertRaises(Exception):
            AnomalyType.objects.create(code='unique_test', name='Second', domain='payment')

    def test_notify_roles_stores_json_list(self):
        """notify_roles can store a list of role strings."""
        at = AnomalyType.objects.create(
            code='notify_test',
            name='Notify Test',
            domain='grade',
            notify_roles=['direction', 'admin', 'professor'],
        )
        at.refresh_from_db()
        self.assertEqual(at.notify_roles, ['direction', 'admin', 'professor'])


class AnomalyThresholdModelTest(TestDataMixin, TestCase):
    """Tests for the AnomalyThreshold model."""

    def test_create_threshold(self):
        """AnomalyThreshold links to AnomalyType with a key-value pair."""
        at = self.create_anomaly_type(code='thresh_parent', domain='grade')
        threshold = AnomalyThreshold.objects.create(
            anomaly_type=at,
            key='std_dev_multiplier',
            value=2.5,
        )
        self.assertEqual(str(threshold), f'{at.code}.std_dev_multiplier = 2.5')

    def test_unique_together_anomaly_type_key(self):
        """Same (anomaly_type, key) pair cannot be duplicated."""
        at = self.create_anomaly_type(code='thresh_unique', domain='grade')
        AnomalyThreshold.objects.create(anomaly_type=at, key='max_val', value=10)
        with self.assertRaises(Exception):
            AnomalyThreshold.objects.create(anomaly_type=at, key='max_val', value=20)


class AnomalyAlertModelTest(TestDataMixin, TestCase):
    """Tests for the AnomalyAlert model."""

    def test_create_alert_defaults(self):
        """AnomalyAlert default status is 'new' and email_sent is False."""
        alert = self.create_anomaly_alert()
        self.assertEqual(alert.status, 'new')
        self.assertFalse(alert.email_sent)

    def test_str_representation(self):
        """AnomalyAlert.__str__ shows severity display and title."""
        at = self.create_anomaly_type(code='str_test', domain='payment')
        alert = self.create_anomaly_alert(
            anomaly_type=at,
            severity='high',
            title='Test Alert Title',
        )
        result = str(alert)
        self.assertIn('High', result)
        self.assertIn('Test Alert Title', result)

    def test_status_choices(self):
        """All STATUS_CHOICES are valid."""
        valid = [s[0] for s in AnomalyAlert.STATUS_CHOICES]
        for status in ('new', 'acknowledged', 'resolved', 'false_positive'):
            self.assertIn(status, valid)

    def test_alert_with_user(self):
        """AnomalyAlert can be associated with a user."""
        user = self.create_user()
        alert = self.create_anomaly_alert(user=user)
        self.assertEqual(alert.user, user)

    def test_alert_ordering_by_detected_at_desc(self):
        """Alerts are ordered by -detected_at."""
        at = self.create_anomaly_type(code='order_test', domain='grade')
        a1 = self.create_anomaly_alert(anomaly_type=at, title='First')
        a2 = self.create_anomaly_alert(anomaly_type=at, title='Second')
        alerts = list(AnomalyAlert.objects.filter(anomaly_type=at))
        # Second created should appear first (more recent)
        self.assertEqual(alerts[0].pk, a2.pk)

    def test_alert_details_stores_json(self):
        """AnomalyAlert.details can store structured JSON data."""
        alert = self.create_anomaly_alert(
            details={'key': 'value', 'count': 42},
        )
        alert.refresh_from_db()
        self.assertEqual(alert.details['key'], 'value')
        self.assertEqual(alert.details['count'], 42)
