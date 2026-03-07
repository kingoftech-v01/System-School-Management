"""
Deep tests for enrollment forms.
Tests all form classes with valid and invalid data.
"""

from datetime import date, timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from enrollment.forms import (
    RegistrationFormStep1,
    RegistrationFormStep2,
    RegistrationFormStep3,
    RegistrationFormStep4,
    RegistrationEditForm,
    DocumentUploadForm,
    RegistrationReviewForm,
    DocumentVerificationForm,
    EnrollmentSearchForm,
)
from enrollment.models import RegistrationForm, EnrollmentDocument
from tests.helpers import TestDataMixin


class EnrollmentFormMixin(TestDataMixin):
    """Shared helpers for enrollment form tests."""

    def _valid_step1_data(self, **overrides):
        data = {
            'student_first_name': 'John',
            'student_last_name': 'Doe',
            'date_of_birth': date(2010, 1, 15),
            'gender': 'M',
            'nationality': 'American',
            'email': 'john.doe@test.com',
            'phone': '+1234567890',
            'street_address': '123 Main St',
            'city': 'Test City',
            'province': 'Test Province',
            'country': 'Test Country',
        }
        data.update(overrides)
        return data

    def _valid_step2_data(self, **overrides):
        data = {
            'parent_first_name': 'Jane',
            'parent_last_name': 'Doe',
            'parent_email': 'jane.doe@test.com',
            'parent_phone': '+0987654321',
            'parent_relationship': 'mother',
        }
        data.update(overrides)
        return data


