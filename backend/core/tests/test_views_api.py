"""
API view tests for the core app.

Tests cover:
- SessionViewSet CRUD + current / set_current actions
- SemesterViewSet CRUD + current / set_current actions
- NewsAndEventsViewSet CRUD + news / events actions
- ActivityLogViewSet list / retrieve (read-only)
- Unauthenticated access
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import NewsAndEvents
from tests.helpers import TestDataMixin


class SessionViewSetTests(TestDataMixin, TestCase):
    """Tests for SessionViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.session = self.create_session()

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_sessions_unauthenticated(self):
        url = reverse('api:core:session-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_sessions(self):
        self._auth(self.admin)
        url = reverse('api:core:session-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_session(self):
        self._auth(self.admin)
        url = reverse('api:core:session-detail', kwargs={'pk': self.session.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_session(self):
        self._auth(self.admin)
        url = reverse('api:core:session-list')
        data = {'session': '2025/2026', 'is_current_session': False}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_current_session_action(self):
        """GET /sessions/current/ returns the current session."""
        self._auth(self.admin)
        url = reverse('api:core:session-current')
        response = self.client.get(url)
        # 200 if a current session exists, 404 otherwise
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_set_current_session_action(self):
        """POST /sessions/{pk}/set_current/ marks session as current."""
        from core.models import Session
        new_session = Session.objects.create(session='2026/2027', is_current_session=False)
        self._auth(self.admin)
        url = reverse('api:core:session-set-current', kwargs={'pk': new_session.pk})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_session.refresh_from_db()
        self.assertTrue(new_session.is_current_session)


class SemesterViewSetTests(TestDataMixin, TestCase):
    """Tests for SemesterViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_semesters(self):
        self._auth(self.admin)
        url = reverse('api:core:semester-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_semester(self):
        self._auth(self.admin)
        url = reverse('api:core:semester-detail', kwargs={'pk': self.semester.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_current_semester_action(self):
        self._auth(self.admin)
        url = reverse('api:core:semester-current')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_set_current_semester_action(self):
        from core.models import Semester
        new_sem = Semester.objects.create(
            semester='Second', is_current_semester=False, session=self.session
        )
        self._auth(self.admin)
        url = reverse('api:core:semester-set-current', kwargs={'pk': new_sem.pk})
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_sem.refresh_from_db()
        self.assertTrue(new_sem.is_current_semester)


class NewsAndEventsViewSetTests(TestDataMixin, TestCase):
    """Tests for NewsAndEventsViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.news = NewsAndEvents.objects.create(
            title='Test News', summary='News summary', posted_as='News'
        )
        self.event = NewsAndEvents.objects.create(
            title='Test Event Post', summary='Event summary', posted_as='Event'
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_news_events_unauthenticated(self):
        url = reverse('api:core:news-event-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_news_events(self):
        self._auth(self.admin)
        url = reverse('api:core:news-event-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_news(self):
        self._auth(self.admin)
        url = reverse('api:core:news-event-list')
        data = {'title': 'New News', 'summary': 'Summary', 'posted_as': 'News'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_news_action(self):
        """GET /news-events/news/ returns only news posts."""
        self._auth(self.admin)
        url = reverse('api:core:news-event-news')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_events_action(self):
        """GET /news-events/events/ returns only event posts."""
        self._auth(self.admin)
        url = reverse('api:core:news-event-events')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_news_events(self):
        self._auth(self.admin)
        url = reverse('api:core:news-event-list')
        response = self.client.get(url, {'search': 'Test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ActivityLogViewSetTests(TestDataMixin, TestCase):
    """Tests for ActivityLogViewSet (read-only)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        from core.models import ActivityLog
        self.log = ActivityLog.objects.create(message='Test log entry')

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_activity_logs(self):
        self._auth(self.admin)
        url = reverse('api:core:activity-log-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_activity_log(self):
        self._auth(self.admin)
        url = reverse('api:core:activity-log-detail', kwargs={'pk': self.log.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_activity_log_is_read_only(self):
        """POST to activity logs should fail (read-only viewset)."""
        self._auth(self.admin)
        url = reverse('api:core:activity-log-list')
        response = self.client.post(url, {'message': 'new entry'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
