"""Tests for attendance app forms."""

from datetime import date
from django.test import TestCase

from tests.helpers import TestDataMixin
from attendance.forms import (
    AttendanceForm, AttendanceReportForm, StudentForm,
    GroupForm, SubjectForm,
)
from attendance.models import Group, Student, Subject, Attendance


class AttendanceFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.professor = self.create_professor_user()
        self.subject = self.create_attendance_subject(teacher=self.professor)

    def test_valid_form(self):
        data = {
            'subject': self.subject.pk,
            'date': '2024-06-01',
        }
        form = AttendanceForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_subject(self):
        data = {'date': '2024-06-01'}
        form = AttendanceForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)

    def test_missing_date(self):
        data = {'subject': self.subject.pk}
        form = AttendanceForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_lecturer_kwarg_accepted(self):
        form = AttendanceForm(lecturer=self.professor)
        self.assertEqual(form.lecturer, self.professor)


class AttendanceReportFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.group = self.create_attendance_group()
        self.student = self.create_attendance_student(group=self.group)

    def test_valid_form(self):
        data = {
            'student': self.student.pk,
            'status': 'present',
        }
        form = AttendanceReportForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_status(self):
        data = {
            'student': self.student.pk,
            'status': 'invalid_status',
        }
        form = AttendanceReportForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_missing_student(self):
        data = {'status': 'present'}
        form = AttendanceReportForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('student', form.errors)


class StudentFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.group = self.create_attendance_group()

    def test_valid_form(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@test.com',
            'group': self.group.pk,
        }
        form = StudentForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = StudentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)
        self.assertIn('email', form.errors)

    def test_invalid_email(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'not-valid',
            'group': self.group.pk,
        }
        form = StudentForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class GroupFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = GroupForm(data={'name': 'Group A'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        form = GroupForm(data={'name': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class SubjectFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.professor = self.create_professor_user()
        self.group = self.create_attendance_group()

    def test_valid_form(self):
        data = {
            'name': 'Mathematics',
            'teacher': self.professor.pk,
            'group': [self.group.pk],
            'slug': 'mathematics',
        }
        form = SubjectForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        data = {
            'teacher': self.professor.pk,
            'group': [self.group.pk],
            'slug': 'test',
        }
        form = SubjectForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
