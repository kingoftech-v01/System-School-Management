"""Tests for course admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from course.models import Program, Course, CourseAllocation, Upload
from course.admin import CourseAdmin


class CourseAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all course models are registered in the admin."""

    def test_program_registered(self):
        self.assertIn(Program, admin.site._registry)

    def test_course_registered(self):
        self.assertIn(Course, admin.site._registry)

    def test_course_allocation_registered(self):
        self.assertIn(CourseAllocation, admin.site._registry)

    def test_upload_registered(self):
        self.assertIn(Upload, admin.site._registry)


class CourseAdminTest(TestDataMixin, TestCase):
    """Test CourseAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CourseAdmin(Course, self.site)

    def test_list_display(self):
        expected = ['title', 'code', 'credit', 'level', 'year', 'semester']
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ['level', 'year', 'semester']
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ['title', 'code', 'slug']
        self.assertEqual(self.admin.search_fields, expected)
