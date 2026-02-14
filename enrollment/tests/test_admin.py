"""Tests for enrollment admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from enrollment.models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory
from enrollment.admin import (
    RegistrationFormAdmin, EnrollmentDocumentAdmin, EnrollmentStatusHistoryAdmin,
)


class EnrollmentAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all enrollment models are registered in the admin."""

    def test_registration_form_registered(self):
        self.assertIn(RegistrationForm, admin.site._registry)

    def test_enrollment_document_registered(self):
        self.assertIn(EnrollmentDocument, admin.site._registry)

    def test_enrollment_status_history_registered(self):
        self.assertIn(EnrollmentStatusHistory, admin.site._registry)


class RegistrationFormAdminTest(TestDataMixin, TestCase):
    """Test RegistrationFormAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = RegistrationFormAdmin(RegistrationForm, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = (
            'student_full_name', 'colored_status', 'enrollment_type', 'filiere',
            'academic_year', 'submitted_at', 'completion_badge', 'reviewed_by', 'tenant',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = (
            'status', 'enrollment_type', 'level', 'academic_year',
            'gender', 'filiere', 'submitted_at', 'tenant',
        )
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = (
            'student_first_name', 'student_last_name', 'email', 'phone',
            'parent_first_name', 'parent_last_name', 'parent_email',
        )
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'submitted_at')

    def test_list_per_page(self):
        self.assertEqual(self.admin.list_per_page, 50)

    def test_inlines(self):
        from enrollment.admin import EnrollmentDocumentInline, EnrollmentStatusHistoryInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(EnrollmentDocumentInline, inline_classes)
        self.assertIn(EnrollmentStatusHistoryInline, inline_classes)

    def test_actions_exist(self):
        action_names = ['approve_registrations', 'reject_registrations', 'mark_under_review']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_approve_registrations_action(self):
        reg = self.create_registration()
        qs = RegistrationForm.objects.filter(pk=reg.pk)
        admin_user = self.create_admin_user()
        request = self.factory.post("/admin/")
        request.user = admin_user
        self.add_middleware(request)
        self.admin.approve_registrations(request, qs)
        reg.refresh_from_db()
        self.assertEqual(reg.status, 'approved')

    def test_reject_registrations_action(self):
        reg = self.create_registration()
        qs = RegistrationForm.objects.filter(pk=reg.pk)
        admin_user = self.create_admin_user()
        request = self.factory.post("/admin/")
        request.user = admin_user
        self.add_middleware(request)
        self.admin.reject_registrations(request, qs)
        reg.refresh_from_db()
        self.assertEqual(reg.status, 'rejected')

    def test_mark_under_review_action(self):
        reg = self.create_registration()
        qs = RegistrationForm.objects.filter(pk=reg.pk)
        admin_user = self.create_admin_user()
        request = self.factory.post("/admin/")
        request.user = admin_user
        self.add_middleware(request)
        self.admin.mark_under_review(request, qs)
        reg.refresh_from_db()
        self.assertEqual(reg.status, 'under_review')

    def test_colored_status(self):
        reg = self.create_registration()
        result = self.admin.colored_status(reg)
        self.assertIn('span', result)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)


class EnrollmentDocumentAdminTest(TestDataMixin, TestCase):
    """Test EnrollmentDocumentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = EnrollmentDocumentAdmin(EnrollmentDocument, self.site)

    def test_list_display(self):
        expected = (
            'document_type', 'registration', 'is_verified',
            'verified_by', 'uploaded_at', 'file_size_display',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('document_type', 'is_verified', 'uploaded_at', 'registration__tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('registration__student_first_name', 'registration__student_last_name', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'uploaded_at')


class EnrollmentStatusHistoryAdminTest(TestDataMixin, TestCase):
    """Test EnrollmentStatusHistoryAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = EnrollmentStatusHistoryAdmin(EnrollmentStatusHistory, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('registration', 'old_status', 'new_status', 'changed_by', 'changed_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('old_status', 'new_status', 'changed_at', 'registration__tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('registration__student_first_name', 'registration__student_last_name', 'notes')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'changed_at')

    def test_has_add_permission_returns_false(self):
        request = self.factory.get("/admin/")
        request.user = self.create_admin_user()
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_delete_permission_returns_false(self):
        request = self.factory.get("/admin/")
        request.user = self.create_admin_user()
        self.assertFalse(self.admin.has_delete_permission(request))
