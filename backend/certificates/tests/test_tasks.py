"""Tests for certificates app Celery tasks."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from certificates.models import (
    Certificate, CertificateTemplate, CertificateVerification,
)
from certificates.tasks import (
    determine_honors,
    cleanup_expired_verifications,
    verify_certificate_integrity,
)
from tests.helpers import TestDataMixin


class DetermineHonorsTest(TestCase):
    def test_summa_cum_laude(self):
        self.assertEqual(determine_honors(95), 'Summa Cum Laude')
        self.assertEqual(determine_honors(100), 'Summa Cum Laude')

    def test_magna_cum_laude(self):
        self.assertEqual(determine_honors(90), 'Magna Cum Laude')
        self.assertEqual(determine_honors(94), 'Magna Cum Laude')

    def test_cum_laude(self):
        self.assertEqual(determine_honors(85), 'Cum Laude')
        self.assertEqual(determine_honors(89), 'Cum Laude')

    def test_no_honors(self):
        self.assertEqual(determine_honors(84), '')
        self.assertEqual(determine_honors(50), '')
        self.assertEqual(determine_honors(0), '')


class CleanupExpiredVerificationsTest(TestDataMixin, TestCase):
    def _make_cert(self):
        template = CertificateTemplate.objects.create(name='Tmpl')
        student_profile = self.create_student_profile()
        course = self.create_course()
        return Certificate.objects.create(
            student=student_profile, course=course,
            template=template, issue_date=timezone.now().date(),
        )

    def test_deletes_old_verifications(self):
        cert = self._make_cert()
        verification = CertificateVerification.objects.create(
            certificate=cert, is_valid=True,
        )
        CertificateVerification.objects.filter(pk=verification.pk).update(
            verified_at=timezone.now() - timedelta(days=731),
        )
        result = cleanup_expired_verifications()
        self.assertFalse(
            CertificateVerification.objects.filter(pk=verification.pk).exists()
        )
        self.assertIn('1', result)

    def test_keeps_recent_verifications(self):
        cert = self._make_cert()
        verification = CertificateVerification.objects.create(
            certificate=cert, is_valid=True,
        )
        result = cleanup_expired_verifications()
        self.assertTrue(
            CertificateVerification.objects.filter(pk=verification.pk).exists()
        )
        self.assertIn('0', result)


class VerifyCertificateIntegrityTest(TestDataMixin, TestCase):
    def _make_cert(self):
        template = CertificateTemplate.objects.create(name='Tmpl2')
        student_profile = self.create_student_profile()
        course = self.create_course()
        return Certificate.objects.create(
            student=student_profile, course=course,
            template=template, issue_date=timezone.now().date(),
        )

    def test_valid_certificates(self):
        cert = self._make_cert()
        # Set hash_signature to the correct hash
        correct_hash = cert.calculate_hash()
        Certificate.objects.filter(pk=cert.pk).update(
            hash_signature=correct_hash,
        )
        result = verify_certificate_integrity()
        self.assertIn('found 0', result)

    def test_detects_tampered(self):
        cert = self._make_cert()
        Certificate.objects.filter(pk=cert.pk).update(
            hash_signature='tampered_hash_value',
        )
        result = verify_certificate_integrity()
        self.assertIn('found 1', result)
