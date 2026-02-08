"""Tests for certificates app models."""

from django.test import TestCase
from django.utils import timezone

from certificates.models import (
    CertificateTemplate, Certificate, CertificateVerification,
    BatchCertificateGeneration,
)
from tests.helpers import TestDataMixin


class CertificateTemplateTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        tmpl = CertificateTemplate.objects.create(
            name='Completion Certificate',
            body_template='Congrats {student_name}!',
            template_file='templates/cert.html',
        )
        self.assertEqual(str(tmpl), 'Completion Certificate')

    def test_defaults(self):
        tmpl = CertificateTemplate.objects.create(
            name='Default Test',
            body_template='Body',
            template_file='templates/cert.html',
        )
        self.assertTrue(tmpl.is_active)
        self.assertEqual(tmpl.orientation, 'landscape')
        self.assertEqual(tmpl.page_size, 'A4')
        self.assertEqual(tmpl.title_text, 'Certificate of Completion')


class CertificateTest(TestDataMixin, TestCase):
    def _create_cert(self, **kwargs):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        defaults = {
            'student': student,
            'course': course,
        }
        defaults.update(kwargs)
        return Certificate.objects.create(**defaults)

    def test_create_and_str(self):
        cert = self._create_cert()
        self.assertIn('CERT-', str(cert))

    def test_certificate_number_auto_generated(self):
        cert = self._create_cert()
        self.assertTrue(cert.certificate_number.startswith('CERT-'))
        self.assertEqual(len(cert.certificate_number), 18)  # CERT-YYYY-XXXXXXXX

    def test_defaults(self):
        cert = self._create_cert()
        self.assertEqual(cert.status, 'pending')
        self.assertFalse(cert.is_revoked)

    def test_calculate_hash(self):
        cert = self._create_cert()
        hash_val = cert.calculate_hash()
        self.assertEqual(len(hash_val), 64)  # SHA-256

    def test_revoke(self):
        cert = self._create_cert()
        user = self.create_user(role='direction')
        cert.revoke(user, 'Academic dishonesty')
        cert.refresh_from_db()
        self.assertTrue(cert.is_revoked)
        self.assertEqual(cert.status, 'revoked')
        self.assertEqual(cert.revoked_by, user)
        self.assertEqual(cert.revocation_reason, 'Academic dishonesty')
        self.assertIsNotNone(cert.revoked_at)

    def test_unique_together_student_course(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        Certificate.objects.create(student=student, course=course)
        with self.assertRaises(Exception):
            Certificate.objects.create(student=student, course=course)


class CertificateVerificationTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        cert = Certificate.objects.create(student=student, course=course)
        verification = CertificateVerification.objects.create(
            certificate=cert,
            verification_method='number',
            is_valid=True,
        )
        self.assertIn('Verification of', str(verification))


class BatchCertificateGenerationTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        course = self.create_course()
        user = self.create_user(role='direction')
        batch = BatchCertificateGeneration.objects.create(
            course=course, initiated_by=user,
        )
        self.assertIn('Batch generation', str(batch))

    def test_defaults(self):
        course = self.create_course()
        batch = BatchCertificateGeneration.objects.create(
            course=course,
            initiated_by=self.create_user(role='direction'),
        )
        self.assertEqual(batch.status, 'pending')
        self.assertEqual(batch.total_students, 0)
        self.assertEqual(batch.processed_count, 0)
        self.assertEqual(batch.success_count, 0)
        self.assertEqual(batch.failure_count, 0)
