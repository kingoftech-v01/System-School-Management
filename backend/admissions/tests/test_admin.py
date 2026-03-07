"""Tests for admissions admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from admissions.models import (
    AdmissionSession, AdmissionStudent, CounselingComment, AdmissionPayment,
)
from admissions.admin import (
    AdmissionSessionAdmin, AdmissionStudentAdmin,
    CounselingCommentAdmin, AdmissionPaymentAdmin,
)


class AdmissionsAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all admissions models are registered in the admin."""

    def test_admission_session_registered(self):
        self.assertIn(AdmissionSession, admin.site._registry)

    def test_admission_student_registered(self):
        self.assertIn(AdmissionStudent, admin.site._registry)

    def test_counseling_comment_registered(self):
        self.assertIn(CounselingComment, admin.site._registry)

    def test_admission_payment_registered(self):
        self.assertIn(AdmissionPayment, admin.site._registry)


class AdmissionSessionAdminTest(TestDataMixin, TestCase):
    """Test AdmissionSessionAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AdmissionSessionAdmin(AdmissionSession, self.site)

    def test_list_display(self):
        expected = ('name', 'start_date', 'end_date', 'is_active', 'get_application_count')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('is_active', 'start_date'))

    def test_search_fields(self):
        self.assertEqual(self.admin.search_fields, ('name',))

    def test_readonly_fields(self):
        self.assertEqual(self.admin.readonly_fields, ('created_at',))

    def test_get_application_count(self):
        session = self.create_admission_session()
        self.create_admission_student(session=session)
        count = self.admin.get_application_count(session)
        self.assertEqual(count, 1)


class AdmissionStudentAdminTest(TestDataMixin, TestCase):
    """Test AdmissionStudentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AdmissionStudentAdmin(AdmissionStudent, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('get_full_name', 'email', 'program', 'status', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'session', 'program', 'gender')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('first_name', 'last_name', 'email', 'phone')
        self.assertEqual(self.admin.search_fields, expected)

    def test_inlines(self):
        from admissions.admin import CounselingCommentInline, AdmissionPaymentInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(CounselingCommentInline, inline_classes)
        self.assertIn(AdmissionPaymentInline, inline_classes)

    def test_actions_exist(self):
        action_names = ['approve_applications', 'reject_applications', 'move_to_counseling']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_approve_applications_action(self):
        student = self.create_admission_student()
        qs = AdmissionStudent.objects.filter(pk=student.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.approve_applications(request, qs)
        student.refresh_from_db()
        self.assertEqual(student.status, 'admitted')

    def test_reject_applications_action(self):
        student = self.create_admission_student()
        qs = AdmissionStudent.objects.filter(pk=student.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.reject_applications(request, qs)
        student.refresh_from_db()
        self.assertEqual(student.status, 'rejected')

    def test_get_full_name(self):
        student = self.create_admission_student()
        name = self.admin.get_full_name(student)
        self.assertIn(student.first_name, name)
        self.assertIn(student.last_name, name)


class AdmissionPaymentAdminTest(TestDataMixin, TestCase):
    """Test AdmissionPaymentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = AdmissionPaymentAdmin(AdmissionPayment, self.site)

    def test_list_display(self):
        expected = ('application', 'amount', 'payment_method', 'verified', 'verified_by', 'paid_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('verified', 'payment_method', 'paid_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('application__first_name', 'application__last_name', 'transaction_id')
        self.assertEqual(self.admin.search_fields, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'verify_payments'))


class CounselingCommentAdminTest(TestDataMixin, TestCase):
    """Test CounselingCommentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = CounselingCommentAdmin(CounselingComment, self.site)

    def test_list_display(self):
        expected = ('application', 'counselor', 'is_recommendation', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('created_at', 'counselor', 'is_recommendation')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('application__first_name', 'application__last_name', 'comment')
        self.assertEqual(self.admin.search_fields, expected)
