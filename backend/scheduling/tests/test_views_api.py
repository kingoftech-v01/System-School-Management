"""
API ViewSet tests for the scheduling app.

Tests cover CRUD operations, custom actions, and permission checks for:
- RoomViewSet
- TimeSlotViewSet
- ScheduleEntryViewSet
- ScheduleExceptionViewSet
- SubstitutionRequestViewSet
- ScheduleNotificationViewSet
- TimetableGenerationViewSet
"""

from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin
from scheduling.models import (
    Room, TimeSlot, ScheduleEntry, ScheduleException,
    SubstitutionRequest, ScheduleNotification, TimetableGeneration,
)


# ============================================================================
# Room ViewSet Tests
# ============================================================================

class RoomViewSetTests(TestDataMixin, TestCase):
    """Tests for RoomViewSet CRUD and custom actions."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student = self.create_student_user()
        self.school = self.create_school()
        self.room = self.create_room(tenant=self.school)

    # -- Authentication --

    def test_list_rooms_unauthenticated(self):
        url = reverse('api:scheduling:room-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_rooms_authenticated(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # -- CRUD --

    def test_create_room(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-list')
        data = {'name': 'New Room', 'code': 'NR001', 'capacity': 40, 'room_type': 'classroom'}
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'New Room')

    def test_retrieve_room(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-detail', kwargs={'pk': self.room.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], self.room.name)

    def test_update_room(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-detail', kwargs={'pk': self.room.pk})
        data = {'name': 'Updated Room', 'code': self.room.code, 'capacity': 50, 'room_type': 'lab'}
        resp = self.client.put(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.name, 'Updated Room')

    def test_partial_update_room(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-detail', kwargs={'pk': self.room.pk})
        resp = self.client.patch(url, {'capacity': 100}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.room.refresh_from_db()
        self.assertEqual(self.room.capacity, 100)

    def test_delete_room(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-detail', kwargs={'pk': self.room.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Room.objects.filter(pk=self.room.pk).exists())

    # -- Custom actions --

    def test_available_rooms_missing_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-available')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_available_rooms_with_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-available')
        resp = self.client.get(url, {
            'date': date.today().isoformat(),
            'start_time': '08:00',
            'end_time': '10:00',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)

    def test_room_utilization(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:room-utilization', kwargs={'pk': self.room.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('utilization_pct', resp.data)


# ============================================================================
# TimeSlot ViewSet Tests
# ============================================================================

class TimeSlotViewSetTests(TestDataMixin, TestCase):
    """Tests for TimeSlotViewSet CRUD and grid action."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.school = self.create_school()
        self.timeslot = self.create_timeslot(tenant=self.school)

    def test_list_timeslots_unauthenticated(self):
        url = reverse('api:scheduling:timeslot-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_timeslots(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timeslot-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_timeslot(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timeslot-list')
        data = {
            'name': 'Morning Slot',
            'start_time': '09:00',
            'end_time': '11:00',
            'day_of_week': 1,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_timeslot(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timeslot-detail', kwargs={'pk': self.timeslot.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_timeslot(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timeslot-detail', kwargs={'pk': self.timeslot.pk})
        data = {
            'name': 'Updated Slot',
            'start_time': '10:00',
            'end_time': '12:00',
            'day_of_week': 2,
        }
        resp = self.client.put(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_timeslot(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timeslot-detail', kwargs={'pk': self.timeslot.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_grid_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timeslot-grid')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ============================================================================
# ScheduleEntry ViewSet Tests
# ============================================================================

class ScheduleEntryViewSetTests(TestDataMixin, TestCase):
    """Tests for ScheduleEntryViewSet CRUD and custom actions."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.student = self.create_student_user()
        self.school = self.create_school()
        self.course = self.create_course()
        self.timeslot = self.create_timeslot(tenant=self.school)
        self.entry = self.create_schedule_entry(
            tenant=self.school,
            course=self.course,
            professor=self.professor,
            time_slot=self.timeslot,
        )

    def test_list_entries_unauthenticated(self):
        url = reverse('api:scheduling:scheduleentry-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_entries(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_entry(self):
        self.client.force_authenticate(user=self.admin)
        ts2 = self.create_timeslot(tenant=self.school, day_of_week=3, start_time='14:00', end_time='16:00')
        url = reverse('api:scheduling:scheduleentry-list')
        data = {
            'course': self.course.pk,
            'professor': self.professor.pk,
            'time_slot': ts2.pk,
            'effective_from': date.today().isoformat(),
            'effective_until': (date.today() + timedelta(days=90)).isoformat(),
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_entry(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-detail', kwargs={'pk': self.entry.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_entry(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-detail', kwargs={'pk': self.entry.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_calendar_feed_missing_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-calendar-feed')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calendar_feed_with_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-calendar-feed')
        resp = self.client.get(url, {
            'start': date.today().isoformat(),
            'end': (date.today() + timedelta(days=7)).isoformat(),
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp.data, list)

    def test_my_schedule(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:scheduling:scheduleentry-my-schedule')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('entries', resp.data)

    def test_conflicts_missing_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-conflicts')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conflicts_with_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-conflicts')
        resp = self.client.get(url, {
            'day_of_week': 0,
            'start_time': '08:00',
            'end_time': '10:00',
            'professor_id': self.professor.pk,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_move_missing_params(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleentry-move')
        resp = self.client.post(url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_move_entry(self):
        self.client.force_authenticate(user=self.admin)
        ts2 = self.create_timeslot(tenant=self.school, day_of_week=4, start_time='14:00', end_time='16:00')
        url = reverse('api:scheduling:scheduleentry-move')
        resp = self.client.post(url, {
            'entry_id': self.entry.pk,
            'time_slot_id': ts2.pk,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_bulk_create(self):
        self.client.force_authenticate(user=self.admin)
        ts2 = self.create_timeslot(tenant=self.school, day_of_week=2, start_time='08:00', end_time='10:00')
        url = reverse('api:scheduling:scheduleentry-bulk-create')
        data = {
            'entries': [{
                'course': self.course.pk,
                'professor': self.professor.pk,
                'time_slot': ts2.pk,
                'effective_from': date.today().isoformat(),
                'effective_until': (date.today() + timedelta(days=60)).isoformat(),
            }]
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['created'], 1)


# ============================================================================
# ScheduleException ViewSet Tests
# ============================================================================

class ScheduleExceptionViewSetTests(TestDataMixin, TestCase):
    """Tests for ScheduleExceptionViewSet CRUD and approval."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.course = self.create_course()
        self.timeslot = self.create_timeslot(tenant=self.school)
        self.entry = self.create_schedule_entry(
            tenant=self.school, course=self.course,
            professor=self.professor, time_slot=self.timeslot,
        )
        self.exception = ScheduleException.objects.create(
            tenant=self.school,
            schedule_entry=self.entry,
            exception_type='cancellation',
            date=date.today() + timedelta(days=5),
            reason='Sick leave',
            created_by=self.admin,
        )

    def test_list_exceptions_unauthenticated(self):
        url = reverse('api:scheduling:scheduleexception-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_exceptions(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleexception-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_exception(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleexception-list')
        data = {
            'schedule_entry': self.entry.pk,
            'exception_type': 'room_change',
            'date': (date.today() + timedelta(days=10)).isoformat(),
            'reason': 'Room maintenance',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_exception(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleexception-detail', kwargs={'pk': self.exception.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_exception(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleexception-detail', kwargs={'pk': self.exception.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_pending_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleexception-pending')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_approve_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:scheduleexception-approve', kwargs={'pk': self.exception.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.exception.refresh_from_db()
        self.assertTrue(self.exception.is_approved)


# ============================================================================
# SubstitutionRequest ViewSet Tests
# ============================================================================

class SubstitutionRequestViewSetTests(TestDataMixin, TestCase):
    """Tests for SubstitutionRequestViewSet CRUD and approval/rejection."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.school = self.create_school()
        self.course = self.create_course()
        self.timeslot = self.create_timeslot(tenant=self.school)
        self.entry = self.create_schedule_entry(
            tenant=self.school, course=self.course,
            professor=self.professor, time_slot=self.timeslot,
        )
        self.sub_request = SubstitutionRequest.objects.create(
            tenant=self.school,
            schedule_entry=self.entry,
            date=date.today() + timedelta(days=3),
            requesting_professor=self.professor,
            reason='Personal appointment',
        )

    def test_list_substitution_requests_unauthenticated(self):
        url = reverse('api:scheduling:substitutionrequest-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_substitution_requests(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:substitutionrequest-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_substitution_request(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:scheduling:substitutionrequest-list')
        data = {
            'schedule_entry': self.entry.pk,
            'date': (date.today() + timedelta(days=7)).isoformat(),
            'requesting_professor': self.professor.pk,
            'reason': 'Medical leave',
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_substitution_request(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:substitutionrequest-detail', kwargs={'pk': self.sub_request.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_approve_substitution_request(self):
        self.client.force_authenticate(user=self.admin)
        substitute = self.create_professor_user()
        url = reverse('api:scheduling:substitutionrequest-approve', kwargs={'pk': self.sub_request.pk})
        resp = self.client.post(url, {'substitute_id': substitute.pk}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.sub_request.refresh_from_db()
        self.assertEqual(self.sub_request.status, 'approved')

    def test_reject_substitution_request(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:substitutionrequest-reject', kwargs={'pk': self.sub_request.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.sub_request.refresh_from_db()
        self.assertEqual(self.sub_request.status, 'rejected')


# ============================================================================
# ScheduleNotification ViewSet Tests
# ============================================================================

class ScheduleNotificationViewSetTests(TestDataMixin, TestCase):
    """Tests for ScheduleNotificationViewSet (read-only) and mark read."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.user = self.create_student_user()
        self.school = self.create_school()
        self.notification = ScheduleNotification.objects.create(
            tenant=self.school,
            recipient=self.user,
            notification_type='cancellation',
            title='Class Cancelled',
            message='Your Monday class has been cancelled.',
        )

    def test_list_notifications_unauthenticated(self):
        url = reverse('api:scheduling:schedulenotification-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_notifications(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:scheduling:schedulenotification-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # DRF pagination wraps results in {'count', 'next', 'previous', 'results'}
        results = resp.data.get('results', resp.data) if isinstance(resp.data, dict) else resp.data
        self.assertEqual(len(results), 1)

    def test_retrieve_notification(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:scheduling:schedulenotification-detail', kwargs={'pk': self.notification.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_mark_read(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:scheduling:schedulenotification-mark-read', kwargs={'pk': self.notification.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_all_read(self):
        ScheduleNotification.objects.create(
            tenant=self.school,
            recipient=self.user,
            notification_type='reminder',
            title='Reminder',
            message='Reminder message.',
        )
        self.client.force_authenticate(user=self.user)
        url = reverse('api:scheduling:schedulenotification-mark-all-read')
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['marked_read'], 2)

    def test_unread_count(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('api:scheduling:schedulenotification-unread-count')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['count'], 1)

    def test_notifications_filtered_by_user(self):
        """Other users should not see another user's notifications."""
        other_user = self.create_student_user()
        self.client.force_authenticate(user=other_user)
        url = reverse('api:scheduling:schedulenotification-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # DRF pagination wraps results in {'count', 'next', 'previous', 'results'}
        results = resp.data.get('results', resp.data) if isinstance(resp.data, dict) else resp.data
        self.assertEqual(len(results), 0)


# ============================================================================
# TimetableGeneration ViewSet Tests
# ============================================================================

class TimetableGenerationViewSetTests(TestDataMixin, TestCase):
    """Tests for TimetableGenerationViewSet CRUD and run/rollback."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.school = self.create_school()
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.generation = TimetableGeneration.objects.create(
            tenant=self.school,
            session=self.session,
            semester=self.semester,
            created_by=self.admin,
        )

    def test_list_generations_unauthenticated(self):
        url = reverse('api:scheduling:timetablegeneration-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_list_generations(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timetablegeneration-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_generation(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timetablegeneration-list')
        data = {
            'session': self.session.pk,
            'semester': self.semester.pk,
        }
        resp = self.client.post(url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_retrieve_generation(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timetablegeneration-detail', kwargs={'pk': self.generation.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_delete_generation(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timetablegeneration-detail', kwargs={'pk': self.generation.pk})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_rollback_action(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('api:scheduling:timetablegeneration-rollback', kwargs={'pk': self.generation.pk})
        resp = self.client.post(url, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.status, 'rolled_back')
