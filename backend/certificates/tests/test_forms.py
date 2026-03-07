"""Tests for certificates app forms."""

from django.test import TestCase

from certificates.forms import (
    CertificateVerificationForm, CertificateForm,
    BatchCertificateGenerationForm,
)
from certificates.models import Certificate, CertificateTemplate
from tests.helpers import TestDataMixin


class CertificateVerificationFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = CertificateVerificationForm(data={
            'certificate_number': 'cert-2024-abc12345',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_normalizes_to_uppercase(self):
        form = CertificateVerificationForm(data={
            'certificate_number': 'cert-2024-abc12345',
        })
        form.is_valid()
        self.assertEqual(form.cleaned_data['certificate_number'], 'CERT-2024-ABC12345')

    def test_strips_whitespace(self):
        form = CertificateVerificationForm(data={
            'certificate_number': '  CERT-2024-ABC  ',
        })
        form.is_valid()
        self.assertEqual(form.cleaned_data['certificate_number'], 'CERT-2024-ABC')


class CertificateFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        tmpl = CertificateTemplate.objects.create(
            name='Test Tmpl', body_template='Body',
            template_file='templates/cert.html', is_active=True,
        )
        form = CertificateForm(data={
            'student': student.pk,
            'course': course.pk,
            'template': tmpl.pk,
            'grade': 'A',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_student_course(self):
        from certificates.models import Certificate
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        course = self.create_course()
        Certificate.objects.create(student=student, course=course)
        form = CertificateForm(data={
            'student': student.pk,
            'course': course.pk,
        })
        self.assertFalse(form.is_valid())


class BatchCertificateGenerationFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        course = self.create_course()
        tmpl = CertificateTemplate.objects.create(
            name='Batch Template', body_template='Body',
            template_file='templates/cert.html', is_active=True,
        )
        form = BatchCertificateGenerationForm(data={
            'course': course.pk,
            'template': tmpl.pk,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_inactive_template(self):
        course = self.create_course()
        tmpl = CertificateTemplate.objects.create(
            name='Inactive', body_template='Body',
            template_file='templates/cert.html', is_active=False,
        )
        form = BatchCertificateGenerationForm(data={
            'course': course.pk,
            'template': tmpl.pk,
        })
        self.assertFalse(form.is_valid())
