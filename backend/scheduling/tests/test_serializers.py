"""Tests for scheduling app serializers."""

from datetime import date, timedelta, time
from django.test import TestCase

from tests.helpers import TestDataMixin
from scheduling.serializers import (
    RoomSerializer,
    RoomListSerializer,
    TimeSlotSerializer,
    ProfessorAvailabilitySerializer,
    ScheduleEntrySerializer,
    ScheduleEntryCreateSerializer,
    CalendarEventSerializer,
    ScheduleExceptionSerializer,
    SubstitutionRequestSerializer,
    ScheduleNotificationSerializer,
    TimetableGenerationSerializer,
)
from scheduling.models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)


class RoomSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        room = self.create_room()
        serializer = RoomSerializer(room)
        self.assertIn('name', serializer.data)
        self.assertIn('code', serializer.data)
        self.assertIn('capacity', serializer.data)
        self.assertIn('room_type', serializer.data)
        self.assertIn('is_active', serializer.data)

    def test_valid_data(self):
        tenant = self.create_school()
        data = {
            'name': 'New Room',
            'code': 'NR001',
            'capacity': 50,
            'room_type': 'classroom',
            'is_active': True,
        }
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class RoomListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        room = self.create_room()
        serializer = RoomListSerializer(room)
        self.assertIn('name', serializer.data)
        self.assertIn('display_name', serializer.data)
        self.assertIn('code', serializer.data)
        self.assertIn('capacity', serializer.data)

    def test_display_name(self):
        room = self.create_room()
        serializer = RoomListSerializer(room)
        self.assertEqual(serializer.data['display_name'], str(room))


class TimeSlotSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        slot = self.create_timeslot()
        serializer = TimeSlotSerializer(slot)
        self.assertIn('name', serializer.data)
        self.assertIn('start_time', serializer.data)
        self.assertIn('end_time', serializer.data)
        self.assertIn('day_of_week', serializer.data)
        self.assertIn('day_of_week_display', serializer.data)
        self.assertIn('duration_minutes', serializer.data)

    def test_duration_minutes(self):
        slot = self.create_timeslot()
        serializer = TimeSlotSerializer(slot)
        self.assertIsInstance(serializer.data['duration_minutes'], int)
        self.assertGreater(serializer.data['duration_minutes'], 0)

    def test_valid_data(self):
        data = {
            'name': 'Slot 1',
            'start_time': '08:00',
            'end_time': '10:00',
            'day_of_week': 0,
            'slot_type': 'class',
            'is_active': True,
        }
        serializer = TimeSlotSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class ProfessorAvailabilitySerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        professor = self.create_professor_user()
        tenant = self.create_school()
        slot = self.create_timeslot(tenant=tenant)
        avail = ProfessorAvailability.objects.create(
            professor=professor, time_slot=slot, preference='preferred',
        )
        serializer = ProfessorAvailabilitySerializer(avail)
        self.assertIn('professor', serializer.data)
        self.assertIn('time_slot', serializer.data)
        self.assertIn('preference', serializer.data)

    def test_valid_data(self):
        professor = self.create_professor_user()
        tenant = self.create_school()
        slot = self.create_timeslot(tenant=tenant)
        data = {
            'professor': professor.pk,
            'time_slot': slot.pk,
            'preference': 'unavailable',
        }
        serializer = ProfessorAvailabilitySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class ScheduleEntrySerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.entry = self.create_schedule_entry(tenant=self.tenant)

    def test_serializes(self):
        serializer = ScheduleEntrySerializer(self.entry)
        self.assertIn('course_title', serializer.data)
        self.assertIn('course_code', serializer.data)
        self.assertIn('professor_name', serializer.data)
        self.assertIn('time_slot_display', serializer.data)
        self.assertIn('status', serializer.data)
        self.assertIn('color', serializer.data)
        self.assertIn('is_locked', serializer.data)

    def test_read_only_id(self):
        serializer = ScheduleEntrySerializer(self.entry)
        self.assertIn('id', serializer.data)

    def test_course_title_value(self):
        serializer = ScheduleEntrySerializer(self.entry)
        self.assertEqual(serializer.data['course_title'], self.entry.course.title)


class ScheduleEntryCreateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.course = self.create_course()
        self.professor = self.create_professor_user()
        self.slot = self.create_timeslot(tenant=self.tenant)

    def test_valid_data(self):
        data = {
            'course': self.course.pk,
            'professor': self.professor.pk,
            'time_slot': self.slot.pk,
            'effective_from': date.today().isoformat(),
            'effective_until': (date.today() + timedelta(days=120)).isoformat(),
            'recurrence': 'weekly',
            'status': 'active',
        }
        serializer = ScheduleEntryCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        serializer = ScheduleEntryCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('course', serializer.errors)
        self.assertIn('professor', serializer.errors)
        self.assertIn('time_slot', serializer.errors)


class CalendarEventSerializerTest(TestDataMixin, TestCase):
    def test_valid_data(self):
        data = {
            'id': 'entry-1',
            'title': 'Math Class',
            'start': '2025-06-01T08:00:00Z',
            'end': '2025-06-01T10:00:00Z',
            'color': '#3788d8',
            'textColor': '#ffffff',
            'editable': False,
            'extendedProps': {'room': 'R101'},
        }
        serializer = CalendarEventSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        serializer = CalendarEventSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('id', serializer.errors)
        self.assertIn('title', serializer.errors)


class ScheduleExceptionSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.entry = self.create_schedule_entry(tenant=self.tenant)
        self.exception = ScheduleException.objects.create(
            tenant=self.tenant,
            schedule_entry=self.entry,
            exception_type='cancellation',
            date=date.today(),
            reason='Holiday',
        )

    def test_serializes(self):
        serializer = ScheduleExceptionSerializer(self.exception)
        self.assertIn('schedule_entry', serializer.data)
        self.assertIn('exception_type', serializer.data)
        self.assertIn('date', serializer.data)
        self.assertIn('reason', serializer.data)
        self.assertIn('schedule_entry_display', serializer.data)

    def test_read_only_notification_sent(self):
        serializer = ScheduleExceptionSerializer(self.exception)
        self.assertIn('notification_sent', serializer.data)


class SubstitutionRequestSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.entry = self.create_schedule_entry(tenant=self.tenant)
        self.professor = self.entry.professor
        self.request = SubstitutionRequest.objects.create(
            tenant=self.tenant,
            schedule_entry=self.entry,
            date=date.today(),
            requesting_professor=self.professor,
            reason='Conference attendance',
        )

    def test_serializes(self):
        serializer = SubstitutionRequestSerializer(self.request)
        self.assertIn('schedule_entry', serializer.data)
        self.assertIn('requesting_professor_name', serializer.data)
        self.assertIn('course_title', serializer.data)
        self.assertIn('reason', serializer.data)
        self.assertIn('status', serializer.data)

    def test_assigned_substitute_name_empty(self):
        serializer = SubstitutionRequestSerializer(self.request)
        self.assertEqual(serializer.data['assigned_substitute_name'], '')


class ScheduleNotificationSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        tenant = self.create_school()
        user = self.create_user()
        notif = ScheduleNotification.objects.create(
            tenant=tenant,
            recipient=user,
            notification_type='cancellation',
            title='Class Cancelled',
            message='Your class has been cancelled.',
        )
        serializer = ScheduleNotificationSerializer(notif)
        self.assertIn('notification_type', serializer.data)
        self.assertIn('title', serializer.data)
        self.assertIn('message', serializer.data)
        self.assertIn('is_read', serializer.data)

    def test_valid_data(self):
        data = {
            'notification_type': 'room_change',
            'title': 'Room Change',
            'message': 'Room changed to R201',
            'is_read': False,
        }
        serializer = ScheduleNotificationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class TimetableGenerationSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        tenant = self.create_school()
        session = self.create_session()
        semester = self.create_semester(session=session)
        user = self.create_admin_user()
        gen = TimetableGeneration.objects.create(
            tenant=tenant, session=session, semester=semester,
            created_by=user, status='pending',
        )
        serializer = TimetableGenerationSerializer(gen)
        self.assertIn('status', serializer.data)
        self.assertIn('status_display', serializer.data)
        self.assertIn('is_published', serializer.data)
        self.assertIn('entries_created', serializer.data)
        self.assertIn('conflicts_found', serializer.data)

    def test_valid_data(self):
        session = self.create_session()
        semester = self.create_semester(session=session)
        data = {
            'session': session.pk,
            'semester': semester.pk,
            'status': 'pending',
            'is_published': False,
        }
        serializer = TimetableGenerationSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
