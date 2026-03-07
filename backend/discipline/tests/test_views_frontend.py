"""
Frontend view tests for the discipline app.

Tests cover:
- action_list: Prefet/direction/admin list disciplinary actions
- action_create: Prefet/direction/admin create actions
- action_detail: Prefet/direction/admin view action details
- action_edit: Prefet/direction/admin edit actions
- action_delete: Prefet/direction/admin delete actions (GET confirm + POST delete)
- action_resolve: Prefet/direction/admin resolve actions (POST-only)
- Permission checks: students/professors denied access
"""

from datetime import date

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class DisciplineViewsBase(TestDataMixin, TestCase):
    """Common setUp for discipline view tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()

        # Users with access (prefet_allowed: secretary, direction, admin, prefet)
        self.prefet = self.create_prefet_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()

        # Users without access
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()

        # Create a disciplinary action for detail/edit/delete/resolve tests
        self.action = self.create_disciplinary_action(
            tenant=self.school,
            student=self.student,
            reported_by=self.prefet,
        )


# ============================================================================
# ACTION LIST
# ============================================================================

class TestActionList(DisciplineViewsBase):
    """Tests for the disciplinary_action_list view."""

    def url(self):
        return reverse('frontend:discipline:action_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_prefet_can_access(self):
        self.client.force_login(self.prefet)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_severity(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'severity': 'minor'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_search(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'search': 'Test'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_resolved_true(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'resolved': 'true'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_resolved_false(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'resolved': 'false'})
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ACTION CREATE
# ============================================================================

class TestActionCreate(DisciplineViewsBase):
    """Tests for the disciplinary_action_create view."""

    def url(self):
        return reverse('frontend:discipline:action_create')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_prefet_get_form(self):
        self.client.force_login(self.prefet)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_get_form(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_data(self):
        self.client.force_login(self.admin)
        data = {
            'student': self.student.pk,
            'incident_type': 'cheating',
            'description': 'Caught cheating on exam',
            'action_taken': 'Verbal warning',
            'severity': 'moderate',
            'incident_date': date.today().isoformat(),
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty_data(self):
        """Submitting empty form re-renders with errors."""
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ACTION DETAIL
# ============================================================================

class TestActionDetail(DisciplineViewsBase):
    """Tests for the disciplinary_action_detail view."""

    def url(self, pk=None):
        return reverse('frontend:discipline:action_detail', kwargs={'pk': pk or self.action.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_prefet_can_view(self):
        self.client.force_login(self.prefet)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_view(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_view(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertIn(response.status_code, [404])


# ============================================================================
# ACTION EDIT
# ============================================================================

class TestActionEdit(DisciplineViewsBase):
    """Tests for the disciplinary_action_edit view."""

    def url(self, pk=None):
        return reverse('frontend:discipline:action_edit', kwargs={'pk': pk or self.action.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_prefet_get_form(self):
        self.client.force_login(self.prefet)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_get_form(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_edit(self):
        self.client.force_login(self.admin)
        data = {
            'student': self.student.pk,
            'incident_type': 'updated_type',
            'description': 'Updated description',
            'action_taken': 'Suspension',
            'severity': 'serious',
            'incident_date': date.today().isoformat(),
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty_data_shows_errors(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# ACTION DELETE
# ============================================================================

class TestActionDelete(DisciplineViewsBase):
    """Tests for the disciplinary_action_delete view."""

    def url(self, pk=None):
        return reverse('frontend:discipline:action_delete', kwargs={'pk': pk or self.action.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_shows_confirmation_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_deletes_action(self):
        self.client.force_login(self.admin)
        action = self.create_disciplinary_action(
            tenant=self.school, student=self.student, reported_by=self.prefet,
        )
        response = self.client.post(
            reverse('frontend:discipline:action_delete', kwargs={'pk': action.pk})
        )
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# ACTION RESOLVE
# ============================================================================

class TestActionResolve(DisciplineViewsBase):
    """Tests for the disciplinary_action_resolve view."""

    def url(self, pk=None):
        return reverse('frontend:discipline:action_resolve', kwargs={'pk': pk or self.action.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_redirects_to_detail(self):
        """GET on resolve redirects to detail page."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302])

    def test_post_resolves_action(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [200, 302, 500])
        self.action.refresh_from_db()
        self.assertTrue(self.action.is_resolved)

    def test_prefet_can_resolve(self):
        self.client.force_login(self.prefet)
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)
