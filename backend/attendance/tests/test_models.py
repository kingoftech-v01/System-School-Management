"""Tests for attendance app models."""

from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from attendance.models import (
    Group, Student, Subject, Satus,
    Attendance, AttendanceReport, DailyAttendanceStat,
)
from tests.helpers import TestDataMixin

User = get_user_model()

# Module-level counter for unique values
_att_counter = 0


def _ac():
    global _att_counter
    _att_counter += 1
    return _att_counter


class GroupModelTest(TestCase):
    def test_create(self):
        group = Group.objects.create(name='CS-101')
        self.assertIsNotNone(group.pk)

    def test_str(self):
        group = Group.objects.create(name='CS-101')
        self.assertEqual(str(group), 'CS-101')


class StudentModelTest(TestDataMixin, TestCase):
    def _create_att_student(self, **overrides):
        n = _ac()
        group = overrides.pop('group', None) or Group.objects.create(name=f'Group-{n}')
        defaults = {
            'first_name': f'First{n}',
            'last_name': f'Last{n}',
            'email': f'attstudent{n}@test.com',
            'group': group,
        }
        defaults.update(overrides)
        return Student.objects.create(**defaults)

    def test_create(self):
        student = self._create_att_student()
        self.assertIsNotNone(student.pk)

    def test_str(self):
        group = Group.objects.create(name='CS-101')
        student = self._create_att_student(
            first_name='John', last_name='Doe', group=group,
        )
        self.assertIn('John', str(student))
        self.assertIn('Doe', str(student))
        self.assertIn('CS-101', str(student))

    def test_get_attendances_empty(self):
        student = self._create_att_student()
        self.assertEqual(student.get_attendances.count(), 0)

    def test_get_absents_and_lates_empty(self):
        student = self._create_att_student()
        self.assertEqual(student.get_absents_and_lates.count(), 0)

    def test_get_subjects(self):
        group = Group.objects.create(name=f'SG-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name='Math', teacher=teacher, slug=f'math-{_ac()}',
        )
        subject.group.add(group)
        student = self._create_att_student(group=group)
        self.assertIn(subject, student.get_subjects)

    def test_get_attendance_percentage_no_records(self):
        student = self._create_att_student()
        self.assertEqual(student.get_attendance_percentage(), 0)

    def test_get_attendance_percentage_all_present(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        subject.group.add(group)
        student = self._create_att_student(group=group)

        attendance = Attendance.objects.create(subject=subject, date=date.today())
        AttendanceReport.objects.create(
            attendance=attendance, student=student, status=Satus.PRESENT,
        )
        self.assertEqual(student.get_attendance_percentage(), 100.0)

    def test_get_attendance_percentage_mixed(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        subject.group.add(group)
        student = self._create_att_student(group=group)

        a1 = Attendance.objects.create(subject=subject, date=date.today())
        a2 = Attendance.objects.create(subject=subject, date=date.today() - timedelta(days=1))
        AttendanceReport.objects.create(attendance=a1, student=student, status=Satus.PRESENT)
        AttendanceReport.objects.create(attendance=a2, student=student, status=Satus.ABSENT)
        self.assertEqual(student.get_attendance_percentage(), 50.0)

    def test_has_low_attendance_no_records(self):
        student = self._create_att_student()
        self.assertTrue(student.has_low_attendance())

    def test_has_low_attendance_above_threshold(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        subject.group.add(group)
        student = self._create_att_student(group=group)

        attendance = Attendance.objects.create(subject=subject, date=date.today())
        AttendanceReport.objects.create(
            attendance=attendance, student=student, status=Satus.PRESENT,
        )
        self.assertFalse(student.has_low_attendance())

    def test_late_counts_as_attended(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        subject.group.add(group)
        student = self._create_att_student(group=group)

        attendance = Attendance.objects.create(subject=subject, date=date.today())
        AttendanceReport.objects.create(
            attendance=attendance, student=student, status=Satus.LATE,
        )
        self.assertEqual(student.get_attendance_percentage(), 100.0)


class SubjectModelTest(TestDataMixin, TestCase):
    def test_create(self):
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name='Mathematics', teacher=teacher, slug=f'math-{_ac()}',
        )
        self.assertIsNotNone(subject.pk)

    def test_str(self):
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name='Mathematics', teacher=teacher, slug=f'math-{_ac()}',
        )
        self.assertEqual(str(subject), 'Mathematics')


class AttendanceModelTest(TestDataMixin, TestCase):
    def test_create(self):
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        att = Attendance.objects.create(subject=subject, date=date.today())
        self.assertIsNotNone(att.pk)

    def test_str(self):
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name='Math', teacher=teacher, slug=f'math-{_ac()}',
        )
        att = Attendance.objects.create(subject=subject, date=date.today())
        self.assertIn('Math', str(att))


class AttendanceReportModelTest(TestDataMixin, TestCase):
    def test_create(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        student = Student.objects.create(
            first_name='A', last_name='B',
            email=f'report{_ac()}@test.com', group=group,
        )
        att = Attendance.objects.create(subject=subject, date=date.today())
        report = AttendanceReport.objects.create(
            attendance=att, student=student, status=Satus.PRESENT,
        )
        self.assertIsNotNone(report.pk)

    def test_default_status_absent(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        student = Student.objects.create(
            first_name='A', last_name='B',
            email=f'report{_ac()}@test.com', group=group,
        )
        att = Attendance.objects.create(subject=subject, date=date.today())
        report = AttendanceReport.objects.create(
            attendance=att, student=student,
        )
        self.assertEqual(report.status, Satus.ABSENT)

    def test_unique_together(self):
        group = Group.objects.create(name=f'GP-{_ac()}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{_ac()}', teacher=teacher, slug=f'sub-{_ac()}',
        )
        student = Student.objects.create(
            first_name='A', last_name='B',
            email=f'report{_ac()}@test.com', group=group,
        )
        att = Attendance.objects.create(subject=subject, date=date.today())
        AttendanceReport.objects.create(
            attendance=att, student=student, status=Satus.PRESENT,
        )
        with self.assertRaises(Exception):
            AttendanceReport.objects.create(
                attendance=att, student=student, status=Satus.ABSENT,
            )


class DailyAttendanceStatModelTest(TestDataMixin, TestCase):
    def _setup_data(self):
        n = _ac()
        group = Group.objects.create(name=f'GP-{n}')
        teacher = self.create_professor_user()
        subject = Subject.objects.create(
            name=f'Sub-{n}', teacher=teacher, slug=f'sub-{n}',
        )
        subject.group.add(group)

        s1 = Student.objects.create(
            first_name='S1', last_name=f'L{n}a',
            email=f'stat{n}a@test.com', group=group,
        )
        s2 = Student.objects.create(
            first_name='S2', last_name=f'L{n}b',
            email=f'stat{n}b@test.com', group=group,
        )

        att = Attendance.objects.create(subject=subject, date=date.today())
        AttendanceReport.objects.create(attendance=att, student=s1, status=Satus.PRESENT)
        AttendanceReport.objects.create(attendance=att, student=s2, status=Satus.ABSENT)

        return subject, group

    def test_create(self):
        subject, group = self._setup_data()
        stat = DailyAttendanceStat.objects.create(
            subject=subject, group=group, date=date.today(),
        )
        self.assertIsNotNone(stat.pk)

    def test_calculate_stats(self):
        subject, group = self._setup_data()
        stat = DailyAttendanceStat.objects.create(
            subject=subject, group=group, date=date.today(),
        )
        stat.calculate_stats()
        stat.refresh_from_db()
        self.assertEqual(stat.total_students, 2)
        self.assertEqual(stat.present_count, 1)
        self.assertEqual(stat.absent_count, 1)
        self.assertEqual(stat.attendance_percentage, 50.0)

    def test_generate_for_date(self):
        subject, group = self._setup_data()
        DailyAttendanceStat.generate_for_date(date=date.today())
        stats = DailyAttendanceStat.objects.filter(
            subject=subject, group=group, date=date.today(),
        )
        self.assertEqual(stats.count(), 1)

    def test_str(self):
        subject, group = self._setup_data()
        stat = DailyAttendanceStat.objects.create(
            subject=subject, group=group, date=date.today(),
        )
        stat.calculate_stats()
        result = str(stat)
        self.assertIn(subject.name, result)
