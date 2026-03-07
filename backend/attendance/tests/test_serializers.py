"""Tests for attendance app serializers."""

from datetime import date
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from attendance.serializers import (
    GroupSerializer, SubjectSerializer, StudentSerializer,
    AttendanceSerializer, AttendanceReportSerializer,
    AttendanceReportViewSerializer,
)
from attendance.models import Group, Student, Subject, Attendance, AttendanceReport


class GroupSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        group = self.create_attendance_group()
        serializer = GroupSerializer(group)
        self.assertIn('name', serializer.data)
        self.assertIn('id', serializer.data)

    def test_all_fields(self):
        group = self.create_attendance_group()
        serializer = GroupSerializer(group)
        self.assertEqual(serializer.data['name'], group.name)


class SubjectSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.professor = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.professor)
        self.subject.group.add(self.group)

    def test_serializes(self):
        serializer = SubjectSerializer(self.subject)
        self.assertIn('name', serializer.data)
        self.assertIn('teacher', serializer.data)
        self.assertIn('group', serializer.data)

    def test_teacher_field_structure(self):
        serializer = SubjectSerializer(self.subject)
        teacher_data = serializer.data['teacher']
        self.assertIn('id', teacher_data)
        self.assertIn('name', teacher_data)

    def test_group_nested(self):
        serializer = SubjectSerializer(self.subject)
        groups = serializer.data['group']
        self.assertIsInstance(groups, list)
        self.assertEqual(len(groups), 1)
        self.assertIn('name', groups[0])


class StudentSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.group = self.create_attendance_group()
        self.student = self.create_attendance_student(group=self.group)

    def test_serializes(self):
        serializer = StudentSerializer(self.student)
        self.assertIn('first_name', serializer.data)
        self.assertIn('last_name', serializer.data)
        self.assertIn('email', serializer.data)

    def test_group_nested(self):
        serializer = StudentSerializer(self.student)
        self.assertIn('group', serializer.data)
        self.assertIsInstance(serializer.data['group'], dict)
        self.assertEqual(serializer.data['group']['name'], self.group.name)


class AttendanceSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.professor = self.create_professor_user()
        self.subject = self.create_attendance_subject(teacher=self.professor)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )

    def test_serializes(self):
        serializer = AttendanceSerializer(self.attendance)
        self.assertIn('id', serializer.data)
        self.assertIn('subject', serializer.data)
        self.assertIn('date', serializer.data)

    def test_subject_field_structure(self):
        serializer = AttendanceSerializer(self.attendance)
        subject_data = serializer.data['subject']
        self.assertIn('id', subject_data)
        self.assertIn('name', subject_data)

    def test_read_only_fields(self):
        serializer = AttendanceSerializer(self.attendance)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)


class AttendanceReportSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.professor = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.professor)
        self.subject.group.add(self.group)
        self.student = self.create_attendance_student(group=self.group)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )
        self.report = AttendanceReport.objects.create(
            attendance=self.attendance, student=self.student, status='present',
        )

    def test_serializes(self):
        serializer = AttendanceReportSerializer(self.report)
        self.assertIn('id', serializer.data)
        self.assertIn('attendance', serializer.data)
        self.assertIn('student', serializer.data)
        self.assertIn('status', serializer.data)

    def test_attendance_field_structure(self):
        serializer = AttendanceReportSerializer(self.report)
        att_data = serializer.data['attendance']
        self.assertIn('id', att_data)
        self.assertIn('date', att_data)
        self.assertIn('subject', att_data)

    def test_update_changes_status(self):
        serializer = AttendanceReportSerializer(
            self.report, data={'status': 'absent'}, partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.status, 'absent')


class AttendanceReportViewSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.professor = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.professor)
        self.subject.group.add(self.group)
        self.student = self.create_attendance_student(group=self.group)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )
        self.report = AttendanceReport.objects.create(
            attendance=self.attendance, student=self.student, status='present',
        )

    def test_serializes(self):
        serializer = AttendanceReportViewSerializer(self.report)
        self.assertIn('student', serializer.data)
        self.assertIn('attendance', serializer.data)

    def test_student_nested_fully(self):
        serializer = AttendanceReportViewSerializer(self.report)
        student_data = serializer.data['student']
        self.assertIn('first_name', student_data)
        self.assertIn('group', student_data)
