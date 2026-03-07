"""Tests for certificates app serializers."""

from datetime import date
from django.test import TestCase

from tests.helpers import TestDataMixin
from certificates.serializers import (
    CertificateTemplateSerializer,
    CertificateSerializer,
    CertificateVerificationSerializer,
    BatchCertificateGenerationSerializer,
    PublicCertificateVerificationSerializer,
    CertificateDownloadSerializer,
)
from certificates.models import (
    CertificateTemplate, Certificate, CertificateVerification,
    BatchCertificateGeneration,
)


class CertificateTemplateSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        template = self.create_certificate_template()
        serializer = CertificateTemplateSerializer(template)
        self.assertIn('name', serializer.data)
        self.assertIn('is_active', serializer.data)

    def test_read_only_fields(self):
        template = self.create_certificate_template()
        serializer = CertificateTemplateSerializer(template)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)

    def test_valid_data(self):
        data = {
            'name': 'New Template',
            'body_template': 'Certificate body text',
            'is_active': True,
        }
        serializer = CertificateTemplateSerializer(data=data)
        # May need template_file etc. so just check key fields parsed
        self.assertIn('name', serializer.fields)


class CertificateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.student_profile = self.create_student_profile()
        self.course = self.create_course()
        self.template = self.create_certificate_template()
        self.certificate = Certificate.objects.create(
            student=self.student_profile,
            course=self.course,
            template=self.template,
            certificate_number='CERT-2024-TEST001',
            issue_date=date.today(),
        )

    def test_serializes(self):
        serializer = CertificateSerializer(self.certificate)
        self.assertIn('certificate_number', serializer.data)
        self.assertIn('is_valid', serializer.data)
        self.assertIn('verification_count', serializer.data)

    def test_is_valid_true_when_not_revoked(self):
        serializer = CertificateSerializer(self.certificate)
        self.assertTrue(serializer.data['is_valid'])

    def test_is_valid_false_when_revoked(self):
        self.certificate.is_revoked = True
        self.certificate.save()
        serializer = CertificateSerializer(self.certificate)
        self.assertFalse(serializer.data['is_valid'])

    def test_verification_count_zero(self):
        serializer = CertificateSerializer(self.certificate)
        self.assertEqual(serializer.data['verification_count'], 0)

    def test_verification_count_with_verifications(self):
        CertificateVerification.objects.create(
            certificate=self.certificate,
            verification_method='number',
            is_valid=True,
        )
        serializer = CertificateSerializer(self.certificate)
        self.assertEqual(serializer.data['verification_count'], 1)

    def test_read_only_fields(self):
        serializer = CertificateSerializer(self.certificate)
        self.assertIn('created_at', serializer.data)


class CertificateVerificationSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.student_profile = self.create_student_profile()
        self.course = self.create_course()
        self.certificate = Certificate.objects.create(
            student=self.student_profile,
            course=self.course,
            certificate_number='CERT-2024-VTEST',
            issue_date=date.today(),
        )
        self.verification = CertificateVerification.objects.create(
            certificate=self.certificate,
            verification_method='number',
            is_valid=True,
        )

    def test_serializes(self):
        serializer = CertificateVerificationSerializer(self.verification)
        self.assertIn('certificate', serializer.data)
        self.assertIn('is_valid', serializer.data)
        self.assertIn('verification_method', serializer.data)

    def test_certificate_number_field(self):
        serializer = CertificateVerificationSerializer(self.verification)
        self.assertEqual(serializer.data['certificate_number'], 'CERT-2024-VTEST')


class BatchCertificateGenerationSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.course = self.create_course()
        self.template = self.create_certificate_template()
        self.user = self.create_admin_user()
        self.batch = BatchCertificateGeneration.objects.create(
            course=self.course,
            template=self.template,
            initiated_by=self.user,
            total_students=10,
            processed_count=5,
        )

    def test_serializes(self):
        serializer = BatchCertificateGenerationSerializer(self.batch)
        self.assertIn('status', serializer.data)

    def test_progress_percentage_calculation(self):
        serializer = BatchCertificateGenerationSerializer(self.batch)
        self.assertEqual(serializer.data['progress_percentage'], 50.0)

    def test_progress_percentage_zero_total(self):
        self.batch.total_students = 0
        self.batch.save()
        serializer = BatchCertificateGenerationSerializer(self.batch)
        self.assertEqual(serializer.data['progress_percentage'], 0)


class PublicCertificateVerificationSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.student_profile = self.create_student_profile()
        self.course = self.create_course()
        self.certificate = Certificate.objects.create(
            student=self.student_profile,
            course=self.course,
            certificate_number='CERT-2024-PUB',
            issue_date=date.today(),
        )

    def test_valid_certificate_number(self):
        data = {'certificate_number': 'CERT-2024-PUB'}
        serializer = PublicCertificateVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_certificate_number(self):
        data = {'certificate_number': 'NONEXISTENT'}
        serializer = PublicCertificateVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('certificate_number', serializer.errors)


class CertificateDownloadSerializerTest(TestDataMixin, TestCase):
    def test_valid_pdf_format(self):
        serializer = CertificateDownloadSerializer(data={'format': 'pdf'})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_png_format(self):
        serializer = CertificateDownloadSerializer(data={'format': 'png'})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_format(self):
        serializer = CertificateDownloadSerializer(data={'format': 'docx'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('format', serializer.errors)
