"""
Frontend view tests for the safeguarding app.

Tests cover:
- Incident CRUD views (list, create, detail, edit)
- Visitor log views (list, sign-in, detail, sign-out)
- Case note views (list, create, detail)
- Role-based access control
- Filtering and pagination
"""

from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from safeguarding.models import Incident, VisitorLog, StudentCaseNote
from tests.helpers import TestDataMixin


class IncidentListTests(TestDataMixin, TestCase):
    """Tests for incident_list view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.prefet = self.create_prefet_user()
        self.student_user = self.create_student_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='security',
            title='Test Incident',
            description='Desc',
            severity='low',
            incident_date=date.today(),
            reported_by=self.admin,
        )
        self.url = reverse('frontend:safeguarding:incident_list')

    def test_admin_can_list(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('incidents', resp.context)

    def test_prefet_can_list(self):
        self.client.force_login(self.prefet)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_anonymous_redirects(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_filter_by_type(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?type=security')
        self.assertEqual(resp.status_code, 200)

    def test_filter_by_severity(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?severity=low')
        self.assertEqual(resp.status_code, 200)

    def test_filter_by_status(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?status=open')
        self.assertEqual(resp.status_code, 200)

    def test_search_filter(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?search=Test+Incident')
        self.assertEqual(resp.status_code, 200)

    def test_context_includes_counts(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertIn('total_count', resp.context)
        self.assertIn('open_count', resp.context)


class IncidentCreateTests(TestDataMixin, TestCase):
    """Tests for incident_create view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.url = reverse('frontend:safeguarding:incident_create')

    def test_get_shows_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_post_valid_creates_incident(self):
        self.client.force_login(self.admin)
        data = {
            'incident_type': 'security',
            'title': 'New Incident',
            'description': 'Security breach',
            'severity': 'high',
            'incident_date': str(date.today()),
            'status': 'open',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Incident.objects.filter(title='New Incident').exists())

    def test_post_invalid_shows_form(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 200)


