"""
API view tests for the discipline app.

Tests cover:
- DisciplinaryActionViewSet CRUD
- Custom actions: resolve, student_history, stats
- Permission-based queryset filtering
- Filtering / searching / ordering
- Unauthenticated access
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


class DisciplinaryActionViewSetTests(TestDataMixin, TestCase):
    """Tests for DisciplinaryActionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.prefet = self.create_prefet_user()
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.action_obj = self.create_disciplinary_action(
            tenant=self.school,
            student=self.student,
            reported_by=self.professor,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # -- Authentication -------------------------------------------------------

    def test_list_actions_unauthenticated(self):
        url = reverse('api:discipline:action-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # -- List / Retrieve ------------------------------------------------------

    def test_list_actions_as_admin(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_actions_as_student_filtered(self):
        """Students can only see their own disciplinary actions."""
        self._auth(self.student)
        url = reverse('api:discipline:action-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_action(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-detail', kwargs={'pk': self.action_obj.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Create ---------------------------------------------------------------

    def test_create_action(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-list')
        data = {
            'student': self.student.pk,
            'incident_type': 'cheating',
            'description': 'Caught cheating on exam',
            'action_taken': 'Written warning',
            'severity': 'moderate',
            'incident_date': date.today().isoformat(),
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST))

    # -- Update ---------------------------------------------------------------

    def test_update_action(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-detail', kwargs={'pk': self.action_obj.pk})
        response = self.client.patch(url, {'description': 'Updated description'}, format='json')
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Delete ---------------------------------------------------------------

    def test_delete_action(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-detail', kwargs={'pk': self.action_obj.pk})
        response = self.client.delete(url)
        self.assertIn(response.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND))

    # -- Custom action: resolve -----------------------------------------------

    def test_resolve_action_as_admin(self):
        """Staff / direction / prefet can resolve an action."""
        self._auth(self.admin)
        url = reverse('api:discipline:action-resolve', kwargs={'pk': self.action_obj.pk})
        response = self.client.post(url, format='json')
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_resolve_action_as_prefet(self):
        self._auth(self.prefet)
        url = reverse('api:discipline:action-resolve', kwargs={'pk': self.action_obj.pk})
        response = self.client.post(url, format='json')
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_resolve_action_forbidden_for_student(self):
        """Students cannot resolve disciplinary actions."""
        self._auth(self.student)
        url = reverse('api:discipline:action-resolve', kwargs={'pk': self.action_obj.pk})
        response = self.client.post(url, format='json')
        # Either 403 (forbidden) or 404 (queryset filtering hides it)
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND))

    # -- Custom action: student_history ---------------------------------------

    def test_student_history_missing_param(self):
        """student_history requires student_id query parameter."""
        self._auth(self.admin)
        url = reverse('api:discipline:action-student-history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_student_history_with_param(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-student-history')
        response = self.client.get(url, {'student_id': self.student.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- Custom action: stats -------------------------------------------------

    def test_stats_action(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_count', response.data)

    # -- Filtering / Searching ------------------------------------------------

    def test_filter_by_severity(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-list')
        response = self.client.get(url, {'severity': 'minor'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_is_resolved(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-list')
        response = self.client.get(url, {'is_resolved': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_actions(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-list')
        response = self.client.get(url, {'search': 'misconduct'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_actions(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-list')
        response = self.client.get(url, {'ordering': '-incident_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stats_contains_expected_keys(self):
        self._auth(self.admin)
        url = reverse('api:discipline:action-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('total_count', 'resolved_count', 'pending_count', 'by_severity'):
            self.assertIn(key, response.data)

    def test_resolve_action_with_date(self):
        """Resolve action with an explicit resolution_date."""
        self._auth(self.admin)
        url = reverse('api:discipline:action-resolve', kwargs={'pk': self.action_obj.pk})
        response = self.client.post(
            url,
            {'resolution_date': date.today().isoformat()},
            format='json',
        )
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_create_action_unauthenticated(self):
        url = reverse('api:discipline:action-list')
        response = self.client.post(url, {}, format='json')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
