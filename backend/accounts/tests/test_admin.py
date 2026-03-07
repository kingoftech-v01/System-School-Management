"""Tests for accounts admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from accounts.models import User, Student, Parent, InvitationCode
from accounts.admin import UserAdmin, InvitationCodeAdmin


class AccountsAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all accounts models are registered in the admin."""

    def test_user_registered(self):
        self.assertIn(User, admin.site._registry)

    def test_student_registered(self):
        self.assertIn(Student, admin.site._registry)

    def test_parent_registered(self):
        self.assertIn(Parent, admin.site._registry)

    def test_invitation_code_registered(self):
        self.assertIn(InvitationCode, admin.site._registry)


class UserAdminTest(TestDataMixin, TestCase):
    """Test UserAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = [
            "get_full_name", "username", "email", "is_active",
            "is_student", "is_lecturer", "is_parent", "is_staff",
            "role", "must_change_password",
        ]
        self.assertEqual(self.admin.list_display, expected)

    def test_search_fields(self):
        expected = ["username", "first_name", "last_name", "email"]
        self.assertEqual(self.admin.search_fields, expected)

    def test_list_filter(self):
        expected = [
            "is_active", "is_student", "is_lecturer",
            "is_parent", "role", "must_change_password",
        ]
        self.assertEqual(self.admin.list_filter, expected)


class InvitationCodeAdminTest(TestDataMixin, TestCase):
    """Test InvitationCodeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = InvitationCodeAdmin(InvitationCode, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = [
            "code", "role", "linked_student", "is_active",
            "created_by", "used_by", "expires_at", "created_at",
        ]
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ["role", "is_active"])

    def test_search_fields(self):
        self.assertEqual(self.admin.search_fields, ["code", "sent_to_email"])

    def test_readonly_fields(self):
        expected = ["code", "created_at", "used_at", "used_by"]
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_raw_id_fields(self):
        self.assertEqual(self.admin.raw_id_fields, ["linked_student", "created_by"])

    def test_actions_exist(self):
        action_names = [
            "generate_parent_codes", "generate_staff_codes",
            "generate_prefet_codes", "generate_accountant_codes",
            "generate_secretary_codes", "generate_librarian_codes",
            "generate_registrar_codes", "deactivate_codes",
        ]
        for name in action_names:
            self.assertTrue(
                hasattr(self.admin, name),
                f"Action '{name}' not found on InvitationCodeAdmin",
            )

    def test_generate_parent_codes_action(self):
        admin_user = self.create_admin_user()
        request = self.factory.post("/admin/")
        request.user = admin_user
        self.add_middleware(request)
        self.admin.generate_parent_codes(request, InvitationCode.objects.none())
        self.assertEqual(InvitationCode.objects.filter(role='parent').count(), 5)

    def test_generate_staff_codes_action(self):
        admin_user = self.create_admin_user()
        request = self.factory.post("/admin/")
        request.user = admin_user
        self.add_middleware(request)
        self.admin.generate_staff_codes(request, InvitationCode.objects.none())
        self.assertEqual(InvitationCode.objects.filter(role='professor').count(), 5)

    def test_deactivate_codes_action(self):
        admin_user = self.create_admin_user()
        request = self.factory.post("/admin/")
        request.user = admin_user
        self.add_middleware(request)
        # Create codes first
        self.admin.generate_parent_codes(request, InvitationCode.objects.none())
        qs = InvitationCode.objects.filter(role='parent')
        self.admin.deactivate_codes(request, qs)
        self.assertTrue(all(not c.is_active for c in InvitationCode.objects.filter(role='parent')))