class TestRegistrationFormStep1(EnrollmentFormMixin, TestCase):
    """Tests for RegistrationFormStep1."""

    def test_valid_data(self):
        form = RegistrationFormStep1(data=self._valid_step1_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = RegistrationFormStep1(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('student_first_name', form.errors)
        self.assertIn('student_last_name', form.errors)
        self.assertIn('date_of_birth', form.errors)

    def test_optional_middle_name(self):
        data = self._valid_step1_data(student_middle_name='')
        form = RegistrationFormStep1(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_optional_postal_code(self):
        data = self._valid_step1_data(postal_code='')
        form = RegistrationFormStep1(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_dob_too_young(self):
        young_dob = date.today() - timedelta(days=365 * 3)
        data = self._valid_step1_data(date_of_birth=young_dob)
        form = RegistrationFormStep1(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_clean_dob_too_old(self):
        old_dob = date(1920, 1, 1)
        data = self._valid_step1_data(date_of_birth=old_dob)
        form = RegistrationFormStep1(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_clean_dob_exactly_5(self):
        five_years_ago = date.today().replace(year=date.today().year - 5)
        data = self._valid_step1_data(date_of_birth=five_years_ago)
        form = RegistrationFormStep1(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_dob_valid_age(self):
        dob = date(2005, 6, 15)
        data = self._valid_step1_data(date_of_birth=dob)
        form = RegistrationFormStep1(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_email_already_registered(self):
        tenant = self.create_school()
        self.create_registration(
            tenant=tenant, email='taken@test.com', status='approved'
        )
        data = self._valid_step1_data(email='taken@test.com')
        form = RegistrationFormStep1(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_clean_email_pending_ok(self):
        """Email in pending status should not block new registration."""
        tenant = self.create_school()
        self.create_registration(
            tenant=tenant, email='pending@test.com', status='pending'
        )
        data = self._valid_step1_data(email='pending@test.com')
        form = RegistrationFormStep1(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_widgets_have_form_control_class(self):
        form = RegistrationFormStep1()
        for field_name, field in form.fields.items():
            css_class = field.widget.attrs.get('class', '')
            self.assertIn('form-control', css_class,
                          f"Widget for {field_name} missing form-control class")

    def test_gender_choices(self):
        data = self._valid_step1_data(gender='F')
        form = RegistrationFormStep1(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class TestRegistrationFormStep2(EnrollmentFormMixin, TestCase):
    """Tests for RegistrationFormStep2."""

    def test_valid_data(self):
        form = RegistrationFormStep2(data=self._valid_step2_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = RegistrationFormStep2(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('parent_first_name', form.errors)
        self.assertIn('parent_last_name', form.errors)

    def test_optional_middle_name(self):
        data = self._valid_step2_data(parent_middle_name='')
        form = RegistrationFormStep2(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_relationship_choices(self):
        for relationship in ['father', 'mother', 'guardian', 'other']:
            data = self._valid_step2_data(parent_relationship=relationship)
            form = RegistrationFormStep2(data=data)
            self.assertTrue(form.is_valid(), form.errors)


class TestRegistrationFormStep3(EnrollmentFormMixin, TestCase):
    """Tests for RegistrationFormStep3."""

    def test_valid_data(self):
        data = {
            'enrollment_type': 'new',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        }
        form = RegistrationFormStep3(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_with_tenant(self):
        tenant = self.create_school()
        filiere = self.create_filiere(tenant=tenant)
        data = {
            'enrollment_type': 'new',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
            'filiere': filiere.pk,
        }
        form = RegistrationFormStep3(data=data, tenant=tenant)
        self.assertTrue(form.is_valid(), form.errors)

    def test_without_tenant(self):
        """Form should work without tenant (no filiere filtering)."""
        data = {
            'enrollment_type': 'new',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        }
        form = RegistrationFormStep3(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_enrollment_type_choices(self):
        for etype in ['new', 'transfer', 're_enrollment']:
            data = {
                'enrollment_type': etype,
                'academic_year': '2024-2025',
                'level': 'Bachelor',
            }
            form = RegistrationFormStep3(data=data)
            self.assertTrue(form.is_valid(), form.errors)


class TestRegistrationFormStep4(EnrollmentFormMixin, TestCase):
    """Tests for RegistrationFormStep4."""

    def test_valid_data(self):
        data = {
            'special_needs': 'None',
            'medical_information': 'None',
        }
        form = RegistrationFormStep4(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_data_is_valid(self):
        """Both fields are optional."""
        form = RegistrationFormStep4(data={})
        self.assertTrue(form.is_valid(), form.errors)


class TestRegistrationEditForm(EnrollmentFormMixin, TestCase):
    """Tests for RegistrationEditForm."""

    def test_form_has_all_fields(self):
        form = RegistrationEditForm()
        expected_fields = [
            'student_first_name', 'student_last_name', 'status',
            'review_notes', 'rejection_reason',
        ]
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_with_tenant(self):
        tenant = self.create_school()
        form = RegistrationEditForm(tenant=tenant)
        # Should not crash
        self.assertIsNotNone(form.fields['filiere'])

    def test_without_tenant(self):
        form = RegistrationEditForm()
        self.assertIsNotNone(form.fields['filiere'])


class TestDocumentUploadForm(EnrollmentFormMixin, TestCase):
    """Tests for DocumentUploadForm."""

    def _make_file(self, name='test.pdf', size=1024, content_type='application/pdf'):
        content = b'%PDF-' + b'x' * (size - 5)
        return SimpleUploadedFile(name, content, content_type=content_type)

    def test_valid_pdf_upload(self):
        f = self._make_file()
        data = {'document_type': 'birth_certificate', 'description': 'Birth cert'}
        form = DocumentUploadForm(data=data, files={'file': f})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_jpg_upload(self):
        f = self._make_file(name='photo.jpg', content_type='image/jpeg')
        data = {'document_type': 'photo'}
        form = DocumentUploadForm(data=data, files={'file': f})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_png_upload(self):
        f = self._make_file(name='photo.png', content_type='image/png')
        data = {'document_type': 'photo'}
        form = DocumentUploadForm(data=data, files={'file': f})
        self.assertTrue(form.is_valid(), form.errors)

    def test_file_too_large(self):
        f = self._make_file(size=11 * 1024 * 1024)
        data = {'document_type': 'transcript'}
        form = DocumentUploadForm(data=data, files={'file': f})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_invalid_extension(self):
        f = self._make_file(name='test.exe', content_type='application/octet-stream')
        data = {'document_type': 'transcript'}
        form = DocumentUploadForm(data=data, files={'file': f})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_invalid_content_type(self):
        f = self._make_file(
            name='test.pdf',
            content_type='application/x-executable'
        )
        data = {'document_type': 'transcript'}
        form = DocumentUploadForm(data=data, files={'file': f})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

    def test_allowed_extensions(self):
        self.assertIn('.pdf', DocumentUploadForm.ALLOWED_EXTENSIONS)
        self.assertIn('.jpg', DocumentUploadForm.ALLOWED_EXTENSIONS)
        self.assertIn('.jpeg', DocumentUploadForm.ALLOWED_EXTENSIONS)
        self.assertIn('.png', DocumentUploadForm.ALLOWED_EXTENSIONS)
        self.assertIn('.doc', DocumentUploadForm.ALLOWED_EXTENSIONS)
        self.assertIn('.docx', DocumentUploadForm.ALLOWED_EXTENSIONS)

    def test_allowed_content_types(self):
        self.assertIn('application/pdf', DocumentUploadForm.ALLOWED_CONTENT_TYPES)
        self.assertIn('image/jpeg', DocumentUploadForm.ALLOWED_CONTENT_TYPES)
        self.assertIn('image/png', DocumentUploadForm.ALLOWED_CONTENT_TYPES)


class TestRegistrationReviewForm(EnrollmentFormMixin, TestCase):
    """Tests for RegistrationReviewForm."""

    def test_approve_valid(self):
        data = {
            'status': 'approved',
            'review_notes': 'All documents verified',
        }
        form = RegistrationReviewForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_reject_without_reason_invalid(self):
        data = {
            'status': 'rejected',
            'rejection_reason': '',
        }
        form = RegistrationReviewForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('rejection_reason', form.errors)

    def test_reject_with_reason_valid(self):
        data = {
            'status': 'rejected',
            'rejection_reason': 'Missing documents',
        }
        form = RegistrationReviewForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_pending_status_no_reason_needed(self):
        data = {
            'status': 'pending',
        }
        form = RegistrationReviewForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_under_review_status(self):
        data = {
            'status': 'under_review',
            'review_notes': 'Checking documents',
        }
        form = RegistrationReviewForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class TestDocumentVerificationForm(EnrollmentFormMixin, TestCase):
    """Tests for DocumentVerificationForm."""

    def test_verify_document(self):
        form = DocumentVerificationForm(data={'is_verified': True})
        self.assertTrue(form.is_valid(), form.errors)

    def test_unverify_document(self):
        form = DocumentVerificationForm(data={'is_verified': False})
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_defaults_to_false(self):
        form = DocumentVerificationForm(data={})
        self.assertTrue(form.is_valid(), form.errors)


class TestEnrollmentSearchForm(EnrollmentFormMixin, TestCase):
    """Tests for EnrollmentSearchForm."""

    def test_empty_form_valid(self):
        """All fields are optional."""
        form = EnrollmentSearchForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_search_by_name(self):
        form = EnrollmentSearchForm(data={'student_name': 'John'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_search_by_email(self):
        form = EnrollmentSearchForm(data={'email': 'john@test.com'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_search_by_status(self):
        form = EnrollmentSearchForm(data={'status': 'pending'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_search_by_enrollment_type(self):
        form = EnrollmentSearchForm(data={'enrollment_type': 'new'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_search_by_academic_year(self):
        form = EnrollmentSearchForm(data={'academic_year': '2024-2025'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_search_by_date_range(self):
        form = EnrollmentSearchForm(data={
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_with_tenant(self):
        tenant = self.create_school()
        form = EnrollmentSearchForm(data={}, tenant=tenant)
        self.assertTrue(form.is_valid(), form.errors)

    def test_without_tenant(self):
        form = EnrollmentSearchForm(data={})
        self.assertTrue(form.is_valid(), form.errors)
