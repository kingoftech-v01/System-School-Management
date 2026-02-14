"""Tests for core admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from core.models import School, Domain, Session, Semester, NewsAndEvents, ActivityLog
from core.admin import SessionAdmin, SemesterAdmin, ActivityLogAdmin, NewsAndEventsAdmin


class CoreAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all core models are registered in the admin."""

    def test_school_registered(self):
        self.assertIn(School, admin.site._registry)

    def test_domain_registered(self):
        self.assertIn(Domain, admin.site._registry)

    def test_session_registered(self):
        self.assertIn(Session, admin.site._registry)

    def test_semester_registered(self):
        self.assertIn(Semester, admin.site._registry)

    def test_news_and_events_registered(self):
        self.assertIn(NewsAndEvents, admin.site._registry)

    def test_activity_log_registered(self):
        self.assertIn(ActivityLog, admin.site._registry)


class SessionAdminTest(TestDataMixin, TestCase):
    """Test SessionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = SessionAdmin(Session, self.site)

    def test_list_display(self):
        expected = ('session', 'is_current_session', 'next_session_begins')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('is_current_session',))


class SemesterAdminTest(TestDataMixin, TestCase):
    """Test SemesterAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = SemesterAdmin(Semester, self.site)

    def test_list_display(self):
        expected = ('semester', 'session', 'is_current_semester', 'next_semester_begins')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('is_current_semester', 'session'))


class ActivityLogAdminTest(TestDataMixin, TestCase):
    """Test ActivityLogAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ActivityLogAdmin(ActivityLog, self.site)

    def test_list_display(self):
        expected = ('message', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('created_at',))

    def test_search_fields(self):
        self.assertEqual(self.admin.search_fields, ('message',))

    def test_readonly_fields(self):
        self.assertEqual(self.admin.readonly_fields, ('created_at',))


class NewsAndEventsAdminTest(TestDataMixin, TestCase):
    """Test NewsAndEventsAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NewsAndEventsAdmin(NewsAndEvents, self.site)

    def test_list_display(self):
        expected = ('title', 'posted_as', 'upload_time', 'updated_date')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('posted_as', 'upload_time'))

    def test_search_fields(self):
        self.assertEqual(self.admin.search_fields, ('title', 'summary'))


class SchoolAdminTest(TestDataMixin, TestCase):
    """Test SchoolAdmin configuration."""

    def test_school_admin_list_display_contains_name(self):
        admin_instance = admin.site._registry[School]
        self.assertIn('name', admin_instance.list_display)

    def test_school_admin_list_display_contains_slug(self):
        admin_instance = admin.site._registry[School]
        self.assertIn('slug', admin_instance.list_display)

    def test_school_admin_list_display_contains_is_active(self):
        admin_instance = admin.site._registry[School]
        self.assertIn('is_active', admin_instance.list_display)

    def test_school_admin_search_fields_contains_name(self):
        admin_instance = admin.site._registry[School]
        self.assertIn('name', admin_instance.search_fields)

    def test_school_admin_list_filter_contains_is_active(self):
        admin_instance = admin.site._registry[School]
        self.assertIn('is_active', admin_instance.list_filter)
