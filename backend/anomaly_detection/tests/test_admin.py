"""Tests for anomaly_detection admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from anomaly_detection.models import AnomalyType, AnomalyAlert
from anomaly_detection.admin import AnomalyTypeAdmin, AnomalyAlertAdmin


class AnomalyDetectionAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all anomaly_detection models are registered in the admin."""

    def test_anomaly_type_registered(self):
        self.assertIn(AnomalyType, admin.site._registry)

    def test_anomaly_alert_registered(self):
        self.assertIn(AnomalyAlert, admin.site._registry)


class AnomalyTypeAdminTest(TestDataMixin, TestCase):
    """Test AnomalyTypeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AnomalyTypeAdmin(AnomalyType, self.site)

    def test_list_display(self):
        expected = ['code', 'name', 'domain', 'severity', 'is_enabled']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ['domain', 'severity', 'is_enabled']
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ['code', 'name']
        self.assertEqual(self.admin.search_fields, expected)

    def test_inlines(self):
        from anomaly_detection.admin import AnomalyThresholdInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(AnomalyThresholdInline, inline_classes)


class AnomalyAlertAdminTest(TestDataMixin, TestCase):
    """Test AnomalyAlertAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AnomalyAlertAdmin(AnomalyAlert, self.site)

    def test_list_display(self):
        expected = ['title', 'anomaly_type', 'severity', 'status', 'user', 'detected_at', 'email_sent']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ['severity', 'status', 'anomaly_type__domain', 'email_sent']
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ['title', 'user__username', 'user__first_name', 'user__last_name']
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ['detected_at', 'acknowledged_at', 'resolved_at', 'details']
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'detected_at')
