"""Tests for filieres admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from filieres.models import Filiere, FiliereSubject, FiliereRequirement
from filieres.admin import FiliereAdmin, FiliereSubjectAdmin, FiliereRequirementAdmin


class FilieresAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all filieres models are registered in the admin."""

    def test_filiere_registered(self):
        self.assertIn(Filiere, admin.site._registry)

    def test_filiere_subject_registered(self):
        self.assertIn(FiliereSubject, admin.site._registry)

    def test_filiere_requirement_registered(self):
        self.assertIn(FiliereRequirement, admin.site._registry)


class FiliereAdminTest(TestDataMixin, TestCase):
    """Test FiliereAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = FiliereAdmin(Filiere, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = (
            'code', 'name', 'level', 'duration_years',
            'status_badge', 'enrollment_info', 'coordinator', 'tenant',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_active', 'level', 'duration_years', 'tenant', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('name', 'code', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'updated_at', 'enrollment_info')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_list_per_page(self):
        self.assertEqual(self.admin.list_per_page, 50)

    def test_inlines(self):
        from filieres.admin import FiliereSubjectInline, FiliereRequirementInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(FiliereSubjectInline, inline_classes)
        self.assertIn(FiliereRequirementInline, inline_classes)

    def test_status_badge(self):
        filiere = self.create_filiere()
        result = self.admin.status_badge(filiere)
        self.assertIn('span', result)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)


class FiliereSubjectAdminTest(TestDataMixin, TestCase):
    """Test FiliereSubjectAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = FiliereSubjectAdmin(FiliereSubject, self.site)

    def test_list_display(self):
        expected = (
            'filiere', 'subject', 'year', 'semester', 'coefficient',
            'credits', 'is_mandatory', 'hours_per_week',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_mandatory', 'year', 'semester', 'filiere__tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('filiere__name', 'filiere__code', 'subject__title')
        self.assertEqual(self.admin.search_fields, expected)

    def test_list_editable(self):
        self.assertEqual(self.admin.list_editable, ('coefficient', 'is_mandatory'))


class FiliereRequirementAdminTest(TestDataMixin, TestCase):
    """Test FiliereRequirementAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = FiliereRequirementAdmin(FiliereRequirement, self.site)

    def test_list_display(self):
        expected = ('filiere', 'requirement_type', 'is_mandatory', 'order', 'description_preview')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('requirement_type', 'is_mandatory', 'filiere__tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('filiere__name', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_list_editable(self):
        self.assertEqual(self.admin.list_editable, ('order', 'is_mandatory'))
