"""
Model tests for the safeguarding app.

Tests cover:
- Incident model (creation, __str__, Meta, choices, relationships)
- IncidentAttachment model (creation, __str__)
- VisitorLog model (creation, __str__, is_currently_on_site, visit_duration)
- StudentCaseNote model (creation, __str__, Meta, confidentiality choices)
"""

from datetime import date, timedelta
from unittest.mock import MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from safeguarding.models import Incident, IncidentAttachment, VisitorLog, StudentCaseNote
from tests.helpers import TestDataMixin


class IncidentModelTests(TestDataMixin, TestCase):
    """Tests for the Incident model."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()

    def _create_incident(self, **kwargs):
        defaults = {
            'tenant': self.school,
            'incident_type': 'security',
            'title': 'Test Incident',
            'description': 'Test description',
            'severity': 'medium',
            'incident_date': date.today(),
            'reported_by': self.admin,
        }
        defaults.update(kwargs)
        return Incident.objects.create(**defaults)

    def test_create_incident(self):
        incident = self._create_incident()
        self.assertIsNotNone(incident.pk)
        self.assertEqual(incident.status, 'open')

    def test_str_includes_title_and_type(self):
        incident = self._create_incident(title='Fire Alarm')
        text = str(incident)
        self.assertIn('Fire Alarm', text)
        self.assertIn('Security', text)

    def test_default_status_is_open(self):
        incident = self._create_incident()
        self.assertEqual(incident.status, 'open')

    def test_incident_type_choices(self):
        types = [c[0] for c in Incident.INCIDENT_TYPE_CHOICES]
        self.assertIn('security', types)
        self.assertIn('medical', types)
        self.assertIn('theft', types)
        self.assertIn('safeguarding', types)

    def test_severity_choices(self):
        severities = [c[0] for c in Incident.SEVERITY_CHOICES]
        self.assertEqual(severities, ['low', 'medium', 'high', 'critical'])

    def test_status_choices(self):
        statuses = [c[0] for c in Incident.STATUS_CHOICES]
        self.assertIn('open', statuses)
        self.assertIn('closed', statuses)
        self.assertIn('investigating', statuses)

    def test_ordering(self):
        self._create_incident(
            title='Old', incident_date=date.today() - timedelta(days=10)
        )
        self._create_incident(
            title='New', incident_date=date.today()
        )
        incidents = list(Incident.objects.all())
        self.assertEqual(incidents[0].title, 'New')

    def test_m2m_students_involved(self):
        incident = self._create_incident()
        student_user = self.create_student_user()
        program = self.create_program()
        student_profile = self.create_student_profile(
            user=student_user, program=program,
        )
        incident.students_involved.add(student_profile)
        self.assertEqual(incident.students_involved.count(), 1)

    def test_m2m_staff_involved(self):
        incident = self._create_incident()
        staff = self.create_professor_user()
        incident.staff_involved.add(staff)
        self.assertEqual(incident.staff_involved.count(), 1)

    def test_follow_up_fields(self):
        incident = self._create_incident(
            follow_up_needed=True,
            follow_up_date=date.today() + timedelta(days=7),
        )
        self.assertTrue(incident.follow_up_needed)
        self.assertIsNotNone(incident.follow_up_date)

    def test_timestamps(self):
        incident = self._create_incident()
        self.assertIsNotNone(incident.created_at)
        self.assertIsNotNone(incident.updated_at)

    def test_updated_by_nullable(self):
        incident = self._create_incident()
        self.assertIsNone(incident.updated_by)


class IncidentAttachmentModelTests(TestDataMixin, TestCase):
    """Tests for the IncidentAttachment model."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='theft',
            title='Attachment Test',
            description='Desc',
            severity='low',
            incident_date=date.today(),
            reported_by=self.admin,
        )

    def test_str_includes_incident_title(self):
        attachment = IncidentAttachment.objects.create(
            incident=self.incident,
            file=SimpleUploadedFile('test.pdf', b'content'),
            description='Police report',
            uploaded_by=self.admin,
        )
        text = str(attachment)
        self.assertIn('Attachment Test', text)
        self.assertIn('Police report', text)

    def test_ordering(self):
        meta = IncidentAttachment._meta
        self.assertEqual(meta.ordering, ['-uploaded_at'])


