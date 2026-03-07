"""
Tests for dailystat app Celery tasks.
The send_daily_stats task creates DailyAttendanceStat records for
students who were absent today.
"""

from datetime import date
from unittest.mock import patch

from django.test import TestCase

from attendance.models import (
    Attendance,
    AttendanceReport,
    Group,
    Satus,
    Student,
    Subject,
)
from dailystat.models import DailyAttendanceStat
from dailystat.tasks import send_daily_stats
from tests.helpers import TestDataMixin


class TestSendDailyStats(TestDataMixin, TestCase):
    """Tests for send_daily_stats task."""

    def setUp(self):
        self.teacher = self.create_professor_user()
        self.group = Group.objects.create(name='Group A')
        self.subject = Subject.objects.create(
            name='Math', teacher=self.teacher, slug='math'
        )
        self.subject.group.add(self.group)
        self.student = Student.objects.create(
            first_name='John', last_name='Doe',
            email='john.doe@test.com', group=self.group
        )

    def test_creates_stat_for_absent_student(self):
        """Task should create a DailyAttendanceStat for absent students."""
        today = date.today()
        attendance = Attendance.objects.create(
            subject=self.subject, date=today
        )
        AttendanceReport.objects.create(
            attendance=attendance, student=self.student,
            status=Satus.ABSENT
        )

        send_daily_stats()

        self.assertTrue(
            DailyAttendanceStat.objects.filter(
                student=self.student, day=today
            ).exists()
        )

    def test_adds_subject_to_existing_stat(self):
        """Task should add subjects to existing stat records."""
        today = date.today()
        # Create initial stat
        stat = DailyAttendanceStat.objects.create(
            student=self.student, day=today
        )

        attendance = Attendance.objects.create(
            subject=self.subject, date=today
        )
        AttendanceReport.objects.create(
            attendance=attendance, student=self.student,
            status=Satus.ABSENT
        )

        send_daily_stats()

        stat.refresh_from_db()
        self.assertIn(self.subject, stat.subjects.all())

    def test_no_stat_for_present_students(self):
        """Task should not create stats for present students."""
        today = date.today()
        attendance = Attendance.objects.create(
            subject=self.subject, date=today
        )
        AttendanceReport.objects.create(
            attendance=attendance, student=self.student,
            status=Satus.PRESENT
        )

        send_daily_stats()

        self.assertFalse(
            DailyAttendanceStat.objects.filter(
                student=self.student, day=today
            ).exists()
        )

    def test_no_records_when_no_absences(self):
        """Task should create no stats when there are no absences."""
        send_daily_stats()
        self.assertEqual(DailyAttendanceStat.objects.count(), 0)
