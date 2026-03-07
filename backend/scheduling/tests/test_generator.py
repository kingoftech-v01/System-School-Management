"""Tests for the timetable auto-generation engine."""

from datetime import date, time

from django.test import TestCase
from django.contrib.auth import get_user_model

from core.models import School, Session, Semester
from course.models import Course, Program
from scheduling.models import (
    Room, TimeSlot, ScheduleEntry, TimetableGeneration,
)
from scheduling.engine.validator import detect_conflicts
from scheduling.engine.types import SchedulingUnit, SlotAssignment, ConflictInfo

User = get_user_model()


def _create_school(**kwargs):
    defaults = {
        'name': 'Gen School', 'email': 'gen@school.local', 'slug': 'gen',
        'subscription_start': date(2025, 1, 1),
        'subscription_end': date(2025, 12, 31),
    }
    defaults.update(kwargs)
    if hasattr(School, 'schema_name'):
        defaults.setdefault('schema_name', 'gen')
    return School.objects.create(**defaults)


class SchedulingTypesTest(TestCase):
    """Test engine data types."""

    def test_scheduling_unit_creation(self):
        unit = SchedulingUnit(
            id='MATH101-1',
            course_id=1,
            course_title='Math',
            course_code='MATH101',
            professor_id=1,
            professor_name='Prof A',
            filiere_id=1,
            filiere_name='CS',
            year=1,
            hours_per_week=4,
            slots_needed=2,
            requires_lab=False,
            expected_students=30,
        )
        self.assertEqual(unit.course_title, 'Math')
        self.assertEqual(unit.hours_per_week, 4)
        self.assertEqual(unit.slots_needed, 2)

    def test_slot_assignment_creation(self):
        unit = SchedulingUnit(
            id='TEST-1', course_id=1, course_title='Test',
            course_code='T1', professor_id=1, professor_name='Prof',
            filiere_id=1, filiere_name='CS', year=1,
            hours_per_week=2, slots_needed=1, requires_lab=False,
            expected_students=30,
        )
        assignment = SlotAssignment(
            unit=unit,
            day_of_week=0,
            time_slot_id=1,
            room_id=1,
            start_time='08:00',
            end_time='10:00',
        )
        self.assertEqual(assignment.day_of_week, 0)

    def test_conflict_info_creation(self):
        conflict = ConflictInfo(
            conflict_type='professor_overlap',
            severity='hard',
            description='Prof A double-booked on Monday 8:00',
            entry_1_id=1,
            entry_2_id=2,
        )
        self.assertEqual(conflict.severity, 'hard')


class ConflictDetectionTest(TestCase):
    """Test the validator's conflict detection."""

    def setUp(self):
        self.school = _create_school()
        self.prof = User.objects.create_user(
            username='gen_prof', password='pass', role='professor',
            email='gen_prof@test.com',
        )
        self.prof.tenant = self.school
        self.prof.save()
        self.program = Program.objects.create(title='Engineering')
        self.course1 = Course.objects.create(title='Math', code='MATH1', program=self.program)
        self.course2 = Course.objects.create(title='Physics', code='PHYS1', program=self.program)
        self.room = Room.objects.create(
            tenant=self.school, name='Room 1', code='R1', capacity=30,
        )
        self.slot = TimeSlot.objects.create(
            tenant=self.school, name='Mon 8-10',
            start_time=time(8, 0), end_time=time(10, 0),
            day_of_week=0,
        )
        self.session = Session.objects.create(session='2024/2025')
        self.semester = Semester.objects.create(semester='First')

    def test_no_conflicts_single_entry(self):
        ScheduleEntry.objects.create(
            tenant=self.school, course=self.course1,
            professor=self.prof, room=self.room,
            time_slot=self.slot, session=self.session,
            semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )
        conflicts = detect_conflicts(self.school)
        self.assertEqual(len(conflicts), 0)

    def test_professor_double_booking_detected(self):
        """Same professor, same time slot = conflict."""
        ScheduleEntry.objects.create(
            tenant=self.school, course=self.course1,
            professor=self.prof, room=self.room,
            time_slot=self.slot, session=self.session,
            semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )
        room2 = Room.objects.create(
            tenant=self.school, name='Room 2', code='R2', capacity=30,
        )
        ScheduleEntry.objects.create(
            tenant=self.school, course=self.course2,
            professor=self.prof, room=room2,
            time_slot=self.slot, session=self.session,
            semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )
        conflicts = detect_conflicts(self.school)
        prof_conflicts = [c for c in conflicts if c.conflict_type == 'professor_overlap']
        self.assertGreater(len(prof_conflicts), 0)

    def test_room_double_booking_detected(self):
        """Same room, same time slot = conflict."""
        prof2 = User.objects.create_user(
            username='gen_prof2', password='pass', role='professor',
            email='gen_prof2@test.com',
        )
        prof2.tenant = self.school
        prof2.save()

        ScheduleEntry.objects.create(
            tenant=self.school, course=self.course1,
            professor=self.prof, room=self.room,
            time_slot=self.slot, session=self.session,
            semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )
        ScheduleEntry.objects.create(
            tenant=self.school, course=self.course2,
            professor=prof2, room=self.room,
            time_slot=self.slot, session=self.session,
            semester=self.semester,
            effective_from=date(2025, 1, 1),
            effective_until=date(2025, 6, 30),
        )
        conflicts = detect_conflicts(self.school)
        room_conflicts = [c for c in conflicts if c.conflict_type == 'room_overlap']
        self.assertGreater(len(room_conflicts), 0)
