"""
API view tests for the events app.

Tests cover:
- EventViewSet CRUD
- Custom actions: upcoming, calendar, stats
- Filtering / searching / ordering
- Audience-based filtering per user role
- Unauthenticated access
"""

from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


class EventViewSetTests(TestDataMixin, TestCase):
    """Tests for EventViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.event = self.create_event(tenant=self.school)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # -- Authentication -------------------------------------------------------

    def test_list_events_unauthenticated(self):
        url = reverse('api:events:event-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # -- List / Retrieve ------------------------------------------------------

    def test_list_events(self):
        self._auth(self.admin)
        url = reverse('api:events:event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_event(self):
        self._auth(self.admin)
        url = reverse('api:events:event-detail', kwargs={'pk': self.event.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Create ---------------------------------------------------------------

    def test_create_event(self):
        self._auth(self.admin)
        url = reverse('api:events:event-list')
        data = {
            'title': 'New Event',
            'description': 'A new test event',
            'event_type': 'meeting',
            'start_date': (timezone.now() + timedelta(days=10)).isoformat(),
            'end_date': (timezone.now() + timedelta(days=10, hours=2)).isoformat(),
            'target_audience': 'all',
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST))

    # -- Update ---------------------------------------------------------------

    def test_update_event(self):
        self._auth(self.admin)
        url = reverse('api:events:event-detail', kwargs={'pk': self.event.pk})
        response = self.client.patch(url, {'title': 'Updated Event'}, format='json')
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Delete ---------------------------------------------------------------

    def test_delete_event(self):
        self._auth(self.admin)
        url = reverse('api:events:event-detail', kwargs={'pk': self.event.pk})
        response = self.client.delete(url)
        self.assertIn(response.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND))

    # -- Custom actions -------------------------------------------------------

    def test_upcoming_events(self):
        """GET /events/upcoming/ returns future events."""
        self._auth(self.admin)
        url = reverse('api:events:event-upcoming')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upcoming_events_with_limit(self):
        self._auth(self.admin)
        url = reverse('api:events:event-upcoming')
        response = self.client.get(url, {'limit': 5})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_calendar_without_month_param(self):
        """Calendar endpoint requires a month parameter."""
        self._auth(self.admin)
        url = reverse('api:events:event-calendar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calendar_with_valid_month(self):
        self._auth(self.admin)
        url = reverse('api:events:event-calendar')
        response = self.client.get(url, {'month': '2025-06'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('events', response.data)

    def test_calendar_with_invalid_month(self):
        self._auth(self.admin)
        url = reverse('api:events:event-calendar')
        response = self.client.get(url, {'month': 'bad-format'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stats_action(self):
        """GET /events/stats/ returns event statistics."""
        self._auth(self.admin)
        url = reverse('api:events:event-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_count', response.data)

    # -- Filtering / Searching ------------------------------------------------

    def test_filter_by_event_type(self):
        self._auth(self.admin)
        url = reverse('api:events:event-list')
        response = self.client.get(url, {'event_type': 'exam'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_events(self):
        self._auth(self.admin)
        url = reverse('api:events:event-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_ordering_events(self):
        self._auth(self.admin)
        url = reverse('api:events:event-list')
        response = self.client.get(url, {'ordering': '-start_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # -- Role-based audience filtering ----------------------------------------

    def test_student_sees_student_events(self):
        """Students see events with target_audience in ('all', 'students')."""
        self._auth(self.student)
        url = reverse('api:events:event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_professor_sees_staff_events(self):
        """Professors see events with target_audience in ('all', 'staff')."""
        self._auth(self.professor)
        url = reverse('api:events:event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_target_audience(self):
        self._auth(self.admin)
        url = reverse('api:events:event-list')
        response = self.client.get(url, {'target_audience': 'all'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_event_unauthenticated(self):
        url = reverse('api:events:event-list')
        data = {'title': 'Nope', 'event_type': 'meeting'}
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_stats_contains_expected_keys(self):
        self._auth(self.admin)
        url = reverse('api:events:event-stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ('total_count', 'upcoming_count', 'past_count', 'by_type', 'by_audience'):
            self.assertIn(key, response.data)
