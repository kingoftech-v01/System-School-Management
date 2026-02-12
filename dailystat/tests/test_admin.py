"""Tests for dailystat admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from dailystat.models import DailyAttendanceStat
from dailystat.admin import DailyAttendanceStatAdmin


class DailyStatAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that dailystat models are registered in the admin."""

    def test_daily_attendance_stat_registered(self):
        self.assertIn(DailyAttendanceStat, admin.site._registry)


class DailyAttendanceStatAdminTest(TestDataMixin, TestCase):
    """Test DailyAttendanceStatAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = DailyAttendanceStatAdmin(DailyAttendanceStat, self.site)

    def test_list_display(self):
        expected = ('student', 'day')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('day',))

    def test_search_fields(self):
        expected = ('student__first_name', 'student__last_name', 'day')
        self.assertEqual(self.admin.search_fields, expected)
