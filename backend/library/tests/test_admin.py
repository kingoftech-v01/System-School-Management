"""Tests for library admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from library.models import Book, BorrowRecord
from library.admin import BookAdmin, BorrowRecordAdmin


class LibraryAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all library models are registered in the admin."""

    def test_book_registered(self):
        self.assertIn(Book, admin.site._registry)

    def test_borrow_record_registered(self):
        self.assertIn(BorrowRecord, admin.site._registry)


class BookAdminTest(TestDataMixin, TestCase):
    """Test BookAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = BookAdmin(Book, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('title', 'author', 'isbn', 'quantity', 'available', 'tenant')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('filiere', 'category', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('title', 'author', 'isbn')
        self.assertEqual(self.admin.search_fields, expected)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)


class BorrowRecordAdminTest(TestDataMixin, TestCase):
    """Test BorrowRecordAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = BorrowRecordAdmin(BorrowRecord, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('book', 'student', 'borrowed_at', 'due_date', 'status', 'tenant')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'tenant')
        self.assertEqual(self.admin.list_filter, expected)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)
