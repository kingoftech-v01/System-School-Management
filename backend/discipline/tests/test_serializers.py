"""Tests for discipline app serializers."""

from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from tests.helpers import TestDataMixin
from discipline.serializers import (
    UserMinimalSerializer,
    DisciplinaryActionSerializer,
    DisciplinaryActionListSerializer,
    DisciplinaryActionCreateSerializer,
)
from discipline.models import DisciplinaryAction


class UserMinimalSerializerTest(TestDataMixin, TestCase):
    def test_serializes_user(self):
        user = self.create_user(first_name='John', last_name='Doe')
        serializer = UserMinimalSerializer(user)
        self.assertEqual(serializer.data['username'], user.username)
        self.assertIn('full_name', serializer.data)

    def test_full_name_field(self):
        user = self.create_user(first_name='Jane', last_name='Smith')
        serializer = UserMinimalSerializer(user)
        self.assertEqual(serializer.data['full_name'], 'Jane Smith')

    def test_read_only_fields(self):
        user = self.create_user()
        serializer = UserMinimalSerializer(user)
        self.assertIn('id', serializer.data)
        self.assertIn('email', serializer.data)


class DisciplinaryActionSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.action = self.create_disciplinary_action()

    def test_serializes(self):
        serializer = DisciplinaryActionSerializer(self.action)
        self.assertIn('id', serializer.data)
        self.assertIn('student', serializer.data)
        self.assertIn('reported_by', serializer.data)
        self.assertIn('severity_display', serializer.data)

    def test_student_nested(self):
        serializer = DisciplinaryActionSerializer(self.action)
        student_data = serializer.data['student']
        self.assertIn('username', student_data)
        self.assertIn('full_name', student_data)

    def test_read_only_fields(self):
        serializer = DisciplinaryActionSerializer(self.action)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)

    def test_severity_display(self):
        serializer = DisciplinaryActionSerializer(self.action)
        self.assertEqual(serializer.data['severity_display'], 'Minor')


class DisciplinaryActionListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        action = self.create_disciplinary_action()
        serializer = DisciplinaryActionListSerializer(action)
        self.assertIn('student_name', serializer.data)
        self.assertIn('reported_by_name', serializer.data)
        self.assertIn('severity_display', serializer.data)
        self.assertIn('incident_type', serializer.data)

    def test_lightweight(self):
        action = self.create_disciplinary_action()
        serializer = DisciplinaryActionListSerializer(action)
        # Should not include full nested objects
        self.assertNotIn('description', serializer.data)
        self.assertNotIn('action_taken', serializer.data)


class DisciplinaryActionCreateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.student = self.create_student_user()

    def test_valid_data(self):
        data = {
            'student': self.student.pk,
            'incident_type': 'misconduct',
            'description': 'Disrupted class',
            'action_taken': 'Verbal warning',
            'severity': 'minor',
            'incident_date': date.today().isoformat(),
        }
        serializer = DisciplinaryActionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_future_incident_date_invalid(self):
        data = {
            'student': self.student.pk,
            'incident_type': 'misconduct',
            'description': 'Test',
            'action_taken': 'Test',
            'severity': 'minor',
            'incident_date': (date.today() + timedelta(days=5)).isoformat(),
        }
        serializer = DisciplinaryActionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('incident_date', serializer.errors)

    def test_resolved_without_resolution_date_invalid(self):
        data = {
            'student': self.student.pk,
            'incident_type': 'misconduct',
            'description': 'Test',
            'action_taken': 'Test',
            'severity': 'minor',
            'incident_date': date.today().isoformat(),
            'is_resolved': True,
        }
        serializer = DisciplinaryActionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('resolution_date', serializer.errors)

    def test_resolved_with_resolution_date_valid(self):
        data = {
            'student': self.student.pk,
            'incident_type': 'misconduct',
            'description': 'Test',
            'action_taken': 'Test',
            'severity': 'minor',
            'incident_date': date.today().isoformat(),
            'is_resolved': True,
            'resolution_date': date.today().isoformat(),
        }
        serializer = DisciplinaryActionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        serializer = DisciplinaryActionCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('student', serializer.errors)
        self.assertIn('incident_type', serializer.errors)
        self.assertIn('description', serializer.errors)
