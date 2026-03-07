"""Tests for library app serializers."""

from datetime import date, timedelta
from django.test import TestCase

from tests.helpers import TestDataMixin
from library.serializers import BookSerializer, BorrowRecordSerializer
from library.models import Book, BorrowRecord


class BookSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        tenant = self.create_school()
        book = self.create_book(tenant=tenant)
        serializer = BookSerializer(book)
        self.assertIn('title', serializer.data)
        self.assertIn('author', serializer.data)
        self.assertIn('isbn', serializer.data)

    def test_all_fields(self):
        tenant = self.create_school()
        book = self.create_book(tenant=tenant)
        serializer = BookSerializer(book)
        self.assertIn('id', serializer.data)
        self.assertIn('tenant', serializer.data)


class BorrowRecordSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        tenant = self.create_school()
        book = self.create_book(tenant=tenant)
        borrow = self.create_borrow_record(tenant=tenant, book=book)
        serializer = BorrowRecordSerializer(borrow)
        self.assertIn('book', serializer.data)
        self.assertIn('student', serializer.data)
        self.assertIn('due_date', serializer.data)
        self.assertIn('status', serializer.data)

    def test_default_status(self):
        tenant = self.create_school()
        book = self.create_book(tenant=tenant)
        borrow = self.create_borrow_record(tenant=tenant, book=book)
        serializer = BorrowRecordSerializer(borrow)
        self.assertEqual(serializer.data['status'], 'borrowed')
