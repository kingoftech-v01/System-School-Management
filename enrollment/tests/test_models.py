"""Tests for enrollment app models."""

from datetime import date
from django.test import TestCase

from enrollment.models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory
from tests.helpers import TestDataMixin


class RegistrationFormModelTest(TestDataMixin, TestCase):
    def test_create_registration(self):
        reg = self.create_registration()
        self.assertIsNotNone(reg.pk)

    def test_default_status_pending(self):
        reg = self.create_registration()
        self.assertEqual(reg.status, 'pending')

    def test_str_contains_name_and_status(self):
        reg = self.create_registration(student_name='John Doe')
        result = str(reg)
        self.assertIn('John Doe', result)
        self.assertIn('Pending', result)

    def test_submitted_at_set(self):
        reg = self.create_registration()
        self.assertIsNotNone(reg.submitted_at)

    def test_can_enroll_pending(self):
        reg = self.create_registration(status='pending')
        self.assertFalse(reg.can_enroll())

    def test_can_enroll_approved(self):
        reg = self.create_registration(status='approved')
        self.assertTrue(reg.can_enroll())

    def test_can_enroll_already_enrolled(self):
        user = self.create_user(role='direction')
        reg = self.create_registration(status='approved', enrolled_user=user)
        self.assertFalse(reg.can_enroll())

    def test_can_enroll_rejected(self):
        reg = self.create_registration(status='rejected')
        self.assertFalse(reg.can_enroll())

    def test_completion_percentage_without_filiere(self):
        reg = self.create_registration()
        pct = reg.get_completion_percentage()
        self.assertLess(pct, 100)

    def test_completion_percentage_with_filiere(self):
        filiere = self.create_filiere()
        reg = self.create_registration(filiere=filiere)
        pct = reg.get_completion_percentage()
        self.assertGreater(pct, 0)

    def test_save_sets_reviewed_at_on_approve(self):
        reg = self.create_registration(status='pending')
        self.assertIsNone(reg.reviewed_at)
        reg.status = 'approved'
        reg.save()
        reg.refresh_from_db()
        self.assertIsNotNone(reg.reviewed_at)

    def test_save_sets_reviewed_at_on_reject(self):
        reg = self.create_registration(status='pending')
        reg.status = 'rejected'
        reg.save()
        reg.refresh_from_db()
        self.assertIsNotNone(reg.reviewed_at)


class EnrollmentDocumentModelTest(TestDataMixin, TestCase):
    def test_create_document(self):
        reg = self.create_registration()
        doc = EnrollmentDocument.objects.create(
            registration=reg,
            document_type='birth_certificate',
            description='Birth cert copy',
        )
        self.assertIsNotNone(doc.pk)

    def test_default_not_verified(self):
        reg = self.create_registration()
        doc = EnrollmentDocument.objects.create(
            registration=reg,
            document_type='photo',
        )
        self.assertFalse(doc.is_verified)

    def test_str(self):
        reg = self.create_registration(student_name='Alice')
        doc = EnrollmentDocument.objects.create(
            registration=reg,
            document_type='birth_certificate',
        )
        result = str(doc)
        self.assertIn('Birth Certificate', result)


class EnrollmentStatusHistoryModelTest(TestDataMixin, TestCase):
    def test_create_history(self):
        reg = self.create_registration()
        user = self.create_admin_user()
        history = EnrollmentStatusHistory.objects.create(
            registration=reg,
            old_status='pending',
            new_status='approved',
            changed_by=user,
            notes='Approved by admin',
        )
        self.assertIsNotNone(history.pk)

    def test_str(self):
        reg = self.create_registration(student_name='Bob')
        history = EnrollmentStatusHistory.objects.create(
            registration=reg,
            old_status='pending',
            new_status='approved',
        )
        result = str(history)
        self.assertIn('Bob', result)

    def test_changed_at_auto_set(self):
        reg = self.create_registration()
        history = EnrollmentStatusHistory.objects.create(
            registration=reg,
            old_status='pending',
            new_status='under_review',
        )
        self.assertIsNotNone(history.changed_at)
