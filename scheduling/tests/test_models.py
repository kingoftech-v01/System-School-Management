"""Tests for scheduling models."""

from datetime import date, time, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from core.models import School, Session, Semester
from course.models import Course, Program
from scheduling.models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)

User = get_user_model()


def _create_school(**kwargs):
    """Create school with conditional schema_name."""
    defaults = {
        'name': 'Test School', 'email': 'test@school.local', 'slug': 'test',
        'subscription_start': date(2025, 1, 1),
        'subscription_end': date(2025, 12, 31),
    }
    defaults.update(kwargs)
    if hasattr(School, 'schema_name'):
        defaults.setdefault('schema_name', 'test')
    return School.objects.create(**defaults)


class RoomModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()

    def test_create_room(self):
        room = Room.objects.create(
            tenant=self.school, name='Room 101', code='R101',
            building='Main', floor=1, capacity=30, room_type='classroom',
        )
        self.assertEqual(str(room), 'Room 101 (Main, Floor 1)')
        self.assertTrue(room.is_active)

    def test_room_without_building(self):
        room = Room.objects.create(
            tenant=self.school, name='Online Room', code='ONL1',
            room_type='online',
        )
        self.assertEqual(str(room), 'Online Room')

    def test_room_code_unique_per_tenant(self):
        Room.objects.create(
            tenant=self.school, name='Room 1', code='R1',
        )
        with self.assertRaises(IntegrityError):
            Room.objects.create(
                tenant=self.school, name='Room 2', code='R1',
            )

    def test_room_equipment_json(self):
        room = Room.objects.create(
            tenant=self.school, name='Lab', code='LAB1',
            room_type='lab',
            equipment=['projector', 'computers', 'whiteboard'],
        )
        room.refresh_from_db()
        self.assertEqual(len(room.equipment), 3)
        self.assertIn('projector', room.equipment)


class TimeSlotModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()

    def test_create_timeslot(self):
        slot = TimeSlot.objects.create(
            tenant=self.school, name='Period 1',
            start_time=time(8, 0), end_time=time(10, 0),
            day_of_week=0, slot_type='class',
        )
        self.assertEqual(str(slot), 'Monday 08:00-10:00')

    def test_duration_minutes(self):
        slot = TimeSlot.objects.create(
            tenant=self.school, name='Period 1',
            start_time=time(8, 0), end_time=time(10, 0),
            day_of_week=0,
        )
        self.assertEqual(slot.duration_minutes, 120)

    def test_unique_day_start_per_tenant(self):
        TimeSlot.objects.create(
            tenant=self.school, name='Slot A',
            start_time=time(8, 0), end_time=time(10, 0),
            day_of_week=0,
        )
        with self.assertRaises(IntegrityError):
            TimeSlot.objects.create(
                tenant=self.school, name='Slot B',
                start_time=time(8, 0), end_time=time(9, 0),
                day_of_week=0,
            )


class ScheduleEntryModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()
        self.professor = User.objects.create_user(
            username='prof1', password='pass', role='professor',
            email='prof@test.com',
        )
        self.professor.tenant = self.school
        self.professor.save()
        self.program = Program.objects.create(title='Computer Science')
        self.course = Course.objects.create(
            title='Mathematics', code='MATH101', program=self.program,
        )
        self.slot = TimeSlot.objects.create(
            tenant=self.school, name='Mon 8-10',
            start_time=time(8, 0), end_time=time(10, 0),
            day_of_week=0,
        )
        self.room = Room.objects.create(
            tenant=self.school, name='Room 1', code='R1',
        )
        self.session = Session.objects.create(session='2024/2025')
        self.semester = Semester.objects.create(semester='First')

    def _create_entry(self, **kwargs):
        defaults = dict(
            tenant=self.school, course=self.course,
            professor=self.professor, room=self.room,
            time_slot=self.slot, session=self.session,
            semester=self.semester,
            effective_from=date(2025, 1, 6),
            effective_until=date(2025, 6, 30),
            recurrence='weekly', status='active',
        )
        defaults.update(kwargs)
        return ScheduleEntry.objects.create(**defaults)

    def test_create_entry(self):
        entry = self._create_entry()
        self.assertIn('Mathematics', str(entry))
        self.assertEqual(entry.status, 'active')

    def test_is_active_on_correct_day(self):
        entry = self._create_entry()
        # Monday within range
        monday = date(2025, 1, 6)
        self.assertTrue(entry.is_active_on(monday))

    def test_is_not_active_on_wrong_day(self):
        entry = self._create_entry()
        # Tuesday
        tuesday = date(2025, 1, 7)
        self.assertFalse(entry.is_active_on(tuesday))

    def test_is_not_active_outside_range(self):
        entry = self._create_entry()
        # Before effective_from
        before = date(2024, 12, 30)
        self.assertFalse(entry.is_active_on(before))
        # After effective_until
        after = date(2025, 7, 7)
        self.assertFalse(entry.is_active_on(after))

    def test_is_not_active_when_cancelled(self):
        entry = self._create_entry(status='cancelled')
        monday = date(2025, 1, 6)
        self.assertFalse(entry.is_active_on(monday))

    def test_biweekly_recurrence(self):
        entry = self._create_entry(recurrence='biweekly_odd')
        # Check two consecutive Mondays - one should be active, one not
        mon1 = date(2025, 1, 6)  # ISO week 2 (even)
        mon2 = date(2025, 1, 13)  # ISO week 3 (odd)
        self.assertFalse(entry.is_active_on(mon1))
        self.assertTrue(entry.is_active_on(mon2))


class ScheduleExceptionModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()
        self.professor = User.objects.create_user(
            username='prof2', password='pass', role='professor',
            email='prof2@test.com',
        )
        self.professor.tenant = self.school
        self.professor.save()
        self.program = Program.objects.create(title='Science')
        self.course = Course.objects.create(
            title='Physics', code='PHYS101', program=self.program,
        )
        self.slot = TimeSlot.objects.create(
            tenant=self.school, name='Tue 8-10',
            start_time=time(8, 0), end_time=time(10, 0),
            day_of_week=1,
        )
        self.session = Session.objects.create(session='2024/2025')
        self.semester = Semester.objects.create(semester='First')
        self.entry = ScheduleEntry.objects.create(
            tenant=self.school, course=self.course,
            professor=self.professor, time_slot=self.slot,
            session=self.session, semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )

    def test_create_cancellation(self):
        exc = ScheduleException.objects.create(
            tenant=self.school, schedule_entry=self.entry,
            exception_type='cancellation', date=date(2025, 2, 4),
            reason='Professor sick',
        )
        self.assertIn('Cancellation', str(exc))

    def test_unique_entry_date_type(self):
        ScheduleException.objects.create(
            tenant=self.school, schedule_entry=self.entry,
            exception_type='cancellation', date=date(2025, 2, 4),
        )
        with self.assertRaises(IntegrityError):
            ScheduleException.objects.create(
                tenant=self.school, schedule_entry=self.entry,
                exception_type='cancellation', date=date(2025, 2, 4),
            )


class SubstitutionRequestModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()
        self.professor = User.objects.create_user(
            username='prof3', password='pass', role='professor',
            email='prof3@test.com',
        )
        self.professor.tenant = self.school
        self.professor.save()
        self.program = Program.objects.create(title='Chemistry Prog')
        self.course = Course.objects.create(
            title='Chemistry', code='CHEM101', program=self.program,
        )
        self.slot = TimeSlot.objects.create(
            tenant=self.school, name='Wed 10-12',
            start_time=time(10, 0), end_time=time(12, 0),
            day_of_week=2,
        )
        self.session = Session.objects.create(session='2024/2025')
        self.semester = Semester.objects.create(semester='First')
        self.entry = ScheduleEntry.objects.create(
            tenant=self.school, course=self.course,
            professor=self.professor, time_slot=self.slot,
            session=self.session, semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )

    def test_create_request(self):
        sub = SubstitutionRequest.objects.create(
            tenant=self.school, schedule_entry=self.entry,
            date=date(2025, 2, 5),
            requesting_professor=self.professor,
            reason='Conference attendance',
        )
        self.assertEqual(sub.status, 'pending')
        self.assertIn('Chemistry', str(sub))


class ScheduleNotificationModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()
        self.user = User.objects.create_user(
            username='student1', password='pass', role='student',
            email='student@test.com',
        )
        self.user.tenant = self.school
        self.user.save()

    def test_create_notification(self):
        notif = ScheduleNotification.objects.create(
            tenant=self.school, recipient=self.user,
            notification_type='cancellation',
            title='Class Cancelled',
            message='Mathematics class on Monday is cancelled.',
        )
        self.assertFalse(notif.is_read)
        self.assertIn('Class Cancelled', str(notif))


class TimetableGenerationModelTest(TestCase):
    def setUp(self):
        self.school = _create_school()
        self.session = Session.objects.create(session='2024/2025')
        self.semester = Semester.objects.create(semester='First')
        self.user = User.objects.create_user(
            username='admin1', password='pass', role='admin',
            email='admin@test.com',
        )

    def test_create_generation(self):
        gen = TimetableGeneration.objects.create(
            tenant=self.school, session=self.session,
            semester=self.semester, created_by=self.user,
            config={'max_classes_per_day': 4},
        )
        self.assertEqual(gen.status, 'pending')
        self.assertEqual(gen.entries_created, 0)
        self.assertIn('Generation #', str(gen))
