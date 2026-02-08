"""Tests for dailystat app models."""

from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from attendance.models import Group, Student, Subject, Attendance, AttendanceReport, Satus
from dailystat.models import DailyAttendanceStat

User = get_user_model()


class DailyAttendanceStatHelperMixin:
    """Helper for creating attendance-related test data."""

    def _create_group(self, name='Group A'):
        return Group.objects.create(name=name)

    def _create_att_student(self, group=None, **kwargs):
        if group is None:
            group = self._create_group()
        defaults = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': f'john{Student.objects.count()}@test.com',
            'group': group,
        }
        defaults.update(kwargs)
        return Student.objects.create(**defaults)

    def _create_teacher(self):
        return User.objects.create_user(
            username=f'teacher{User.objects.count()}',
            password='TestPass123!@#',
        )

    def _create_subject(self, teacher=None, groups=None):
        if teacher is None:
            teacher = self._create_teacher()
        subject = Subject.objects.create(
            name='Math', teacher=teacher,
            slug=f'math-{Subject.objects.count()}',
        )
        if groups:
            subject.group.set(groups)
        return subject


class DailyAttendanceStatModelTest(DailyAttendanceStatHelperMixin, TestCase):
    def test_create(self):
        group = self._create_group()
        student = self._create_att_student(group=group)
        subject = self._create_subject(groups=[group])
        stat = DailyAttendanceStat.objects.create(student=student, day=date.today())
        stat.subjects.add(subject)
        self.assertIsNotNone(stat.pk)
        self.assertEqual(stat.day, date.today())
        self.assertEqual(stat.subjects.count(), 1)

    def test_multiple_students(self):
        group = self._create_group()
        s1 = self._create_att_student(group=group, first_name='Alice')
        s2 = self._create_att_student(group=group, first_name='Bob')
        DailyAttendanceStat.objects.create(student=s1, day=date.today())
        DailyAttendanceStat.objects.create(student=s2, day=date.today())
        self.assertEqual(DailyAttendanceStat.objects.count(), 2)

    def test_ordering(self):
        group = self._create_group()
        student = self._create_att_student(group=group)
        stat1 = DailyAttendanceStat.objects.create(student=student, day=date(2024, 1, 1))
        stat2 = DailyAttendanceStat.objects.create(student=student, day=date(2024, 6, 1))
        stats = list(DailyAttendanceStat.objects.all())
        # ordering is ['-day'], so newest first
        self.assertEqual(stats[0], stat2)
        self.assertEqual(stats[1], stat1)

    def test_multiple_subjects(self):
        group = self._create_group()
        student = self._create_att_student(group=group)
        teacher = self._create_teacher()
        subj1 = self._create_subject(teacher=teacher, groups=[group])
        subj2 = Subject.objects.create(
            name='Physics', teacher=teacher, slug='physics-1',
        )
        subj2.group.add(group)
        stat = DailyAttendanceStat.objects.create(student=student, day=date.today())
        stat.subjects.add(subj1, subj2)
        self.assertEqual(stat.subjects.count(), 2)

    def test_verbose_names(self):
        self.assertEqual(
            DailyAttendanceStat._meta.verbose_name,
            'Daily Attendance Stat',
        )