class VisitorLogModelTests(TestDataMixin, TestCase):
    """Tests for the VisitorLog model."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()

    def _create_visitor(self, **kwargs):
        defaults = {
            'tenant': self.school,
            'visitor_name': 'John Doe',
            'visitor_type': 'parent',
            'purpose': 'Meeting',
            'time_in': timezone.now(),
            'logged_by': self.admin,
        }
        defaults.update(kwargs)
        return VisitorLog.objects.create(**defaults)

    def test_create_visitor(self):
        visitor = self._create_visitor()
        self.assertIsNotNone(visitor.pk)

    def test_str_includes_name_and_type(self):
        visitor = self._create_visitor(visitor_name='Jane Smith')
        text = str(visitor)
        self.assertIn('Jane Smith', text)
        self.assertIn('Parent', text)

    def test_is_currently_on_site_true_no_timeout(self):
        visitor = self._create_visitor()
        self.assertTrue(visitor.is_currently_on_site)

    def test_is_currently_on_site_false_with_timeout(self):
        visitor = self._create_visitor()
        visitor.time_out = timezone.now()
        visitor.save()
        self.assertFalse(visitor.is_currently_on_site)

    def test_visit_duration_none_when_still_on_site(self):
        visitor = self._create_visitor()
        self.assertIsNone(visitor.visit_duration)

    def test_visit_duration_calculated_when_checked_out(self):
        now = timezone.now()
        visitor = self._create_visitor(time_in=now)
        visitor.time_out = now + timedelta(hours=2)
        visitor.save()
        duration = visitor.visit_duration
        self.assertIsNotNone(duration)
        self.assertAlmostEqual(duration.total_seconds(), 7200, delta=5)

    def test_visitor_type_choices(self):
        types = [c[0] for c in VisitorLog.VISITOR_TYPE_CHOICES]
        self.assertIn('parent', types)
        self.assertIn('police', types)
        self.assertIn('social_worker', types)

    def test_ordering(self):
        meta = VisitorLog._meta
        self.assertEqual(meta.ordering, ['-time_in'])

    def test_m2m_students_involved(self):
        visitor = self._create_visitor()
        student_user = self.create_student_user()
        program = self.create_program()
        student_profile = self.create_student_profile(
            user=student_user, program=program,
        )
        visitor.students_involved.add(student_profile)
        self.assertEqual(visitor.students_involved.count(), 1)


class StudentCaseNoteModelTests(TestDataMixin, TestCase):
    """Tests for the StudentCaseNote model."""

    def setUp(self):
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )

    def _create_note(self, **kwargs):
        defaults = {
            'tenant': self.school,
            'student': self.student_profile,
            'category': 'academic',
            'confidentiality': 'standard',
            'title': 'Test Note',
            'content': 'Content',
            'created_by': self.admin,
        }
        defaults.update(kwargs)
        return StudentCaseNote.objects.create(**defaults)

    def test_create_note(self):
        note = self._create_note()
        self.assertIsNotNone(note.pk)

    def test_str_includes_student_and_title(self):
        note = self._create_note(title='Academic Concern')
        text = str(note)
        self.assertIn('Academic Concern', text)

    def test_default_confidentiality(self):
        note = self._create_note()
        self.assertEqual(note.confidentiality, 'standard')

    def test_category_choices(self):
        categories = [c[0] for c in StudentCaseNote.CATEGORY_CHOICES]
        self.assertIn('academic', categories)
        self.assertIn('behavioral', categories)
        self.assertIn('family', categories)
        self.assertIn('medical', categories)
        self.assertIn('legal', categories)
        self.assertIn('counseling', categories)

    def test_confidentiality_choices(self):
        levels = [c[0] for c in StudentCaseNote.CONFIDENTIALITY_CHOICES]
        self.assertEqual(levels, ['standard', 'restricted', 'highly_restricted'])

    def test_follow_up_fields(self):
        note = self._create_note(
            follow_up_date=date.today() + timedelta(days=7),
            follow_up_completed=False,
        )
        self.assertFalse(note.follow_up_completed)
        self.assertIsNotNone(note.follow_up_date)

    def test_related_incident_link(self):
        incident = Incident.objects.create(
            tenant=self.school,
            incident_type='behavioral',
            title='Linked Incident',
            description='Desc',
            severity='low',
            incident_date=date.today(),
            reported_by=self.admin,
        )
        note = self._create_note(related_incident=incident)
        self.assertEqual(note.related_incident, incident)

    def test_ordering(self):
        meta = StudentCaseNote._meta
        self.assertEqual(meta.ordering, ['-created_at'])

    def test_permissions_defined(self):
        perms = [p[0] for p in StudentCaseNote._meta.permissions]
        self.assertIn('view_restricted_notes', perms)
        self.assertIn('view_highly_restricted_notes', perms)

    def test_timestamps(self):
        note = self._create_note()
        self.assertIsNotNone(note.created_at)
        self.assertIsNotNone(note.updated_at)
