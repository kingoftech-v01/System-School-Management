"""Tests for dailystat app serializers."""

from datetime import date
from django.test import TestCase
from django.contrib.auth import get_user_model

from attendance.models import Group, Student, Subject
from dailystat.models import DailyAttendanceStat
from dailystat.serializers import DailyAttendanceStatSerializer

User = get_user_model()


class DailyAttendanceStatSerializerTest(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name='Group A')
        self.student = Student.objects.create(
            first_name='John', last_name='Doe',
            email='john@test.com', group=self.group,
        )
        self.teacher = User.objects.create_user(
            username='teacher1', password='TestPass123!@#',
        )
        self.subject = Subject.objects.create(
            name='Math (101)', teacher=self.teacher, slug='math-101',
        )
        self.subject.group.add(self.group)

    def test_serialize(self):
        stat = DailyAttendanceStat.objects.create(
            student=self.student, day=date.today(),
        )
        stat.subjects.add(self.subject)
        serializer = DailyAttendanceStatSerializer(stat)
        data = serializer.data
        self.assertEqual(data['student']['id'], self.student.pk)
        self.assertEqual(data['student']['first_name'], 'John')
        self.assertEqual(data['student']['last_name'], 'Doe')

    def test_subjects_serialized(self):
        stat = DailyAttendanceStat.objects.create(
            student=self.student, day=date.today(),
        )
        stat.subjects.add(self.subject)
        serializer = DailyAttendanceStatSerializer(stat)
        data = serializer.data
        self.assertEqual(len(data['subjects']), 1)
        self.assertEqual(data['subjects'][0]['id'], self.subject.pk)
        # Name should be split at '(' and stripped
        self.assertEqual(data['subjects'][0]['name'], 'Math')

    def test_empty_subjects(self):
        stat = DailyAttendanceStat.objects.create(
            student=self.student, day=date.today(),
        )
        serializer = DailyAttendanceStatSerializer(stat)
        data = serializer.data
        self.assertEqual(data['subjects'], [])

    def test_day_field(self):
        stat = DailyAttendanceStat.objects.create(
            student=self.student, day=date(2024, 6, 15),
        )
        serializer = DailyAttendanceStatSerializer(stat)
        self.assertEqual(serializer.data['day'], '2024-06-15')
