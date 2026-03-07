"""Tests for attendance app API views."""

from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from attendance.models import Group, Student, Subject, Attendance, AttendanceReport


class StudentViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.group = self.create_attendance_group()
        self.student = self.create_attendance_student(group=self.group)

    def test_list_students(self):
        resp = self.client.get('/api/v1/attendance/students/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_student(self):
        resp = self.client.get(f'/api/v1/attendance/students/{self.student.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['first_name'], self.student.first_name)

    def test_read_only_no_post(self):
        data = {
            'first_name': 'New',
            'last_name': 'Student',
            'email': 'new@test.com',
            'group': {'name': self.group.name},
        }
        resp = self.client.post('/api/v1/attendance/students/', data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_read_only_no_delete(self):
        resp = self.client.delete(f'/api/v1/attendance/students/{self.student.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class GroupViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.group = self.create_attendance_group()

    def test_list_groups(self):
        resp = self.client.get('/api/v1/attendance/groups/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_group(self):
        resp = self.client.get(f'/api/v1/attendance/groups/{self.group.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_group_students_action(self):
        self.create_attendance_student(group=self.group)
        resp = self.client.get(f'/api/v1/attendance/groups/{self.group.pk}/students/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_read_only_no_post(self):
        resp = self.client.post('/api/v1/attendance/groups/', {'name': 'X'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class SubjectViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.professor = self.create_professor_user()
        self.subject = self.create_attendance_subject(teacher=self.professor)

    def test_admin_can_list(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v1/attendance/subjects/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_non_admin_denied(self):
        student = self.create_student_user()
        self.client.force_authenticate(user=student)
        resp = self.client.get('/api/v1/attendance/subjects/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_denied(self):
        resp = self.client.get('/api/v1/attendance/subjects/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class AttendanceViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.professor = self.create_professor_user()
        self.client.force_authenticate(user=self.professor)
        self.subject = self.create_attendance_subject(teacher=self.professor)

    def test_list_attendances(self):
        resp = self.client.get('/api/v1/attendance/attendances/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/attendance/attendances/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_date_action_no_day(self):
        resp = self.client.get('/api/v1/attendance/attendances/date/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['detail'], 'Attendance not found')

    def test_date_action_with_invalid_day(self):
        resp = self.client.get('/api/v1/attendance/attendances/date/?day=2024-01-01')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
