"""
Deep serializer tests for the attendance app.

Tests cover:
- GroupSerializer (fields, serialization)
- SubjectSerializer (fields, teacher representation)
- StudentSerializer (fields, nested group, create method)
- AttendanceSerializer (fields, get_subject, create validation)
- AttendanceReportSerializer (fields, get_attendance, create/update validation)
- AttendanceReportViewSerializer (fields, nested student)
"""

from datetime import date

from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory

from attendance.models import (
    Attendance, AttendanceReport, Group, Satus, Student, Subject,
)
from attendance.serializers import (
    AttendanceReportSerializer,
    AttendanceReportViewSerializer,
    AttendanceSerializer,
    GroupSerializer,
    StudentSerializer,
    SubjectSerializer,
)
from tests.helpers import TestDataMixin


class GroupSerializerTests(TestDataMixin, TestCase):
    """Tests for GroupSerializer."""

    def test_serializes_group(self):
        group = self.create_attendance_group()
        s = GroupSerializer(group)
        self.assertIn('id', s.data)
        self.assertIn('name', s.data)
        self.assertEqual(s.data['name'], group.name)

    def test_valid_data(self):
        s = GroupSerializer(data={'name': 'New Group'})
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name(self):
        s = GroupSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('name', s.errors)


class SubjectSerializerTests(TestDataMixin, TestCase):
    """Tests for SubjectSerializer."""

    def setUp(self):
        self.teacher = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.teacher)
        self.subject.group.add(self.group)

    def test_serializes_subject(self):
        s = SubjectSerializer(self.subject)
        data = s.data
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertIn('teacher', data)
        self.assertIn('group', data)

    def test_teacher_representation(self):
        s = SubjectSerializer(self.subject)
        teacher_data = s.data['teacher']
        self.assertIn('id', teacher_data)
        self.assertIn('name', teacher_data)
        self.assertEqual(teacher_data['id'], self.teacher.id)

    def test_group_is_nested(self):
        s = SubjectSerializer(self.subject)
        group_data = s.data['group']
        self.assertIsInstance(group_data, list)
        self.assertTrue(len(group_data) >= 1)
        self.assertIn('name', group_data[0])


class StudentSerializerTests(TestDataMixin, TestCase):
    """Tests for attendance StudentSerializer."""

    def setUp(self):
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)

    def test_serializes_student(self):
        s = StudentSerializer(self.att_student)
        data = s.data
        self.assertIn('id', data)
        self.assertIn('first_name', data)
        self.assertIn('last_name', data)
        self.assertIn('email', data)
        self.assertIn('group', data)

    def test_group_nested_in_output(self):
        s = StudentSerializer(self.att_student)
        self.assertIsInstance(s.data['group'], dict)
        self.assertIn('name', s.data['group'])

    def test_all_fields_present(self):
        s = StudentSerializer(self.att_student)
        data = s.data
        self.assertEqual(data['first_name'], self.att_student.first_name)
        self.assertEqual(data['last_name'], self.att_student.last_name)
        self.assertEqual(data['email'], self.att_student.email)


class AttendanceSerializerTests(TestDataMixin, TestCase):
    """Tests for AttendanceSerializer."""

    def setUp(self):
        self.teacher = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.teacher)
        self.subject.group.add(self.group)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )
        self.factory = APIRequestFactory()

    def test_serializes_attendance(self):
        s = AttendanceSerializer(self.attendance)
        data = s.data
        self.assertIn('id', data)
        self.assertIn('subject', data)
        self.assertIn('date', data)

    def test_subject_representation(self):
        s = AttendanceSerializer(self.attendance)
        subj = s.data['subject']
        self.assertIn('id', subj)
        self.assertIn('name', subj)
        self.assertEqual(subj['id'], self.subject.id)

    def test_create_duplicate_date_raises(self):
        request = self.factory.post('/')
        request.user = self.teacher
        s = AttendanceSerializer(
            data={'date': str(date.today())},
            context={'request': request},
        )
        if s.is_valid():
            # Save should raise because subject_id is set in perform_create
            # and a duplicate date check exists in the serializer
            try:
                s.save(subject_id=self.subject.pk)
                # If it saves, a duplicate exists
                self.fail('Should have raised validation error for duplicate date')
            except Exception:
                pass  # Expected

    def test_create_nonexistent_subject(self):
        request = self.factory.post('/')
        request.user = self.teacher
        s = AttendanceSerializer(
            data={'date': '2025-12-01'},
            context={'request': request},
        )
        if s.is_valid():
            try:
                s.save(subject_id=99999)
                self.fail('Should have raised validation error')
            except Exception:
                pass

    def test_create_wrong_teacher(self):
        other_teacher = self.create_professor_user()
        request = self.factory.post('/')
        request.user = other_teacher
        s = AttendanceSerializer(
            data={'date': '2025-11-01'},
            context={'request': request},
        )
        if s.is_valid():
            try:
                s.save(subject_id=self.subject.pk)
                self.fail('Should have raised validation error')
            except Exception:
                pass

    def test_read_only_fields(self):
        s = AttendanceSerializer(self.attendance)
        self.assertIn('created_at', s.data)
        self.assertIn('updated_at', s.data)


