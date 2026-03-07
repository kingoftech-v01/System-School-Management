"""Tests for events admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from events.models import Event
from events.admin import EventAdmin


class EventsAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that events models are registered in the admin."""

    def test_event_registered(self):
        self.assertIn(Event, admin.site._registry)


class EventAdminTest(TestDataMixin, TestCase):
    """Test EventAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = EventAdmin(Event, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('title', 'event_type', 'start_date', 'end_date', 'target_audience', 'tenant')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('event_type', 'target_audience', 'tenant', 'start_date')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('title', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'reminder_sent')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)
