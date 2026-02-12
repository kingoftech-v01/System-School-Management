"""Tests for alumni admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from alumni.models import Alumni, AlumniEvent, AlumniDonation, AlumniAchievement
from alumni.admin import (
    AlumniAdmin, AlumniEventAdmin, AlumniDonationAdmin, AlumniAchievementAdmin,
)


class AlumniAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all alumni models are registered in the admin."""

    def test_alumni_registered(self):
        self.assertIn(Alumni, admin.site._registry)

    def test_alumni_event_registered(self):
        self.assertIn(AlumniEvent, admin.site._registry)

    def test_alumni_donation_registered(self):
        self.assertIn(AlumniDonation, admin.site._registry)

    def test_alumni_achievement_registered(self):
        self.assertIn(AlumniAchievement, admin.site._registry)


class AlumniAdminTest(TestDataMixin, TestCase):
    """Test AlumniAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AlumniAdmin(Alumni, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('student', 'graduation_year', 'current_occupation', 'current_employer', 'is_active')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('graduation_year', 'is_active', 'willing_to_mentor')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('student__student__first_name', 'student__student__last_name', 'personal_email', 'current_employer')
        self.assertEqual(self.admin.search_fields, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'activate_alumni'))
        self.assertTrue(hasattr(self.admin, 'deactivate_alumni'))

    def test_activate_alumni_action(self):
        alum = self.create_alumni()
        alum.is_active = False
        alum.save()
        qs = Alumni.objects.filter(pk=alum.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.activate_alumni(request, qs)
        alum.refresh_from_db()
        self.assertTrue(alum.is_active)

    def test_deactivate_alumni_action(self):
        alum = self.create_alumni()
        qs = Alumni.objects.filter(pk=alum.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.deactivate_alumni(request, qs)
        alum.refresh_from_db()
        self.assertFalse(alum.is_active)


class AlumniEventAdminTest(TestDataMixin, TestCase):
    """Test AlumniEventAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AlumniEventAdmin(AlumniEvent, self.site)

    def test_list_display(self):
        expected = ('title', 'event_type', 'event_date', 'location', 'get_attendee_count', 'is_active', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('event_type', 'event_date', 'is_active', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('title', 'description', 'location')
        self.assertEqual(self.admin.search_fields, expected)

    def test_get_attendee_count(self):
        event = self.create_alumni_event()
        count = self.admin.get_attendee_count(event)
        self.assertEqual(count, 0)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'event_date')


class AlumniDonationAdminTest(TestDataMixin, TestCase):
    """Test AlumniDonationAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AlumniDonationAdmin(AlumniDonation, self.site)

    def test_list_display(self):
        expected = ('alumni', 'amount', 'currency', 'purpose', 'is_anonymous', 'tax_receipt_sent', 'donated_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('purpose', 'is_anonymous', 'currency', 'tax_receipt_sent', 'donated_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'mark_receipt_sent'))
        self.assertTrue(hasattr(self.admin, 'mark_thank_you_sent'))


class AlumniAchievementAdminTest(TestDataMixin, TestCase):
    """Test AlumniAchievementAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AlumniAchievementAdmin(AlumniAchievement, self.site)

    def test_list_display(self):
        expected = ('alumni', 'title', 'achievement_type', 'is_featured', 'is_published', 'achievement_date', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('achievement_type', 'is_featured', 'is_published', 'achievement_date')
        self.assertEqual(self.admin.list_filter, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'feature_achievements'))
        self.assertTrue(hasattr(self.admin, 'unfeature_achievements'))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'achievement_date')
