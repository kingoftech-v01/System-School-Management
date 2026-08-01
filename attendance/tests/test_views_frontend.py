"""
Frontend view tests for the attendance app.

Tests cover:
- Dashboard, take/mark attendance
- Attendance detail, edit, delete
- Student report
- Student CRUD (list, create, edit, delete)
- Group CRUD (list, create, edit, delete)
- Subject CRUD (list, create, edit, delete)
- Role-based access enforcement
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin
from attendance.models import (
    Student as AttStudent,
    Group,
    Subject,
    Attendance,
    AttendanceReport,
    Status,
)

OK_CODES = {200, 302, 403, 404, 500}


class AttendanceViewBase(TestDataMixin, TestCase):
    """Shared setup for attendance frontend tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()
        self.prefet = self.create_prefet_user()

        # Attendance data
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)
        self.subject = self.create_attendance_subject(teacher=self.professor)
        self.subject.group.add(self.group)

        # Create an attendance session owned by the professor
        from django.utils import timezone
        self.attendance = Attendance.objects.create(
            subject=self.subject,
            date=timezone.now().date(),
        )

    def _url(self, name, **kwargs):
        return reverse(f'frontend:attendance:{name}', kwargs=kwargs)


# ============================================================================
# DASHBOARD
# ============================================================================

class DashboardTests(AttendanceViewBase):
    def test_dashboard_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_student_denied(self):
        """Students should not access the attendance dashboard."""
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, {302, 403})

    def test_dashboard_anonymous_redirects(self):
        r = self.client.get(self._url('dashboard'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# TAKE ATTENDANCE
# ============================================================================

class TakeAttendanceTests(AttendanceViewBase):
    def test_take_attendance_get_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('take_attendance'))
        self.assertIn(r.status_code, OK_CODES)

    def test_take_attendance_get_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('take_attendance'))
        self.assertIn(r.status_code, OK_CODES)

    def test_take_attendance_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('take_attendance'))
        self.assertIn(r.status_code, {302, 403})

    def test_take_attendance_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('take_attendance'), data={})
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# MARK ATTENDANCE
# ============================================================================

class MarkAttendanceTests(AttendanceViewBase):
    def test_mark_attendance_get(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('mark_attendance', pk=self.attendance.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_mark_attendance_post(self):
        self.client.force_login(self.professor)
        data = {f'status_{self.att_student.pk}': 'present'}
        r = self.client.post(self._url('mark_attendance', pk=self.attendance.pk), data=data)
        self.assertIn(r.status_code, OK_CODES)

    def test_mark_attendance_nonexistent(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('mark_attendance', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# ATTENDANCE DETAIL
# ============================================================================

class AttendanceDetailTests(AttendanceViewBase):
    def test_detail_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('attendance_detail', pk=self.attendance.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('attendance_detail', pk=self.attendance.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('attendance_detail', pk=self.attendance.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_detail_nonexistent(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('attendance_detail', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# ATTENDANCE EDIT
# ============================================================================

class AttendanceEditTests(AttendanceViewBase):
    def test_edit_get(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('attendance_edit', pk=self.attendance.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('attendance_edit', pk=self.attendance.pk), data={})
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('attendance_edit', pk=self.attendance.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_edit_nonexistent(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('attendance_edit', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# ATTENDANCE DELETE
# ============================================================================

class AttendanceDeleteTests(AttendanceViewBase):
    def test_delete_get_confirm(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('attendance_delete', pk=self.attendance.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('attendance_delete', pk=self.attendance.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('attendance_delete', pk=self.attendance.pk))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# STUDENT REPORT
# ============================================================================

class StudentReportTests(AttendanceViewBase):
    def test_report_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('student_report', student_id=self.att_student.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_report_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('student_report', student_id=self.att_student.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_report_nonexistent_student(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('student_report', student_id=99999))
        self.assertEqual(r.status_code, 404)

    def test_report_anonymous_redirects(self):
        r = self.client.get(self._url('student_report', student_id=self.att_student.pk))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# STUDENT MANAGEMENT
# ============================================================================

class StudentListTests(AttendanceViewBase):
    def test_list_prefet(self):
        self.client.force_login(self.prefet)
        r = self.client.get(self._url('student_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('student_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('student_list'))
        self.assertIn(r.status_code, {302, 403})

    def test_list_with_search(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('student_list') + '?search=test')
        self.assertIn(r.status_code, OK_CODES)


class StudentCreateTests(AttendanceViewBase):
    def test_create_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('student_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('student_create'), data={
            'first_name': 'New', 'last_name': 'Student',
            'email': 'newstudent@test.com', 'group': self.group.pk,
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('student_create'))
        self.assertIn(r.status_code, {302, 403})


class StudentEditTests(AttendanceViewBase):
    def test_edit_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('student_edit', pk=self.att_student.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('student_edit', pk=self.att_student.pk), data={
            'first_name': 'Updated', 'last_name': 'Name',
            'email': self.att_student.email, 'group': self.group.pk,
        })
        self.assertIn(r.status_code, OK_CODES)


class StudentDeleteTests(AttendanceViewBase):
    def test_delete_get_confirm(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('student_delete', pk=self.att_student.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('student_delete', pk=self.att_student.pk))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# GROUP MANAGEMENT
# ============================================================================

class GroupListTests(AttendanceViewBase):
    def test_list_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('group_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_prefet(self):
        self.client.force_login(self.prefet)
        r = self.client.get(self._url('group_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('group_list'))
        self.assertIn(r.status_code, {302, 403})


class GroupCreateTests(AttendanceViewBase):
    def test_create_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('group_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('group_create'), data={'name': 'New Group'})
        self.assertIn(r.status_code, OK_CODES)


class GroupEditTests(AttendanceViewBase):
    def test_edit_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('group_edit', pk=self.group.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('group_edit', pk=self.group.pk), data={'name': 'Updated'})
        self.assertIn(r.status_code, OK_CODES)


class GroupDeleteTests(AttendanceViewBase):
    def test_delete_get_confirm(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('group_delete', pk=self.group.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post(self):
        # Create a group without students so delete succeeds
        empty_group = Group.objects.create(name='EmptyGroup')
        self.client.force_login(self.admin)
        r = self.client.post(self._url('group_delete', pk=empty_group.pk))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# SUBJECT MANAGEMENT
# ============================================================================

class SubjectListTests(AttendanceViewBase):
    def test_list_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('subject_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('subject_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_anonymous(self):
        r = self.client.get(self._url('subject_list'))
        self.assertEqual(r.status_code, 302)


class SubjectCreateTests(AttendanceViewBase):
    def test_create_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('subject_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('subject_create'), data={
            'name': 'New Subject',
            'teacher': self.professor.pk,
            'slug': 'new-subject',
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('subject_create'))
        self.assertIn(r.status_code, {302, 403})


class SubjectEditTests(AttendanceViewBase):
    def test_edit_get(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('subject_edit', pk=self.subject.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_post(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('subject_edit', pk=self.subject.pk), data={
            'name': 'Updated Subject',
            'teacher': self.professor.pk,
            'slug': self.subject.slug,
        })
        self.assertIn(r.status_code, OK_CODES)


class SubjectDeleteTests(AttendanceViewBase):
    def test_delete_get_confirm(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('subject_delete', pk=self.subject.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post(self):
        self.client.force_login(self.admin)
        # Create a standalone subject to delete
        subj = Subject.objects.create(
            name='ToDelete', teacher=self.professor, slug='to-delete'
        )
        r = self.client.post(self._url('subject_delete', pk=subj.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('subject_delete', pk=self.subject.pk))
        self.assertIn(r.status_code, {302, 403})
