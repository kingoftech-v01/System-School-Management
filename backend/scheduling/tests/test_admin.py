"""Tests for scheduling admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from scheduling.models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)
from scheduling.admin import (
    RoomAdmin, TimeSlotAdmin, ProfessorAvailabilityAdmin,
    ScheduleEntryAdmin, ScheduleExceptionAdmin, SubstitutionRequestAdmin,
    ScheduleNotificationAdmin, TimetableGenerationAdmin,
)


class SchedulingAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all scheduling models are registered in the admin."""

    def test_room_registered(self):
        self.assertIn(Room, admin.site._registry)

    def test_timeslot_registered(self):
        self.assertIn(TimeSlot, admin.site._registry)

    def test_professor_availability_registered(self):
        self.assertIn(ProfessorAvailability, admin.site._registry)

    def test_schedule_entry_registered(self):
        self.assertIn(ScheduleEntry, admin.site._registry)

    def test_schedule_exception_registered(self):
        self.assertIn(ScheduleException, admin.site._registry)

    def test_substitution_request_registered(self):
        self.assertIn(SubstitutionRequest, admin.site._registry)

    def test_schedule_notification_registered(self):
        self.assertIn(ScheduleNotification, admin.site._registry)

    def test_timetable_generation_registered(self):
        self.assertIn(TimetableGeneration, admin.site._registry)


class RoomAdminTest(TestDataMixin, TestCase):
    """Test RoomAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = RoomAdmin(Room, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('name', 'code', 'building', 'floor', 'capacity', 'room_type', 'is_active', 'tenant')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('room_type', 'is_active', 'building', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('name', 'code', 'building')
        self.assertEqual(self.admin.search_fields, expected)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)


class TimeSlotAdminTest(TestDataMixin, TestCase):
    """Test TimeSlotAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = TimeSlotAdmin(TimeSlot, self.site)

    def test_list_display(self):
        expected = ('name', 'day_of_week', 'start_time', 'end_time', 'slot_type', 'order', 'is_active', 'tenant')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('day_of_week', 'slot_type', 'is_active', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_ordering(self):
        self.assertEqual(self.admin.ordering, ('day_of_week', 'order', 'start_time'))


class ProfessorAvailabilityAdminTest(TestDataMixin, TestCase):
    """Test ProfessorAvailabilityAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ProfessorAvailabilityAdmin(ProfessorAvailability, self.site)

    def test_list_display(self):
        expected = ('professor', 'time_slot', 'preference')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('preference',))

    def test_search_fields(self):
        expected = ('professor__first_name', 'professor__last_name')
        self.assertEqual(self.admin.search_fields, expected)


class ScheduleEntryAdminTest(TestDataMixin, TestCase):
    """Test ScheduleEntryAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ScheduleEntryAdmin(ScheduleEntry, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = (
            'course', 'professor', 'room', 'time_slot', 'filiere',
            'recurrence', 'status', 'is_locked', 'tenant',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'recurrence', 'is_locked', 'semester', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('course__title', 'professor__first_name', 'professor__last_name')
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'updated_at')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_raw_id_fields(self):
        self.assertEqual(self.admin.raw_id_fields, ('professor', 'created_by'))

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)


class ScheduleExceptionAdminTest(TestDataMixin, TestCase):
    """Test ScheduleExceptionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ScheduleExceptionAdmin(ScheduleException, self.site)

    def test_list_display(self):
        expected = (
            'schedule_entry', 'exception_type', 'date',
            'is_approved', 'notification_sent', 'tenant',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('exception_type', 'is_approved', 'notification_sent', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'updated_at')
        self.assertEqual(self.admin.readonly_fields, expected)


class SubstitutionRequestAdminTest(TestDataMixin, TestCase):
    """Test SubstitutionRequestAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = SubstitutionRequestAdmin(SubstitutionRequest, self.site)

    def test_list_display(self):
        expected = (
            'requesting_professor', 'schedule_entry', 'date',
            'status', 'assigned_substitute', 'tenant',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('requesting_professor__first_name', 'requesting_professor__last_name')
        self.assertEqual(self.admin.search_fields, expected)


class ScheduleNotificationAdminTest(TestDataMixin, TestCase):
    """Test ScheduleNotificationAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ScheduleNotificationAdmin(ScheduleNotification, self.site)

    def test_list_display(self):
        expected = ('title', 'recipient', 'notification_type', 'is_read', 'email_sent', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('notification_type', 'is_read', 'email_sent', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('title', 'recipient__first_name', 'recipient__last_name')
        self.assertEqual(self.admin.search_fields, expected)


class TimetableGenerationAdminTest(TestDataMixin, TestCase):
    """Test TimetableGenerationAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = TimetableGenerationAdmin(TimetableGeneration, self.site)

    def test_list_display(self):
        expected = (
            'pk', 'session', 'semester', 'status',
            'entries_created', 'conflicts_found', 'is_published', 'tenant',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'is_published', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'started_at', 'completed_at')
        self.assertEqual(self.admin.readonly_fields, expected)
