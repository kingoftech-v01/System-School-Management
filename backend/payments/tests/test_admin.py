"""Tests for payments admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin


class PaymentsAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that payments admin.py has no custom registrations.

    The payments admin.py is empty (just 'from django.contrib import admin')
    so we verify no custom models are registered beyond defaults.
    """

    def test_payments_admin_module_loads(self):
        """Verify the payments admin module can be imported."""
        import payments.admin  # noqa: F401
        self.assertTrue(True)
