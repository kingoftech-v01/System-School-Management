"""
API view tests for the safeguarding app.

Tests cover:
- IncidentViewSet CRUD + close, upload_attachment, stats actions
- VisitorLogViewSet CRUD + checkout, on_site actions
- StudentCaseNoteViewSet CRUD + confidentiality filtering
- Authentication checks
- Filtering / searching / ordering
"""

from datetime import date

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from safeguarding.models import Incident, VisitorLog, StudentCaseNote
from tests.helpers import TestDataMixin


class IncidentViewSetTests(TestDataMixin, TestCase):
    """Tests for IncidentViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.student_user = self.create_student_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='security',
            title='Security Issue',
            description='Test desc',
            severity='medium',
            incident_date=date.today(),
            reported_by=self.admin,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_unauthenticated(self):
        url = reverse('api:safeguarding:incident-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_authenticated(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_incident(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-detail', kwargs={'pk': self.incident.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], 'Security Issue')

    def test_create_incident(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-list')
        data = {
            'incident_type': 'medical',
            'title': 'New Medical',
            'description': 'Medical emergency',
            'severity': 'high',
            'incident_date': str(date.today()),
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Incident.objects.filter(title='New Medical').exists())

    def test_create_sets_reported_by(self):
        self._auth(self.direction)
        url = reverse('api:safeguarding:incident-list')
        data = {
            'incident_type': 'theft',
            'title': 'Theft Report',
            'description': 'Desc',
            'severity': 'low',
            'incident_date': str(date.today()),
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        incident = Incident.objects.get(title='Theft Report')
        self.assertEqual(incident.reported_by, self.direction)

    def test_update_incident(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-detail', kwargs={'pk': self.incident.pk})
        data = {
            'incident_type': 'security',
            'title': 'Updated Title',
            'description': 'Updated desc',
            'severity': 'high',
            'incident_date': str(date.today()),
        }
        resp = self.client.put(url, data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.title, 'Updated Title')
        self.assertEqual(self.incident.updated_by, self.admin)

    def test_delete_incident(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-detail', kwargs={'pk': self.incident.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_close_action(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-close', kwargs={'pk': self.incident.pk})
        resp = self.client.post(url, {'resolution': 'All resolved'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.status, 'closed')
        self.assertEqual(self.incident.resolution, 'All resolved')

    def test_stats_action(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-stats')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total', resp.data)
        self.assertIn('open', resp.data)
        self.assertIn('by_type', resp.data)
        self.assertIn('by_severity', resp.data)

    def test_filter_by_incident_type(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-list')
        resp = self.client.get(url, {'incident_type': 'security'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filter_by_severity(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-list')
        resp = self.client.get(url, {'severity': 'medium'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_search(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:incident-list')
        resp = self.client.get(url, {'search': 'Security'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class VisitorLogViewSetTests(TestDataMixin, TestCase):
    """Tests for VisitorLogViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.visitor = VisitorLog.objects.create(
            tenant=self.school,
            visitor_name='Jane Doe',
            visitor_type='parent',
            purpose='Meeting with teacher',
            time_in=timezone.now(),
            logged_by=self.admin,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_unauthenticated(self):
        url = reverse('api:safeguarding:visitor-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_authenticated(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_visitor(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-detail', kwargs={'pk': self.visitor.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_visitor(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-list')
        data = {
            'visitor_name': 'New Visitor',
            'visitor_type': 'contractor',
            'purpose': 'Maintenance',
            'time_in': timezone.now().isoformat(),
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = VisitorLog.objects.get(visitor_name='New Visitor')
        self.assertEqual(created.logged_by, self.admin)

    def test_checkout_action(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-checkout', kwargs={'pk': self.visitor.pk})
        resp = self.client.post(url, {'notes': 'Left safely'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.visitor.refresh_from_db()
        self.assertIsNotNone(self.visitor.time_out)
        self.assertIn('Left safely', self.visitor.notes)

    def test_checkout_already_checked_out(self):
        self.visitor.time_out = timezone.now()
        self.visitor.save()
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-checkout', kwargs={'pk': self.visitor.pk})
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_on_site_action(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-on-site')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) >= 1)

    def test_on_site_excludes_checked_out(self):
        self.visitor.time_out = timezone.now()
        self.visitor.save()
        self._auth(self.admin)
        url = reverse('api:safeguarding:visitor-on-site')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 0)


class StudentCaseNoteViewSetTests(TestDataMixin, TestCase):
    """Tests for StudentCaseNoteViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
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
            title='Note 1',
            content='Content 1',
            created_by=self.admin,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_unauthenticated(self):
        url = reverse('api:safeguarding:case-note-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_authenticated(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:case-note-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_case_note(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:case-note-list')
        data = {
            'student': self.student_profile.pk,
            'category': 'behavioral',
            'confidentiality': 'standard',
            'title': 'New Note',
            'content': 'New content',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        created = StudentCaseNote.objects.get(title='New Note')
        self.assertEqual(created.created_by, self.admin)

    def test_retrieve_case_note(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:case-note-detail', kwargs={'pk': self.note.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_confidentiality_filtering_standard_user(self):
        """User without special perms only sees standard notes."""
        StudentCaseNote.objects.create(
            tenant=self.school,
            student=self.student_profile,
            category='family',
            confidentiality='restricted',
            title='Restricted Note',
            content='Secret',
            created_by=self.admin,
        )
        self._auth(self.direction)
        url = reverse('api:safeguarding:case-note-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        for note in resp.data.get('results', resp.data):
            self.assertEqual(note['confidentiality'], 'standard')

    def test_confidentiality_with_restricted_perm(self):
        """User with view_restricted_notes sees restricted but not highly_restricted."""
        StudentCaseNote.objects.create(
            tenant=self.school,
            student=self.student_profile,
            category='family',
            confidentiality='restricted',
            title='Restricted',
            content='Secret',
            created_by=self.admin,
        )
        StudentCaseNote.objects.create(
            tenant=self.school,
            student=self.student_profile,
            category='legal',
            confidentiality='highly_restricted',
            title='Top Secret',
            content='Very secret',
            created_by=self.admin,
        )
        perm = Permission.objects.get(codename='view_restricted_notes')
        self.direction.user_permissions.add(perm)
        self._auth(self.direction)
        url = reverse('api:safeguarding:case-note-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        notes = resp.data.get('results', resp.data)
        for note in notes:
            self.assertNotEqual(note['confidentiality'], 'highly_restricted')

    def test_filter_by_category(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:case-note-list')
        resp = self.client.get(url, {'category': 'academic'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filter_by_student(self):
        self._auth(self.admin)
        url = reverse('api:safeguarding:case-note-list')
        resp = self.client.get(url, {'student': self.student_profile.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
