"""Tests for library app API views."""

from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from library.models import Book, BorrowRecord


class BookViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.tenant = self.create_school()
        self.book = self.create_book(tenant=self.tenant)

    def test_list_books(self):
        resp = self.client.get('/api/v1/library/books/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_book(self):
        resp = self.client.get(f'/api/v1/library/books/{self.book.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], self.book.title)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/library/books/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class BorrowRecordViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.tenant = self.create_school()
        self.book = self.create_book(tenant=self.tenant)
        self.borrow = self.create_borrow_record(tenant=self.tenant, book=self.book)

    def test_list_borrow_records(self):
        resp = self.client.get('/api/v1/library/borrow-records/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_borrow_record(self):
        resp = self.client.get(f'/api/v1/library/borrow-records/{self.borrow.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/library/borrow-records/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
