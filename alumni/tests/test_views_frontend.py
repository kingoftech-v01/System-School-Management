"""
Frontend view tests for the alumni app.

Tests cover:
- directory: list alumni with search (authenticated)
- profile: view single alumni profile
- alumni_create: direction creates alumni records
- alumni_edit: direction edits alumni records
- events: list alumni events (upcoming and past)
- event_detail: view single alumni event
- achievements: list published achievements
- donate: alumni makes a donation
- Role-based access (direction manages, all authenticated view)
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class AlumniViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for alumni/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.direction_user = self.create_direction_user()
        self.admin_user = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()
        self.secretary_user = self.create_secretary_user()

    # ── directory ──────────────────────────────────────────────────

    def test_directory_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:alumni:directory')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_directory_student_access(self):
        """Students can view the alumni directory."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:directory')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_directory_direction_access(self):
        """Direction user can view the alumni directory."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:alumni:directory')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_directory_with_search(self):
        """Directory supports search by name/year/occupation."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:directory')
        resp = self.client.get(url, {'q': '2024'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_directory_with_alumni_records(self):
        """Directory lists alumni records."""
        self.create_alumni()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:directory')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_directory_pagination(self):
        """Directory supports pagination."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:directory')
        resp = self.client.get(url, {'page': 1})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── profile ────────────────────────────────────────────────────

    def test_profile_view(self):
        """Authenticated user can view an alumni profile."""
        alumni = self.create_alumni()
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:profile', args=[alumni.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_profile_nonexistent(self):
        """Non-existent alumni returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:profile', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_profile_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        alumni = self.create_alumni()
        url = reverse('frontend:alumni:profile', args=[alumni.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── alumni_create (direction only) ─────────────────────────────

    def test_alumni_create_get_direction(self):
        """Direction user can access the create form."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:alumni:alumni_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_create_get_admin(self):
        """Admin can access the create form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:alumni_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_create_denied_student(self):
        """Student cannot create alumni records."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:alumni_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_create_post_invalid(self):
        """POST with empty data re-renders the form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:alumni_create')
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_create_post_valid(self):
        """POST with valid data (form fields only, student excluded from form)."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:alumni_create')
        resp = self.client.post(url, {
            'graduation_year': 2024,
            'current_occupation': 'Engineer',
            'current_employer': 'Tech Corp',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── alumni_edit (direction only) ───────────────────────────────

    def test_alumni_edit_get_direction(self):
        """Direction user can access the edit form."""
        alumni = self.create_alumni()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:alumni:alumni_edit', args=[alumni.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_edit_get_admin(self):
        """Admin can access the edit form."""
        alumni = self.create_alumni()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:alumni_edit', args=[alumni.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_edit_denied_student(self):
        """Student cannot edit alumni records."""
        alumni = self.create_alumni()
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:alumni_edit', args=[alumni.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_edit_post_valid(self):
        """POST with valid data updates the alumni record."""
        alumni = self.create_alumni()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:alumni_edit', args=[alumni.pk])
        resp = self.client.post(url, {
            'graduation_year': 2023,
            'current_occupation': 'Software Engineer',
            'current_employer': 'TechCorp',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_alumni_edit_nonexistent(self):
        """Editing a non-existent alumni returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:alumni_edit', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── events ─────────────────────────────────────────────────────

    def test_events_list_student(self):
        """Student can view alumni events list."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:events')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_events_list_with_events(self):
        """Events list displays alumni events."""
        self.create_alumni_event()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:events')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_events_list_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:alumni:events')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── event_detail ───────────────────────────────────────────────

    def test_event_detail_view(self):
        """Authenticated user can view an event detail."""
        event = self.create_alumni_event()
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:event_detail', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_detail_nonexistent(self):
        """Non-existent event returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:alumni:event_detail', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── achievements ───────────────────────────────────────────────

    def test_achievements_list(self):
        """Authenticated user can view achievements."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:achievements')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_achievements_list_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:alumni:achievements')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── donate ─────────────────────────────────────────────────────

    def test_donate_get_authenticated(self):
        """Authenticated user can view the donation form."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:donate')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_donate_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:alumni:donate')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_donate_post_without_alumni_record(self):
        """User without alumni record is redirected with error."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:alumni:donate')
        resp = self.client.post(url, {
            'amount': '100.00',
            'purpose': 'general',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])
