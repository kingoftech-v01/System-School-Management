"""Tests for enrollment app forms."""

from datetime import date, timedelta
from django.test import TestCase

from enrollment.forms import (
    RegistrationFormStep1,
    RegistrationFormStep2,
    RegistrationFormStep3,
    RegistrationFormStep4,
    DocumentUploadForm,
    RegistrationReviewForm,
)
from tests.helpers import TestDataMixin


class RegistrationFormStep1Test(TestCase):
    def test_valid_form(self):
        form = RegistrationFormStep1(data={
            'student_first_name': 'John',
            'student_last_name': 'Doe',
            'date_of_birth': date(2005, 1, 1),
            'gender': 'M',
            'nationality': 'French',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'street_address': '123 Test St',
            'city': 'Test City',
            'province': 'Test Province',
            'country': 'Test Country',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        form = RegistrationFormStep1(data={
            'date_of_birth': date(2005, 1, 1),
            'gender': 'M',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'street_address': '123 Test St',
            'city': 'Test City',
            'province': 'Test Province',
            'country': 'Test Country',
        })
        self.assertFalse(form.is_valid())

    def test_too_young(self):
        form = RegistrationFormStep1(data={
            'student_first_name': 'Young',
            'student_last_name': 'Kid',
            'date_of_birth': date.today() - timedelta(days=365),  # 1 year old
            'gender': 'M',
            'email': 'young@example.com',
            'phone': '+1234567890',
            'street_address': '123 Test St',
            'city': 'Test City',
            'province': 'Test Province',
            'country': 'Test Country',
        })
        self.assertFalse(form.is_valid())

    def test_too_old(self):
        form = RegistrationFormStep1(data={
            'student_first_name': 'Old',
            'student_last_name': 'Person',
            'date_of_birth': date(1900, 1, 1),
            'gender': 'F',
            'email': 'old@example.com',
            'phone': '+1234567890',
            'street_address': '123 Test St',
            'city': 'Test City',
            'province': 'Test Province',
            'country': 'Test Country',
        })
        self.assertFalse(form.is_valid())


class RegistrationFormStep2Test(TestCase):
    def test_valid_form(self):
        form = RegistrationFormStep2(data={
            'parent_first_name': 'Jane',
            'parent_last_name': 'Doe',
            'parent_email': 'jane@example.com',
            'parent_phone': '+0987654321',
            'parent_relationship': 'mother',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_parent_name(self):
        form = RegistrationFormStep2(data={
            'parent_email': 'jane@example.com',
            'parent_phone': '+0987654321',
        })
        self.assertFalse(form.is_valid())


class RegistrationFormStep3Test(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = RegistrationFormStep3(data={
            'enrollment_type': 'new',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        })
        self.assertTrue(form.is_valid(), form.errors)


class RegistrationFormStep4Test(TestCase):
    def test_valid_empty(self):
        form = RegistrationFormStep4(data={})
        self.assertTrue(form.is_valid())

    def test_with_data(self):
        form = RegistrationFormStep4(data={
            'special_needs': 'None',
            'medical_information': 'No allergies',
        })
        self.assertTrue(form.is_valid())


class RegistrationReviewFormTest(TestCase):
    def test_approve_valid(self):
        form = RegistrationReviewForm(data={
            'status': 'approved',
            'review_notes': 'All documents verified',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_reject_requires_reason(self):
        form = RegistrationReviewForm(data={
            'status': 'rejected',
            'review_notes': 'Missing documents',
        })
        self.assertFalse(form.is_valid())

    def test_reject_with_reason(self):
        form = RegistrationReviewForm(data={
            'status': 'rejected',
            'review_notes': 'Missing docs',
            'rejection_reason': 'Birth certificate not provided',
        })
        self.assertTrue(form.is_valid(), form.errors)
