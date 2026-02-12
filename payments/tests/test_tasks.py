"""
Tests for payments app Celery tasks.
All tasks are stub implementations (pass only), so we verify they
can be called directly without errors and return None.
"""

from django.test import TestCase

from payments.tasks import (
    generate_monthly_invoices,
    process_failed_payments,
    send_payment_reminders,
)
from tests.helpers import TestDataMixin


class TestSendPaymentReminders(TestDataMixin, TestCase):
    """Tests for send_payment_reminders task."""

    def test_task_runs_without_error(self):
        """Task should execute without raising errors."""
        result = send_payment_reminders()
        self.assertIsNone(result)

    def test_task_returns_none(self):
        """Stub task should return None."""
        self.assertIsNone(send_payment_reminders())


class TestProcessFailedPayments(TestDataMixin, TestCase):
    """Tests for process_failed_payments task."""

    def test_task_runs_without_error(self):
        """Task should execute without raising errors."""
        result = process_failed_payments()
        self.assertIsNone(result)

    def test_task_returns_none(self):
        """Stub task should return None."""
        self.assertIsNone(process_failed_payments())


class TestGenerateMonthlyInvoices(TestDataMixin, TestCase):
    """Tests for generate_monthly_invoices task."""

    def test_task_runs_without_error(self):
        """Task should execute without raising errors."""
        result = generate_monthly_invoices()
        self.assertIsNone(result)

    def test_task_returns_none(self):
        """Stub task should return None."""
        self.assertIsNone(generate_monthly_invoices())
