"""Tests for result admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from result.models import TakenCourse, Result
from result.admin import ScoreAdmin


class ResultAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all result models are registered in the admin."""

    def test_taken_course_registered(self):
        self.assertIn(TakenCourse, admin.site._registry)

    def test_result_registered(self):
        self.assertIn(Result, admin.site._registry)


class ScoreAdminTest(TestDataMixin, TestCase):
    """Test ScoreAdmin (TakenCourse admin) configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ScoreAdmin(TakenCourse, self.site)

    def test_list_display(self):
        expected = [
            "student", "course", "assignment", "mid_exam", "quiz",
            "attendance", "final_exam", "total", "grade", "comment",
        ]
        self.assertEqual(self.admin.list_display, expected)

    def test_admin_uses_score_admin_class(self):
        """Verify TakenCourse is registered with ScoreAdmin."""
        registered_admin = admin.site._registry[TakenCourse]
        self.assertIsInstance(registered_admin, ScoreAdmin)
