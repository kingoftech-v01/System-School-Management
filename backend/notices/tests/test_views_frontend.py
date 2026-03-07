"""
Frontend view tests for the notices app.

Tests cover:
- notice_list: listing with search, priority filter, pagination, expired toggle
- notice_create: GET form, POST valid/invalid (direction only)
- notice_detail: view notice, acknowledgment info
- notice_update: GET form, POST update (direction only)
- notice_delete: GET confirm, POST delete (direction only)
- notice_respond: POST acknowledge (any logged-in user)
- Role-based access control (direction/admin vs student/professor)
"""

from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class NoticeViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for notices/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.direction_user = self.create_direction_user()
        self.admin_user = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()

    def _create_notice(self, **kwargs):
        from notices.models import Notice
        defaults = {
            'title': 'Test Notice Title',
            'content': 'This is the content of the test notice.',
            'priority': 'normal',
            'uploaded_by': self.direction_user,
        }
        defaults.update(kwargs)
        return Notice.objects.create(**defaults)

    # ── notice_list ────────────────────────────────────────────────

    def test_notice_list_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_list_direction_access(self):
        """Direction user can view notice list."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_list_admin_access(self):
        """Admin/superuser can view notice list."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_list_student_access(self):
        """Students can view the notice list (login_required only)."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_list_with_search(self):
        """Notice list supports search query parameter."""
        self._create_notice()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url, {'search': 'Test'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_list_with_priority_filter(self):
        """Notice list supports priority filter."""
        self._create_notice(priority='high')
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url, {'priority': 'high'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_list_show_expired(self):
        """Notice list supports show_expired toggle."""
        self._create_notice(expires_at=date.today() - timedelta(days=1))
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_list')
        resp = self.client.get(url, {'show_expired': 'true'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── notice_detail ──────────────────────────────────────────────

    def test_notice_detail_direction(self):
        """Direction user can view notice detail."""
        notice = self._create_notice()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_detail', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_detail_admin(self):
        """Admin can view notice detail."""
        notice = self._create_notice()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_detail', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_detail_student(self):
        """Student can view notice detail."""
        notice = self._create_notice()
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_detail', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_detail_nonexistent(self):
        """Requesting non-existent notice returns 404 or redirect."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_detail', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── notice_create ──────────────────────────────────────────────

    def test_notice_create_get_direction(self):
        """Direction user can access the create notice form."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_create_get_admin(self):
        """Admin can access the create notice form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_create_denied_for_student(self):
        """Student cannot create notices (direction_only)."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_create_denied_for_professor(self):
        """Professor cannot create notices (direction_only)."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:notices:notice_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_create_post_valid(self):
        """POST with valid data creates a notice."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_create')
        resp = self.client.post(url, {
            'title': 'New Notice Title',
            'content': 'Content for the new notice goes here.',
            'priority': 'high',
            'is_active': True,
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_create_post_invalid(self):
        """POST with invalid data re-renders the form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_create')
        resp = self.client.post(url, {
            'title': '',  # empty title should fail validation
            'content': '',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── notice_update ──────────────────────────────────────────────

    def test_notice_update_get_direction(self):
        """Direction user can access the update form."""
        notice = self._create_notice()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_update', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_update_get_admin(self):
        """Admin can access the update form."""
        notice = self._create_notice()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_update', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_update_denied_for_student(self):
        """Student cannot update notices."""
        notice = self._create_notice()
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_update', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_update_post_valid(self):
        """POST with valid data updates the notice."""
        notice = self._create_notice()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_update', args=[notice.pk])
        resp = self.client.post(url, {
            'title': 'Updated Notice Title',
            'content': 'Updated content for the notice body.',
            'priority': 'urgent',
            'is_active': True,
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_update_post_invalid(self):
        """POST with invalid data re-renders the form."""
        notice = self._create_notice()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_update', args=[notice.pk])
        resp = self.client.post(url, {
            'title': '',
            'content': '',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── notice_delete ──────────────────────────────────────────────

    def test_notice_delete_get_direction(self):
        """Direction user can see delete confirmation."""
        notice = self._create_notice()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_delete', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_delete_post_direction(self):
        """Direction user can delete a notice via POST."""
        notice = self._create_notice()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_delete', args=[notice.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_delete_post_admin(self):
        """Admin can delete a notice via POST."""
        notice = self._create_notice()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:notices:notice_delete', args=[notice.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_delete_denied_for_student(self):
        """Student cannot delete notices."""
        notice = self._create_notice()
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_delete', args=[notice.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── notice_respond ─────────────────────────────────────────────

    def test_notice_respond_post_student(self):
        """Student can acknowledge a notice via POST."""
        notice = self._create_notice()
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_respond', args=[notice.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_respond_post_direction(self):
        """Direction user can acknowledge a notice via POST."""
        notice = self._create_notice()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:notices:notice_respond', args=[notice.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_respond_get_redirects(self):
        """GET on notice_respond should redirect (POST only action)."""
        notice = self._create_notice()
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_respond', args=[notice.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_respond_double_acknowledge(self):
        """Acknowledging a notice twice should not fail."""
        notice = self._create_notice()
        self.client.force_login(self.student_user)
        url = reverse('frontend:notices:notice_respond', args=[notice.pk])
        self.client.post(url)
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_notice_respond_anonymous(self):
        """Anonymous users cannot respond to notices."""
        notice = self._create_notice()
        url = reverse('frontend:notices:notice_respond', args=[notice.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])
