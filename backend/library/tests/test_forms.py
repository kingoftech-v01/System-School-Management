"""Tests for library app forms."""

from datetime import date, timedelta
from django.test import TestCase

from tests.helpers import TestDataMixin
from library.forms import BookForm, BorrowForm


class BookFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'title': 'Introduction to Algorithms',
            'isbn': '9780262033848',
            'author': 'Cormen et al.',
            'quantity': 5,
            'available': 3,
        }
        form = BookForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_title(self):
        data = {
            'isbn': '9780262033848',
            'author': 'Author',
        }
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_missing_author(self):
        data = {
            'title': 'Some Book',
            'isbn': '9780262033848',
        }
        form = BookForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('author', form.errors)

    def test_meta_fields(self):
        form = BookForm()
        expected = ['title', 'isbn', 'author', 'publisher', 'category', 'quantity', 'available']
        for field_name in expected:
            self.assertIn(field_name, form.fields)


class BorrowFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.book = self.create_book(tenant=self.tenant)
        self.student = self.create_student_user()

    def test_valid_form(self):
        data = {
            'book': self.book.pk,
            'student': self.student.pk,
            'due_date': (date.today() + timedelta(days=14)).isoformat(),
        }
        form = BorrowForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_due_date(self):
        data = {
            'book': self.book.pk,
            'student': self.student.pk,
        }
        form = BorrowForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)
