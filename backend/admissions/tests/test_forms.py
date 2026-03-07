"""Tests for admissions app forms."""

from datetime import date
from django.test import TestCase

from tests.helpers import TestDataMixin
from admissions.forms import AdmissionApplicationForm, CounselingCommentForm, AdmissionStatusForm


class AdmissionApplicationFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.session = self.create_admission_session()

    def test_valid_form(self):
        data = {
            'session': self.session.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'phone': '1234567890',
            'gender': 'M',
            'date_of_birth': '2005-01-01',
            'guardian_first_name': 'Jane',
            'guardian_last_name': 'Doe',
            'guardian_phone': '0987654321',
        }
        form = AdmissionApplicationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = AdmissionApplicationForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('email', form.errors)

    def test_invalid_email(self):
        data = {
            'session': self.session.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'not-an-email',
            'phone': '1234567890',
            'gender': 'M',
            'date_of_birth': '2005-01-01',
        }
        form = AdmissionApplicationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_meta_fields(self):
        form = AdmissionApplicationForm()
        self.assertIn('first_name', form.fields)
        self.assertIn('session', form.fields)
        self.assertIn('gender', form.fields)


class CounselingCommentFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {'comment': 'This student shows great promise.', 'is_recommendation': True}
        form = CounselingCommentForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_comment(self):
        data = {'is_recommendation': False}
        form = CounselingCommentForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)


class AdmissionStatusFormTest(TestDataMixin, TestCase):
    def test_valid_email(self):
        form = AdmissionStatusForm(data={'email': 'test@example.com'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email(self):
        form = AdmissionStatusForm(data={'email': 'not-an-email'})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_empty_email(self):
        form = AdmissionStatusForm(data={'email': ''})
        self.assertFalse(form.is_valid())
