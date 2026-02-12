"""Tests for discipline admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from discipline.models import DisciplinaryAction
from discipline.admin import DisciplinaryActionAdmin


class DisciplineAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that discipline models are registered in the admin."""

    def test_disciplinary_action_registered(self):
        self.assertIn(DisciplinaryAction, admin.site._registry)


class DisciplinaryActionAdminTest(TestDataMixin, TestCase):
    """Test DisciplinaryActionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = DisciplinaryActionAdmin(DisciplinaryAction, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('student', 'incident_type', 'severity', 'incident_date', 'is_resolved', 'tenant')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('severity', 'is_resolved', 'incident_date', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('student__username', 'student__first_name', 'student__last_name', 'incident_type', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'updated_at', 'reported_by', 'updated_by')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_fieldsets_exist(self):
        self.assertIsNotNone(self.admin.fieldsets)
        fieldset_names = [f[0] for f in self.admin.fieldsets]
        self.assertIn('Basic Information', fieldset_names)
        self.assertIn('Details', fieldset_names)
        self.assertIn('Audit Trail', fieldset_names)

    def test_save_model_sets_reported_by_on_create(self):
        admin_user = self.create_admin_user()
        school = self.create_school()
        student = self.create_student_user()
        request = self.factory.post("/admin/")
        request.user = admin_user

        action = DisciplinaryAction(
            tenant=school,
            student=student,
            incident_type='misconduct',
            description='Test',
            action_taken='Warning',
            severity='minor',
            incident_date='2025-01-01',
        )

        class FakeForm:
            changed_data = []

        self.admin.save_model(request, action, FakeForm(), change=False)
        self.assertEqual(action.reported_by, admin_user)

    def test_save_model_sets_updated_by_on_change(self):
        admin_user = self.create_admin_user()
        action = self.create_disciplinary_action()
        request = self.factory.post("/admin/")
        request.user = admin_user

        class FakeForm:
            changed_data = []

        self.admin.save_model(request, action, FakeForm(), change=True)
        self.assertEqual(action.updated_by, admin_user)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)
