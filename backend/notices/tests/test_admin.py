"""Tests for notices admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from notices.models import Notice, NoticeDocument, NotifyGroup, NoticeResponse
from notices.admin import (
    NoticeAdmin, NoticeDocumentAdmin, NotifyGroupAdmin, NoticeResponseAdmin,
)


class NoticesAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all notices models are registered in the admin."""

    def test_notice_registered(self):
        self.assertIn(Notice, admin.site._registry)

    def test_notice_document_registered(self):
        self.assertIn(NoticeDocument, admin.site._registry)

    def test_notify_group_registered(self):
        self.assertIn(NotifyGroup, admin.site._registry)

    def test_notice_response_registered(self):
        self.assertIn(NoticeResponse, admin.site._registry)


class NoticeAdminTest(TestDataMixin, TestCase):
    """Test NoticeAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NoticeAdmin(Notice, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('title', 'uploaded_by', 'priority', 'is_active', 'expires_at', 'created_at', 'get_read_count')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('priority', 'is_active', 'created_at', 'expires_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('title', 'content', 'uploaded_by__username')
        self.assertEqual(self.admin.search_fields, expected)

    def test_date_hierarchy(self):
        self.assertEqual(self.admin.date_hierarchy, 'created_at')

    def test_inlines(self):
        from notices.admin import NoticeDocumentInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(NoticeDocumentInline, inline_classes)

    def test_actions_exist(self):
        action_names = ['activate_notices', 'deactivate_notices', 'mark_as_urgent']
        for name in action_names:
            self.assertTrue(hasattr(self.admin, name))

    def test_activate_notices_action(self):
        notice = self.create_notice()
        Notice.objects.filter(pk=notice.pk).update(is_active=False)
        qs = Notice.objects.filter(pk=notice.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.activate_notices(request, qs)
        notice.refresh_from_db()
        self.assertTrue(notice.is_active)

    def test_deactivate_notices_action(self):
        notice = self.create_notice()
        qs = Notice.objects.filter(pk=notice.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.deactivate_notices(request, qs)
        notice.refresh_from_db()
        self.assertFalse(notice.is_active)

    def test_mark_as_urgent_action(self):
        notice = self.create_notice()
        qs = Notice.objects.filter(pk=notice.pk)
        request = self.factory.post("/admin/")
        request.user = self.create_admin_user()
        self.admin.mark_as_urgent(request, qs)
        notice.refresh_from_db()
        self.assertEqual(notice.priority, 'urgent')

    def test_get_read_count(self):
        notice = self.create_notice()
        count = self.admin.get_read_count(notice)
        self.assertEqual(count, 0)

    def test_get_unread_count(self):
        notice = self.create_notice()
        count = self.admin.get_unread_count(notice)
        self.assertEqual(count, 0)


class NoticeDocumentAdminTest(TestDataMixin, TestCase):
    """Test NoticeDocumentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NoticeDocumentAdmin(NoticeDocument, self.site)

    def test_list_display(self):
        expected = ('filename', 'notice', 'file_size', 'uploaded_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('uploaded_at',))

    def test_search_fields(self):
        expected = ('filename', 'notice__title')
        self.assertEqual(self.admin.search_fields, expected)


class NotifyGroupAdminTest(TestDataMixin, TestCase):
    """Test NotifyGroupAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NotifyGroupAdmin(NotifyGroup, self.site)

    def test_list_display(self):
        expected = ('name', 'description', 'get_member_count', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_search_fields(self):
        expected = ('name', 'description')
        self.assertEqual(self.admin.search_fields, expected)


class NoticeResponseAdminTest(TestDataMixin, TestCase):
    """Test NoticeResponseAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NoticeResponseAdmin(NoticeResponse, self.site)

    def test_list_display(self):
        expected = ('notice', 'user', 'acknowledged', 'acknowledged_at', 'read_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('acknowledged', 'read_at', 'acknowledged_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('notice__title', 'user__username')
        self.assertEqual(self.admin.search_fields, expected)

    def test_actions_exist(self):
        self.assertTrue(hasattr(self.admin, 'mark_as_acknowledged'))
