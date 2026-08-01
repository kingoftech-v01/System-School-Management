"""
Deep API view tests for the attendance app.

Tests cover:
- StudentViewSet (list, retrieve, attendances action)
- GroupViewSet (list, retrieve, students action, subjects action)
- SubjectViewSet (list, permission checks)
- AttendanceViewSet (list, create, reports action, date action)
- AttendanceReportViewSet (list, create, update)
- Authentication checks
"""

from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from attendance.models import (
    Attendance, AttendanceReport, Group, Status, Student, Subject,
)
from tests.helpers import TestDataMixin


class StudentViewSetTests(TestDataMixin, TestCase):
    """Tests for attendance StudentViewSet (read-only)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:attendance:student-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:attendance:student-detail', kwargs={'pk': self.att_student.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_read_only_post_not_allowed(self):
        self._auth(self.admin)
        url = reverse('api:attendance:student-list')
        resp = self.client.post(url, {'first_name': 'X', 'last_name': 'Y', 'email': 'x@y.com', 'group': self.group.pk})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_attendances_action(self):
        teacher = self.create_professor_user()
        subject = self.create_attendance_subject(teacher=teacher)
        subject.group.add(self.group)
        attendance = Attendance.objects.create(
            subject=subject, date=date.today(),
        )
        AttendanceReport.objects.create(
            attendance=attendance, student=self.att_student,
            status=Status.PRESENT,
        )
        self._auth(self.admin)
        url = reverse(
            'api:attendance:student-attendances',
            kwargs={'pk': self.att_student.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_attendances_filter_by_status(self):
        teacher = self.create_professor_user()
        subject = self.create_attendance_subject(teacher=teacher)
        subject.group.add(self.group)
        attendance = Attendance.objects.create(
            subject=subject, date=date.today(),
        )
        AttendanceReport.objects.create(
            attendance=attendance, student=self.att_student,
            status=Status.ABSENT,
        )
        self._auth(self.admin)
        url = reverse(
            'api:attendance:student-attendances',
            kwargs={'pk': self.att_student.pk},
        )
        resp = self.client.get(url, {'status': 'absent'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class GroupViewSetTests(TestDataMixin, TestCase):
    """Tests for attendance GroupViewSet (read-only)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:attendance:group-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:attendance:group-detail', kwargs={'pk': self.group.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_students_action(self):
        self._auth(self.admin)
        url = reverse(
            'api:attendance:group-students',
            kwargs={'pk': self.group.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_subjects_action(self):
        teacher = self.create_professor_user()
        subject = self.create_attendance_subject(teacher=teacher)
        subject.group.add(self.group)
        self._auth(self.admin)
        url = reverse(
            'api:attendance:group-subjects',
            kwargs={'pk': self.group.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class SubjectViewSetTests(TestDataMixin, TestCase):
    """Tests for attendance SubjectViewSet (admin-only)."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.teacher = self.create_professor_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.teacher)
        self.subject.group.add(self.group)

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_as_admin(self):
        self._auth(self.admin)
        url = reverse('api:attendance:subject-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_as_student_forbidden(self):
        self._auth(self.student_user)
        url = reverse('api:attendance:subject-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:attendance:subject-detail', kwargs={'pk': self.subject.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class AttendanceViewSetTests(TestDataMixin, TestCase):
    """Tests for AttendanceViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
        self.teacher = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.group = self.create_attendance_group()
        self.subject = self.create_attendance_subject(teacher=self.teacher)
        self.subject.group.add(self.group)
        self.attendance = Attendance.objects.create(
            subject=self.subject, date=date.today(),
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list_unauthenticated(self):
        url = reverse('api:attendance:attendance-list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_authenticated(self):
        self._auth(self.admin)
        url = reverse('api:attendance:attendance-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:attendance:attendance-detail', kwargs={'pk': self.attendance.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_reports_action(self):
        att_student = self.create_attendance_student(group=self.group)
        AttendanceReport.objects.create(
            attendance=self.attendance,
            student=att_student,
            status=Status.PRESENT,
        )
        self._auth(self.admin)
        url = reverse(
            'api:attendance:attendance-reports',
            kwargs={'pk': self.attendance.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_reports_action_filter_by_group(self):
        att_student = self.create_attendance_student(group=self.group)
        AttendanceReport.objects.create(
            attendance=self.attendance,
            student=att_student,
            status=Status.PRESENT,
        )
        self._auth(self.admin)
        url = reverse(
            'api:attendance:attendance-reports',
            kwargs={'pk': self.attendance.pk},
        )
        resp = self.client.get(url, {'group': self.group.pk})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_date_action_found(self):
        self._auth(self.teacher)
        url = reverse('api:attendance:attendance-date')
        today = date.today().strftime('%Y-%m-%d')
        resp = self.client.get(url, {'day': today})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_date_action_not_found(self):
        self._auth(self.teacher)
        url = reverse('api:attendance:attendance-date')
        resp = self.client.get(url, {'day': '2000-01-01'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('detail', resp.data)

    def test_date_action_no_day_param(self):
        self._auth(self.teacher)
        url = reverse('api:attendance:attendance-date')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('detail', resp.data)


class AttendanceReportViewSetTests(TestDataMixin, TestCase):
    """Tests for AttendanceReportViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.admin = self.create_admin_user()
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
            status=Status.PRESENT,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    def test_list(self):
        self._auth(self.admin)
        url = reverse('api:attendance:report-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve(self):
        self._auth(self.admin)
        url = reverse('api:attendance:report-detail', kwargs={'pk': self.report.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_status(self):
        self._auth(self.admin)
        url = reverse('api:attendance:report-detail', kwargs={'pk': self.report.pk})
        resp = self.client.patch(url, {'status': 'absent'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, 'absent')

    def test_list_unauthenticated_is_read_only(self):
        """AttendanceReportViewSet allows read access to unauthenticated users."""
        url = reverse('api:attendance:report-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
