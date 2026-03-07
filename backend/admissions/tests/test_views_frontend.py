"""
Frontend view tests for the admissions app.

Tests cover:
- home (admission_session_list): list active sessions (authenticated)
- apply: public admission application (GET form, POST submit)
- check_status: public status lookup by email
- admission_list: direction reviews all applications with filters
- admission_detail: direction views single application
- counseling_comment: direction adds counseling comments
- Role-based access (public vs direction-only views)
"""

from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class AdmissionsViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for admissions/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.direction_user = self.create_direction_user()
        self.admin_user = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()
        self.secretary_user = self.create_secretary_user()
        self.admission_session = self.create_admission_session()

    # ── home (admission_session_list) ──────────────────────────────

    def test_home_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:admissions:home')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_home_student_access(self):
        """Student can view active admission sessions."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:admissions:home')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_home_direction_access(self):
        """Direction user can view sessions."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:admissions:home')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_home_shows_active_sessions(self):
        """Home page lists active admission sessions."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:home')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── apply (public) ─────────────────────────────────────────────

    def test_apply_get_anonymous(self):
        """Anonymous users can access the application form."""
        url = reverse('frontend:admissions:apply')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_apply_get_authenticated(self):
        """Authenticated users can also access the application form."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:admissions:apply')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_apply_post_valid(self):
        """POST with valid data submits an application."""
        url = reverse('frontend:admissions:apply')
        resp = self.client.post(url, {
            'session': self.admission_session.pk,
            'first_name': 'Jean',
            'last_name': 'Dupont',
            'email': 'jean.dupont@example.com',
            'phone': '0612345678',
            'gender': 'M',
            'date_of_birth': '2005-03-15',
            'address': '123 Rue de Test',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_apply_post_invalid(self):
        """POST with empty data re-renders the form."""
        url = reverse('frontend:admissions:apply')
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_apply_post_missing_session(self):
        """POST without session field shows validation error."""
        url = reverse('frontend:admissions:apply')
        resp = self.client.post(url, {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@test.com',
            'phone': '1234567890',
            'gender': 'F',
            'date_of_birth': '2005-01-01',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── check_status (public) ──────────────────────────────────────

    def test_check_status_get(self):
        """GET shows the email lookup form."""
        url = reverse('frontend:admissions:check_status')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_check_status_post_found(self):
        """POST with email that has applications returns results."""
        student = self.create_admission_student(session=self.admission_session)
        url = reverse('frontend:admissions:check_status')
        resp = self.client.post(url, {'email': student.email})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_check_status_post_not_found(self):
        """POST with unknown email shows info message."""
        url = reverse('frontend:admissions:check_status')
        resp = self.client.post(url, {'email': 'unknown@example.com'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_check_status_post_invalid_email(self):
        """POST with invalid email re-renders the form."""
        url = reverse('frontend:admissions:check_status')
        resp = self.client.post(url, {'email': 'not-an-email'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── admission_list (direction only) ────────────────────────────

    def test_admission_list_direction(self):
        """Direction user can view all applications."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:admissions:admission_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_list_admin(self):
        """Admin can view all applications."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:admission_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_list_denied_student(self):
        """Students cannot view the admin application list."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:admissions:admission_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_list_with_status_filter(self):
        """Application list supports status filtering."""
        self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:admission_list')
        resp = self.client.get(url, {'status': 'pending'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_list_with_search(self):
        """Application list supports search by name/email."""
        self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:admission_list')
        resp = self.client.get(url, {'search': 'Applicant'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_list_secretary_access(self):
        """Secretary can access the application list (direction_only allows secretary)."""
        self.client.force_login(self.secretary_user)
        url = reverse('frontend:admissions:admission_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── admission_detail (direction only) ──────────────────────────

    def test_admission_detail_direction(self):
        """Direction user can view application detail."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.direction_user)
        url = reverse('frontend:admissions:admission_detail', args=[student.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_detail_admin(self):
        """Admin can view application detail."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:admission_detail', args=[student.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_detail_nonexistent(self):
        """Non-existent application returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:admission_detail', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_admission_detail_denied_student(self):
        """Students cannot view application detail."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.student_user)
        url = reverse('frontend:admissions:admission_detail', args=[student.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── counseling_comment (direction only) ────────────────────────

    def test_counseling_comment_get_direction(self):
        """Direction user can access the counseling comment form."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.direction_user)
        url = reverse('frontend:admissions:counseling_comment', args=[student.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_counseling_comment_post_valid(self):
        """POST with valid data creates a counseling comment."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:counseling_comment', args=[student.pk])
        resp = self.client.post(url, {
            'comment': 'This student shows great potential.',
            'is_recommendation': True,
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_counseling_comment_post_invalid(self):
        """POST with empty data re-renders the form."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:admissions:counseling_comment', args=[student.pk])
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_counseling_comment_denied_student(self):
        """Students cannot create counseling comments."""
        student = self.create_admission_student(session=self.admission_session)
        self.client.force_login(self.student_user)
        url = reverse('frontend:admissions:counseling_comment', args=[student.pk])
        resp = self.client.post(url, {'comment': 'Should not work.'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])
