"""Tests for enrollment app Celery tasks."""

from django.test import TestCase

from enrollment.models import RegistrationForm
from enrollment.tasks import (
    generate_enrollment_report,
    cleanup_old_rejected_registrations,
)
from tests.helpers import TestDataMixin


class GenerateEnrollmentReportTest(TestDataMixin, TestCase):
    def test_generates_stats(self):
        tenant = self.create_school()
        reg1 = self.create_registration(tenant=tenant)
        reg2 = self.create_registration(tenant=tenant)
        reg3 = self.create_registration(tenant=tenant)
        # Update statuses directly
        RegistrationForm.objects.filter(pk=reg2.pk).update(status='approved')
        RegistrationForm.objects.filter(pk=reg3.pk).update(status='rejected')

        result = generate_enrollment_report(tenant.pk, '2024-2025')
        self.assertEqual(result['total'], 3)
        self.assertEqual(result['pending'], 1)
        self.assertEqual(result['approved'], 1)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(result['enrolled'], 0)

    def test_filters_by_academic_year(self):
        tenant = self.create_school()
        self.create_registration(tenant=tenant, academic_year='2024-2025')
        self.create_registration(tenant=tenant, academic_year='2023-2024')

        result = generate_enrollment_report(tenant.pk, '2024-2025')
        self.assertEqual(result['total'], 1)

    def test_empty_results(self):
        tenant = self.create_school()
        result = generate_enrollment_report(tenant.pk, '2024-2025')
        self.assertEqual(result['total'], 0)


class CleanupOldRejectedRegistrationsTest(TestDataMixin, TestCase):
    def test_counts_old_rejected(self):
        result = cleanup_old_rejected_registrations()
        self.assertIsInstance(result, int)
