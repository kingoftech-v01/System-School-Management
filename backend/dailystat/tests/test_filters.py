"""
Tests for dailystat app filters.
"""

from datetime import date

from django.test import TestCase

from attendance.models import Group, Student, Subject
from dailystat.filters import DailyAttendanceStatFilter
from dailystat.models import DailyAttendanceStat
from tests.helpers import TestDataMixin


class TestDailyAttendanceStatFilter(TestDataMixin, TestCase):
    """Tests for DailyAttendanceStatFilter."""

    def setUp(self):
        self.teacher = self.create_professor_user()
        self.group = Group.objects.create(name='L1-A')
        self.subject = Subject.objects.create(
            name='Physics', teacher=self.teacher, slug='physics'
        )
        self.subject.group.add(self.group)

        self.student1 = Student.objects.create(
            first_name='Alice', last_name='Martin',
            email='alice@test.com', group=self.group
        )
        self.student2 = Student.objects.create(
            first_name='Bob', last_name='Johnson',
            email='bob@test.com', group=self.group
        )

        today = date.today()
        self.stat1 = DailyAttendanceStat.objects.create(
            student=self.student1, day=today
        )
        self.stat1.subjects.add(self.subject)

        self.stat2 = DailyAttendanceStat.objects.create(
            student=self.student2, day=today
        )
        self.stat2.subjects.add(self.subject)

    def test_filter_by_student_first_name(self):
        """Filter should match student by first name."""
        qs = DailyAttendanceStat.objects.all()
        f = DailyAttendanceStatFilter(data={'student': 'Alice'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.stat1)

    def test_filter_by_student_last_name(self):
        """Filter should match student by last name."""
        qs = DailyAttendanceStat.objects.all()
        f = DailyAttendanceStatFilter(data={'student': 'Johnson'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.stat2)

    def test_filter_by_subject_slug(self):
        """Filter should match by subject slug."""
        qs = DailyAttendanceStat.objects.all()
        f = DailyAttendanceStatFilter(data={'subjects': 'physics'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 2)

    def test_filter_by_group_name(self):
        """Filter should match by student's group name."""
        qs = DailyAttendanceStat.objects.all()
        f = DailyAttendanceStatFilter(data={'group': 'L1-A'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 2)
