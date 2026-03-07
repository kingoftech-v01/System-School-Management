"""Tests for enrollment app serializers."""

from django.test import TestCase

from enrollment.serializers import (
    RegistrationFormCreateSerializer,
    RegistrationReviewSerializer,
    EnrollmentStatusHistorySerializer,
)
from enrollment.models import EnrollmentStatusHistory
from tests.helpers import TestDataMixin


class RegistrationFormCreateSerializerTest(TestDataMixin, TestCase):
    def test_valid_data(self):
        data = {
            'student_name': 'New Student',
            'date_of_birth': '2005-01-01',
            'gender': 'M',
            'email': 'newstudent@test.com',
            'phone': '+1234567890',
            'address': '123 St',
            'parent_name': 'Parent',
            'parent_email': 'parent@test.com',
            'parent_phone': '+0987654321',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        }
        serializer = RegistrationFormCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_email_lowercased(self):
        data = {
            'student_name': 'Test',
            'date_of_birth': '2005-01-01',
            'gender': 'M',
            'email': 'UPPER@TEST.COM',
            'phone': '+1234567890',
            'address': '123 St',
            'parent_name': 'Parent',
            'parent_email': 'parent@test.com',
            'parent_phone': '+0987654321',
            'academic_year': '2024-2025',
            'level': 'Bachelor',
        }
        serializer = RegistrationFormCreateSerializer(data=data)
        serializer.is_valid()
        self.assertEqual(serializer.validated_data['email'], 'upper@test.com')


class RegistrationReviewSerializerTest(TestDataMixin, TestCase):
    def test_approve(self):
        serializer = RegistrationReviewSerializer(data={
            'status': 'approved',
            'review_notes': 'Good',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_reject_without_reason(self):
        serializer = RegistrationReviewSerializer(data={
            'status': 'rejected',
        })
        self.assertFalse(serializer.is_valid())

    def test_invalid_status(self):
        serializer = RegistrationReviewSerializer(data={
            'status': 'invalid_status',
        })
        self.assertFalse(serializer.is_valid())


class EnrollmentStatusHistorySerializerTest(TestDataMixin, TestCase):
    def test_serializes_history(self):
        reg = self.create_registration()
        history = EnrollmentStatusHistory.objects.create(
            registration=reg, old_status='pending', new_status='approved',
        )
        serializer = EnrollmentStatusHistorySerializer(history)
        data = serializer.data
        self.assertIn('old_status', data)
        self.assertIn('new_status', data)