class IncidentDetailTests(TestDataMixin, TestCase):
    """Tests for incident_detail view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='medical',
            title='Medical Emergency',
            description='Desc',
            severity='critical',
            incident_date=date.today(),
            reported_by=self.admin,
        )

    def test_admin_can_view_detail(self):
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:safeguarding:incident_detail',
            kwargs={'pk': self.incident.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_nonexistent_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:safeguarding:incident_detail',
            kwargs={'pk': 99999},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class IncidentEditTests(TestDataMixin, TestCase):
    """Tests for incident_edit view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.incident = Incident.objects.create(
            tenant=self.school,
            incident_type='theft',
            title='Theft Report',
            description='Desc',
            severity='medium',
            incident_date=date.today(),
            reported_by=self.admin,
        )
        self.url = reverse(
            'frontend:safeguarding:incident_edit',
            kwargs={'pk': self.incident.pk},
        )

    def test_get_shows_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_post_valid_updates(self):
        self.client.force_login(self.admin)
        data = {
            'incident_type': 'theft',
            'title': 'Updated Title',
            'description': 'Updated desc',
            'severity': 'high',
            'incident_date': str(date.today()),
            'status': 'investigating',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.incident.refresh_from_db()
        self.assertEqual(self.incident.title, 'Updated Title')


class VisitorListTests(TestDataMixin, TestCase):
    """Tests for visitor_list view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.student_user = self.create_student_user()
        self.prefet = self.create_prefet_user()
        self.visitor = VisitorLog.objects.create(
            tenant=self.school,
            visitor_name='John Doe',
            visitor_type='parent',
            purpose='Meeting',
            time_in=timezone.now(),
            logged_by=self.admin,
        )
        self.url = reverse('frontend:safeguarding:visitor_list')

    def test_admin_can_view(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('visitors', resp.context)

    def test_direction_can_view(self):
        self.client.force_login(self.direction)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_prefet_denied(self):
        """Prefet does not have direction_only access for visitors."""
        self.client.force_login(self.prefet)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_filter_by_type(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?type=parent')
        self.assertEqual(resp.status_code, 200)

    def test_filter_on_site(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?on_site=true')
        self.assertEqual(resp.status_code, 200)


class VisitorSignInTests(TestDataMixin, TestCase):
    """Tests for visitor_sign_in view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.url = reverse('frontend:safeguarding:visitor_sign_in')

    def test_get_shows_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_post_creates_visitor(self):
        self.client.force_login(self.admin)
        now = timezone.now()
        staff = self.create_direction_user()
        data = {
            'visitor_name': 'Jane Smith',
            'visitor_type': 'parent',
            'purpose': 'Parent meeting',
            'time_in': now.strftime('%Y-%m-%d %H:%M:%S'),
            'host_staff': staff.pk,
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            VisitorLog.objects.filter(visitor_name='Jane Smith').exists()
        )


class VisitorSignOutTests(TestDataMixin, TestCase):
    """Tests for visitor_sign_out view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.visitor = VisitorLog.objects.create(
            tenant=self.school,
            visitor_name='Test Visitor',
            visitor_type='other',
            purpose='Visit',
            time_in=timezone.now(),
            logged_by=self.admin,
        )
        self.url = reverse(
            'frontend:safeguarding:visitor_sign_out',
            kwargs={'pk': self.visitor.pk},
        )

    def test_post_signs_out_visitor(self):
        self.client.force_login(self.admin)
        resp = self.client.post(self.url, {'notes': 'Left at 5pm'})
        self.assertEqual(resp.status_code, 302)
        self.visitor.refresh_from_db()
        self.assertIsNotNone(self.visitor.time_out)

    def test_already_signed_out(self):
        self.visitor.time_out = timezone.now()
        self.visitor.save()
        self.client.force_login(self.admin)
        resp = self.client.post(self.url, {'notes': ''})
        self.assertEqual(resp.status_code, 302)


class CaseNoteListTests(TestDataMixin, TestCase):
    """Tests for case_note_list view."""

    def setUp(self):
        self.client = Client()
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
            title='Academic Note',
            content='Note content',
            created_by=self.admin,
        )
        self.url = reverse('frontend:safeguarding:case_note_list')

    def test_admin_can_view(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('notes', resp.context)

    def test_direction_can_view(self):
        self.client.force_login(self.direction)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_filter_by_category(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?category=academic')
        self.assertEqual(resp.status_code, 200)


class CaseNoteCreateTests(TestDataMixin, TestCase):
    """Tests for case_note_create view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.url = reverse('frontend:safeguarding:case_note_create')

    def test_get_shows_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_post_valid_creates_note(self):
        self.client.force_login(self.admin)
        data = {
            'student': self.student_profile.pk,
            'category': 'behavioral',
            'confidentiality': 'standard',
            'title': 'Behavioral Note',
            'content': 'Content here',
        }
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            StudentCaseNote.objects.filter(title='Behavioral Note').exists()
        )


class CaseNoteDetailTests(TestDataMixin, TestCase):
    """Tests for case_note_detail view with confidentiality checks."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )

    def _create_note(self, confidentiality='standard'):
        return StudentCaseNote.objects.create(
            tenant=self.school,
            student=self.student_profile,
            category='general',
            title='Test Note',
            content='Content',
            confidentiality=confidentiality,
            created_by=self.admin,
        )

    def test_admin_can_view_standard(self):
        note = self._create_note('standard')
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:safeguarding:case_note_detail',
            kwargs={'pk': note.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_direction_without_perm_restricted_redirects(self):
        note = self._create_note('restricted')
        self.client.force_login(self.direction)
        url = reverse(
            'frontend:safeguarding:case_note_detail',
            kwargs={'pk': note.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_direction_with_perm_can_view_restricted(self):
        note = self._create_note('restricted')
        perm = Permission.objects.get(codename='view_restricted_notes')
        self.direction.user_permissions.add(perm)
        self.client.force_login(self.direction)
        url = reverse(
            'frontend:safeguarding:case_note_detail',
            kwargs={'pk': note.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_highly_restricted_denied_without_perm(self):
        note = self._create_note('highly_restricted')
        self.client.force_login(self.direction)
        url = reverse(
            'frontend:safeguarding:case_note_detail',
            kwargs={'pk': note.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_superuser_can_view_highly_restricted(self):
        note = self._create_note('highly_restricted')
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:safeguarding:case_note_detail',
            kwargs={'pk': note.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
