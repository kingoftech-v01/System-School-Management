"""Tests for certificates admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from certificates.models import (
    CertificateTemplate, Certificate, CertificateVerification, BatchCertificateGeneration,
)
from certificates.admin import (
    CertificateTemplateAdmin, CertificateAdmin,
    CertificateVerificationAdmin, BatchCertificateGenerationAdmin,
)


class CertificatesAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all certificates models are registered in the admin."""

    def test_certificate_template_registered(self):
        self.assertIn(CertificateTemplate, admin.site._registry)

    def test_certificate_registered(self):
        self.assertIn(Certificate, admin.site._registry)

    def test_certificate_verification_registered(self):
        self.assertIn(CertificateVerification, admin.site._registry)

    def test_batch_certificate_generation_registered(self):
        self.assertIn(BatchCertificateGeneration, admin.site._registry)


class CertificateTemplateAdminTest(TestDataMixin, TestCase):
    """Test CertificateTemplateAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CertificateTemplateAdmin(CertificateTemplate, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('name', 'orientation', 'page_size', 'is_active', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_active', 'orientation', 'page_size', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('name', 'description')
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'updated_at')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'activate_templates'))
        self.assertTrue(hasattr(self.admin, 'deactivate_templates'))

    def test_activate_templates_action(self):
        template = self.create_certificate_template()
        CertificateTemplate.objects.filter(pk=template.pk).update(is_active=False)
        qs = CertificateTemplate.objects.filter(pk=template.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.activate_templates(request, qs)
        template.refresh_from_db()
        self.assertTrue(template.is_active)


class CertificateAdminTest(TestDataMixin, TestCase):
    """Test CertificateAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CertificateAdmin(Certificate, self.site)

    def test_list_display(self):
        expected = (
            'certificate_number', 'student', 'course', 'template', 'issue_date',
            'is_revoked', 'get_verification_status', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('is_revoked', 'issue_date', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = (
            'certificate_number', 'student__student__first_name', 'student__student__last_name',
            'course__name', 'hash_signature', 'blockchain_hash',
        )
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'issue_date')

    def test_actions_exist(self):
        action_names = ['revoke_certificates', 'unrevoke_certificates', 'regenerate_hash']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))


class CertificateVerificationAdminTest(TestDataMixin, TestCase):
    """Test CertificateVerificationAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CertificateVerificationAdmin(CertificateVerification, self.site)

    def test_list_display(self):
        expected = ('certificate', 'get_verified_by', 'verification_method', 'is_valid', 'verified_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('verification_method', 'is_valid', 'verified_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('certificate__certificate_number', 'verified_by_email', 'ip_address', 'notes')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'verified_at')


class BatchCertificateGenerationAdminTest(TestDataMixin, TestCase):
    """Test BatchCertificateGenerationAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = BatchCertificateGenerationAdmin(BatchCertificateGeneration, self.site)

    def test_list_display(self):
        expected = (
            'course', 'template', 'status', 'get_progress', 'success_count', 'get_failed_count',
            'get_created_by', 'created_at',
        )
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'created_at', 'completed_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('course__name', 'created_by__username', 'error_log')
        self.assertEqual(self.admin.search_fields, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'mark_pending'))
        self.assertTrue(hasattr(self.admin, 'mark_completed'))

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')
