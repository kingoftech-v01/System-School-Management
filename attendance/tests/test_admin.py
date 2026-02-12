"""Tests for attendance admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from attendance.models import Attendance, AttendanceReport, Group, Student, Subject, DailyAttendanceStat
from attendance.admin import SubjectAdmin


class AttendanceAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all attendance models are registered in the admin."""

    def test_attendance_registered(self):
        self.assertIn(Attendance, admin.site._registry)

    def test_attendance_report_registered(self):
        self.assertIn(AttendanceReport, admin.site._registry)

    def test_group_registered(self):
        self.assertIn(Group, admin.site._registry)

    def test_student_registered(self):
        self.assertIn(Student, admin.site._registry)

    def test_subject_registered(self):
        self.assertIn(Subject, admin.site._registry)

    def test_daily_attendance_stat_registered(self):
        self.assertIn(DailyAttendanceStat, admin.site._registry)


class SubjectAdminTest(TestDataMixin, TestCase):
    """Test SubjectAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = SubjectAdmin(Subject, self.site)

    def test_list_display(self):
        expected = ['name', 'slug', 'teacher']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ['teacher'])

    def test_search_fields(self):
        expected = ['name', 'slug', 'teacher__first_name', 'teacher__last_name']
        self.assertEqual(self.admin.search_fields, expected)

    def test_prepopulated_fields(self):
        self.assertEqual(self.admin.prepopulated_fields, {'slug': ('name',)})

    def test_inlines(self):
        from attendance.admin import M2MInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(M2MInline, inline_classes)
