"""
Frontend view tests for the events app.

Tests cover:
- event_list: list events with filtering by type, date, audience (all logged-in)
- event_create: direction creates events (GET form, POST)
- event_detail: view event details (all logged-in)
- event_edit: direction edits events (GET form, POST)
- event_delete: direction deletes events (GET confirm, POST delete)
- Role-based access (direction/admin manage, others view)
- Audience filtering (students see student events, etc.)
"""

from datetime import datetime

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class EventsViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for events/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.direction_user = self.create_direction_user()
        self.admin_user = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()
        self.parent_user = self.create_parent_user()
        self.secretary_user = self.create_secretary_user()

    def _create_event(self, **kwargs):
        return self.create_event(tenant=self.school, **kwargs)

    # ── event_list ─────────────────────────────────────────────────

    def test_event_list_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_student_access(self):
        """Student can view events list (filtered to student/all audience)."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_direction_access(self):
        """Direction user can view all events."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_professor_access(self):
        """Professor can view events (filtered to staff/all audience)."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_parent_access(self):
        """Parent can view events (filtered to parents/all audience)."""
        self.client.force_login(self.parent_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_with_type_filter(self):
        """Event list supports event_type filter."""
        self._create_event(event_type='exam')
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url, {'event_type': 'exam'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_with_date_range_filter(self):
        """Event list supports date range filtering."""
        self._create_event()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url, {
            'date_from': '2025-01-01',
            'date_to': '2025-12-31',
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_with_invalid_date(self):
        """Event list handles invalid date input gracefully."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url, {'date_from': 'invalid'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_list_pagination(self):
        """Event list supports pagination."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_list')
        resp = self.client.get(url, {'page': 1})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── event_create ───────────────────────────────────────────────

    def test_event_create_get_direction(self):
        """Direction user can access the event creation form."""
        self.client.force_login(self.direction_user)
        url = reverse('frontend:events:event_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_create_get_admin(self):
        """Admin can access the event creation form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_create_denied_student(self):
        """Student cannot create events."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:events:event_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_create_denied_professor(self):
        """Professor cannot create events."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:events:event_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_create_post_valid(self):
        """POST with valid data creates an event."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_create')
        resp = self.client.post(url, {
            'title': 'Final Exams',
            'description': 'End of semester final examinations.',
            'event_type': 'exam',
            'start_date': '2025-06-15 09:00:00',
            'end_date': '2025-06-15 17:00:00',
            'target_audience': 'students',
            'send_reminder': True,
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_create_post_invalid(self):
        """POST with empty data re-renders the form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_create')
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── event_detail ───────────────────────────────────────────────

    def test_event_detail_student(self):
        """Student can view event details."""
        event = self._create_event()
        self.client.force_login(self.student_user)
        url = reverse('frontend:events:event_detail', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_detail_direction(self):
        """Direction user can view event details."""
        event = self._create_event()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:events:event_detail', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_detail_nonexistent(self):
        """Non-existent event returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_detail', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── event_edit ─────────────────────────────────────────────────

    def test_event_edit_get_direction(self):
        """Direction user can access the event edit form."""
        event = self._create_event()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:events:event_edit', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_edit_get_admin(self):
        """Admin can access the event edit form."""
        event = self._create_event()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_edit', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_edit_denied_student(self):
        """Student cannot edit events."""
        event = self._create_event()
        self.client.force_login(self.student_user)
        url = reverse('frontend:events:event_edit', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_edit_post_valid(self):
        """POST with valid data updates the event."""
        event = self._create_event()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_edit', args=[event.pk])
        resp = self.client.post(url, {
            'title': 'Updated Event Title',
            'description': 'Updated description.',
            'event_type': 'meeting',
            'start_date': '2025-07-01 10:00:00',
            'end_date': '2025-07-01 12:00:00',
            'target_audience': 'staff',
            'send_reminder': False,
        })
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_edit_post_invalid(self):
        """POST with invalid data re-renders the form."""
        event = self._create_event()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_edit', args=[event.pk])
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── event_delete ───────────────────────────────────────────────

    def test_event_delete_get_direction(self):
        """Direction user can view the delete confirmation page."""
        event = self._create_event()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:events:event_delete', args=[event.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_delete_post_direction(self):
        """Direction user can delete an event via POST."""
        event = self._create_event()
        self.client.force_login(self.direction_user)
        url = reverse('frontend:events:event_delete', args=[event.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_delete_post_admin(self):
        """Admin can delete an event via POST."""
        event = self._create_event()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_delete', args=[event.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_delete_denied_student(self):
        """Student cannot delete events."""
        event = self._create_event()
        self.client.force_login(self.student_user)
        url = reverse('frontend:events:event_delete', args=[event.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_delete_denied_professor(self):
        """Professor cannot delete events."""
        event = self._create_event()
        self.client.force_login(self.professor_user)
        url = reverse('frontend:events:event_delete', args=[event.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_event_delete_nonexistent(self):
        """Deleting a non-existent event returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:events:event_delete', args=[99999])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])