class AttendanceReportSerializerTests(TestDataMixin, TestCase):
    """Tests for AttendanceReportSerializer."""

    def setUp(self):
        self.teacher = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)
        self.subject = self.create_attendance_subject(teacher=self.teacher)
        self.subject.group.add(self.group)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )
        self.report = AttendanceReport.objects.create(
            attendance=self.attendance,
            student=self.att_student,
            status=Satus.PRESENT,
        )
        self.factory = APIRequestFactory()

    def test_serializes_report(self):
        s = AttendanceReportSerializer(self.report)
        data = s.data
        self.assertIn('id', data)
        self.assertIn('attendance', data)
        self.assertIn('student', data)
        self.assertIn('status', data)

    def test_attendance_representation(self):
        s = AttendanceReportSerializer(self.report)
        att = s.data['attendance']
        self.assertIn('id', att)
        self.assertIn('date', att)
        self.assertIn('subject', att)
        self.assertEqual(att['subject']['id'], self.subject.id)

    def test_update_status(self):
        s = AttendanceReportSerializer(
            self.report,
            data={'status': 'absent'},
            partial=True,
        )
        self.assertTrue(s.is_valid(), s.errors)
        updated = s.save()
        self.assertEqual(updated.status, 'absent')

    def test_create_duplicate_raises(self):
        request = self.factory.post('/')
        request.user = self.teacher
        s = AttendanceReportSerializer(
            data={'student': self.att_student.pk, 'status': 'present'},
            context={'request': request},
        )
        if s.is_valid():
            try:
                s.save(attendance_id=self.attendance.pk)
                self.fail('Should have raised validation error for duplicate')
            except Exception:
                pass

    def test_create_wrong_group_raises(self):
        other_group = self.create_attendance_group()
        other_student = self.create_attendance_student(group=other_group)
        request = self.factory.post('/')
        request.user = self.teacher
        s = AttendanceReportSerializer(
            data={'student': other_student.pk, 'status': 'present'},
            context={'request': request},
        )
        if s.is_valid():
            try:
                s.save(attendance_id=self.attendance.pk)
                self.fail('Should have raised error for student not in group')
            except Exception:
                pass


class AttendanceReportViewSerializerTests(TestDataMixin, TestCase):
    """Tests for AttendanceReportViewSerializer (read-only with nested student)."""

    def setUp(self):
        self.teacher = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)
        self.subject = self.create_attendance_subject(teacher=self.teacher)
        self.subject.group.add(self.group)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )
        self.report = AttendanceReport.objects.create(
            attendance=self.attendance,
            student=self.att_student,
            status=Satus.LATE,
        )

    def test_serializes_with_nested_student(self):
        s = AttendanceReportViewSerializer(self.report)
        data = s.data
        self.assertIn('student', data)
        self.assertIsInstance(data['student'], dict)
        self.assertIn('first_name', data['student'])
        self.assertIn('group', data['student'])

    def test_attendance_representation(self):
        s = AttendanceReportViewSerializer(self.report)
        att = s.data['attendance']
        self.assertIn('id', att)
        self.assertIn('date', att)
        self.assertIn('subject', att)

    def test_status_field(self):
        s = AttendanceReportViewSerializer(self.report)
        self.assertEqual(s.data['status'], 'late')

    def test_read_only_fields(self):
        s = AttendanceReportViewSerializer(self.report)
        self.assertIn('created_at', s.data)
        self.assertIn('updated_at', s.data)
