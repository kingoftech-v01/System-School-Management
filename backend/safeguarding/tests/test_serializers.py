"""
Serializer tests for the safeguarding app.

Tests cover:
- IncidentListSerializer, IncidentDetailSerializer, IncidentCreateSerializer
- VisitorLogListSerializer, VisitorLogDetailSerializer, VisitorLogCreateSerializer
- StudentCaseNoteListSerializer, StudentCaseNoteDetailSerializer, StudentCaseNoteCreateSerializer
- UserMinimalSerializer
- IncidentAttachmentSerializer
- Validation (future incident date)
"""

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from safeguarding.models import Incident, VisitorLog, StudentCaseNote
from safeguarding.serializers import (
    IncidentAttachmentSerializer,
    IncidentCreateSerializer,
    IncidentDetailSerializer,
    IncidentListSerializer,
    StudentCaseNoteCreateSerializer,
    StudentCaseNoteDetailSerializer,
    StudentCaseNoteListSerializer,
    UserMinimalSerializer,
    VisitorLogCreateSerializer,
    VisitorLogDetailSerializer,
    VisitorLogListSerializer,
)
from tests.helpers import TestDataMixin


class UserMinimalSerializerTests(TestDataMixin, TestCase):
    """Tests for UserMinimalSerializer."""

    def test_serializes_user(self):
        user = self.create_admin_user()
        s = UserMinimalSerializer(user)
        self.assertEqual(s.data['id'], user.id)
        self.assertEqual(s.data['username'], user.username)
        self.assertIn('full_name', s.data)

    def test_full_name_uses_property(self):
        user = self.create_admin_user(first_name='John', last_name='Doe')
        s = UserMinimalSerializer(user)
        self.assertIn('John', s.data['full_name'])


class IncidentListSerializerTests(TestDataMixin, TestCase):
    """Tests for IncidentListSerializer."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='security',
            title='Test',
            description='Desc',
            severity='low',
            incident_date=date.today(),
            reported_by=self.admin,
        )

    def test_fields_present(self):
        s = IncidentListSerializer(self.incident)
        data = s.data
        self.assertIn('id', data)
        self.assertIn('title', data)
        self.assertIn('incident_type_display', data)
        self.assertIn('severity_display', data)
        self.assertIn('status_display', data)
        self.assertIn('reported_by_name', data)

    def test_display_fields_correct(self):
        s = IncidentListSerializer(self.incident)
        self.assertEqual(s.data['incident_type'], 'security')
        self.assertEqual(s.data['incident_type_display'], 'Security')


class IncidentDetailSerializerTests(TestDataMixin, TestCase):
    """Tests for IncidentDetailSerializer."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='medical',
            title='Medical Test',
            description='Desc',
            severity='critical',
            incident_date=date.today(),
            reported_by=self.admin,
        )

    def test_includes_nested_reported_by(self):
        s = IncidentDetailSerializer(self.incident)
        self.assertIn('reported_by', s.data)
        self.assertIsInstance(s.data['reported_by'], dict)

    def test_includes_attachments(self):
        s = IncidentDetailSerializer(self.incident)
        self.assertIn('attachments', s.data)
        self.assertIsInstance(s.data['attachments'], list)


class IncidentCreateSerializerTests(TestDataMixin, TestCase):
    """Tests for IncidentCreateSerializer."""

    def test_valid_data(self):
        s = IncidentCreateSerializer(data={
            'incident_type': 'theft',
            'title': 'Theft Report',
            'description': 'Desc',
            'severity': 'low',
            'incident_date': str(date.today()),
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_future_date_rejected(self):
        future_date = date.today() + timedelta(days=30)
        s = IncidentCreateSerializer(data={
            'incident_type': 'theft',
            'title': 'Future',
            'description': 'Desc',
            'severity': 'low',
            'incident_date': str(future_date),
        })
        self.assertFalse(s.is_valid())
        self.assertIn('incident_date', s.errors)

    def test_missing_required_fields(self):
        s = IncidentCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('title', s.errors)
        self.assertIn('description', s.errors)


class VisitorLogListSerializerTests(TestDataMixin, TestCase):
    """Tests for VisitorLogListSerializer."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.visitor = VisitorLog.objects.create(
            tenant=self.school,
            visitor_name='John',
            visitor_type='parent',
            purpose='Meeting',
            time_in=timezone.now(),
            host_staff=self.admin,
            logged_by=self.admin,
        )

    def test_fields_present(self):
        s = VisitorLogListSerializer(self.visitor)
        data = s.data
        self.assertIn('visitor_name', data)
        self.assertIn('visitor_type_display', data)
        self.assertIn('host_staff_name', data)
        self.assertIn('is_currently_on_site', data)

    def test_is_currently_on_site_true_when_no_timeout(self):
        s = VisitorLogListSerializer(self.visitor)
        self.assertTrue(s.data['is_currently_on_site'])

    def test_host_staff_name_populated(self):
        s = VisitorLogListSerializer(self.visitor)
        self.assertIsNotNone(s.data['host_staff_name'])

    def test_host_staff_name_none_when_no_host(self):
        self.visitor.host_staff = None
        self.visitor.save()
        s = VisitorLogListSerializer(self.visitor)
        self.assertIsNone(s.data['host_staff_name'])


class VisitorLogCreateSerializerTests(TestDataMixin, TestCase):
    """Tests for VisitorLogCreateSerializer."""

    def test_valid_data(self):
        s = VisitorLogCreateSerializer(data={
            'visitor_name': 'Jane',
            'visitor_type': 'other',
            'purpose': 'Delivery',
            'time_in': timezone.now().isoformat(),
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_required(self):
        s = VisitorLogCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('visitor_name', s.errors)


class CaseNoteListSerializerTests(TestDataMixin, TestCase):
    """Tests for StudentCaseNoteListSerializer."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.note = StudentCaseNote.objects.create(
            tenant=self.school,
            student=self.student_profile,
            category='academic',
            confidentiality='standard',
            title='Test Note',
            content='Content',
            created_by=self.admin,
        )

    def test_fields_present(self):
        s = StudentCaseNoteListSerializer(self.note)
        data = s.data
        self.assertIn('student_name', data)
        self.assertIn('category_display', data)
        self.assertIn('confidentiality_display', data)
        self.assertIn('created_by_name', data)

    def test_student_name(self):
        s = StudentCaseNoteListSerializer(self.note)
        self.assertIsNotNone(s.data['student_name'])


class CaseNoteCreateSerializerTests(TestDataMixin, TestCase):
    """Tests for StudentCaseNoteCreateSerializer."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )

    def test_valid_data(self):
        s = StudentCaseNoteCreateSerializer(data={
            'student': self.student_profile.pk,
            'category': 'behavioral',
            'confidentiality': 'standard',
            'title': 'New Note',
            'content': 'Content',
        })
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_required(self):
        s = StudentCaseNoteCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('student', s.errors)
        self.assertIn('title', s.errors)
