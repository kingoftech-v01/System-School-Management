"""Tests for library app models."""

from datetime import date, timedelta, datetime
from django.test import TestCase
from django.core.exceptions import ValidationError

from library.models import BookCategory, Publisher, Book, BorrowRecord, validate_isbn
from tests.helpers import TestDataMixin, _next_counter


class ValidateIsbnTest(TestCase):
    def test_valid_isbn_13(self):
        # ISBN-13 for "978-0-306-40615-7"
        validate_isbn('9780306406157')

    def test_invalid_isbn_13_check_digit(self):
        with self.assertRaises(ValidationError):
            validate_isbn('9780306406158')  # Wrong check digit

    def test_isbn_13_with_hyphens(self):
        validate_isbn('978-0-306-40615-7')

    def test_invalid_length(self):
        with self.assertRaises(ValidationError):
            validate_isbn('12345')

    def test_isbn_13_non_digit(self):
        with self.assertRaises(ValidationError):
            validate_isbn('978030640615X')


class BookCategoryModelTest(TestCase):
    def test_create(self):
        cat = BookCategory.objects.create(name='Science')
        self.assertIsNotNone(cat.pk)

    def test_str(self):
        cat = BookCategory.objects.create(name='Fiction')
        self.assertEqual(str(cat), 'Fiction')

    def test_default_is_active(self):
        cat = BookCategory.objects.create(name=f'Cat-{_next_counter()}')
        self.assertTrue(cat.is_active)

    def test_parent_child(self):
        parent = BookCategory.objects.create(name=f'Parent-{_next_counter()}')
        child = BookCategory.objects.create(
            name=f'Child-{_next_counter()}', parent=parent,
        )
        self.assertEqual(child.parent, parent)

    def test_get_book_count_empty(self):
        cat = BookCategory.objects.create(name=f'Empty-{_next_counter()}')
        self.assertEqual(cat.get_book_count(), 0)

    def test_get_book_count_with_books(self):
        cat = BookCategory.objects.create(name=f'Cat-{_next_counter()}')
        tenant = None
        from tests.helpers import TestDataMixin
        mixin = TestDataMixin()
        tenant = mixin.create_school()
        n = _next_counter()
        Book.objects.create(
            tenant=tenant, title=f'Book-{n}', author='Author',
            isbn=f'978030640{n:04d}7', category=cat,
        )
        self.assertEqual(cat.get_book_count(), 1)

    def test_get_book_count_recursive(self):
        parent = BookCategory.objects.create(name=f'Parent-{_next_counter()}')
        child = BookCategory.objects.create(
            name=f'Child-{_next_counter()}', parent=parent,
        )
        mixin = TestDataMixin()
        tenant = mixin.create_school()
        n = _next_counter()
        Book.objects.create(
            tenant=tenant, title=f'Book-{n}', author='Author',
            isbn=f'978030641{n:04d}4', category=child,
        )
        # Parent should count child's books
        self.assertEqual(parent.get_book_count(), 1)


class PublisherModelTest(TestCase):
    def test_create(self):
        pub = Publisher.objects.create(name=f'Publisher-{_next_counter()}')
        self.assertIsNotNone(pub.pk)

    def test_str(self):
        pub = Publisher.objects.create(name='OReilly')
        self.assertEqual(str(pub), 'OReilly')

    def test_unique_name(self):
        Publisher.objects.create(name='DupPub')
        with self.assertRaises(Exception):
            Publisher.objects.create(name='DupPub')


class BookModelTest(TestDataMixin, TestCase):
    def _create_book(self, **overrides):
        tenant = overrides.pop('tenant', None) or self.create_school()
        n = _next_counter()
        defaults = {
            'tenant': tenant,
            'title': f'Book Title {n}',
            'author': 'Test Author',
            'isbn': f'978030642{n:04d}1',
            'quantity': 3,
            'available': 3,
        }
        defaults.update(overrides)
        return Book.objects.create(**defaults)

    def test_create(self):
        book = self._create_book()
        self.assertIsNotNone(book.pk)

    def test_str(self):
        book = self._create_book(title='Python Guide', author='Guido')
        self.assertEqual(str(book), 'Python Guide by Guido')

    def test_is_available_true(self):
        book = self._create_book(available=1)
        self.assertTrue(book.is_available())

    def test_is_available_false(self):
        book = self._create_book(available=0)
        self.assertFalse(book.is_available())

    def test_borrow_success(self):
        book = self._create_book(quantity=3, available=3)
        result = book.borrow()
        self.assertTrue(result)
        book.refresh_from_db()
        self.assertEqual(book.available, 2)

    def test_borrow_none_available(self):
        book = self._create_book(quantity=1, available=0)
        result = book.borrow()
        self.assertFalse(result)
        book.refresh_from_db()
        self.assertEqual(book.available, 0)

    def test_return_book_success(self):
        book = self._create_book(quantity=3, available=2)
        result = book.return_book()
        self.assertTrue(result)
        book.refresh_from_db()
        self.assertEqual(book.available, 3)

    def test_return_book_at_full_quantity(self):
        book = self._create_book(quantity=3, available=3)
        result = book.return_book()
        self.assertFalse(result)

    def test_borrow_then_return(self):
        book = self._create_book(quantity=2, available=2)
        book.borrow()
        book.refresh_from_db()
        self.assertEqual(book.available, 1)
        book.return_book()
        book.refresh_from_db()
        self.assertEqual(book.available, 2)

    def test_default_language(self):
        book = self._create_book()
        self.assertEqual(book.language, 'English')


class BorrowRecordModelTest(TestDataMixin, TestCase):
    def _create_record(self, **overrides):
        n = _next_counter()
        tenant = overrides.pop('tenant', None) or self.create_school()
        book = overrides.pop('book', None)
        if book is None:
            book = Book.objects.create(
                tenant=tenant, title=f'BR Book {n}', author='Author',
                isbn=f'978030643{n:04d}8', quantity=5, available=5,
            )
        student = overrides.pop('student', None) or self.create_user(role='direction')
        defaults = {
            'tenant': tenant,
            'book': book,
            'student': student,
            'due_date': date.today() + timedelta(days=14),
        }
        defaults.update(overrides)
        return BorrowRecord.objects.create(**defaults)

    def test_create(self):
        record = self._create_record()
        self.assertIsNotNone(record.pk)

    def test_str(self):
        record = self._create_record()
        self.assertTrue(len(str(record)) > 0)

    def test_default_status_borrowed(self):
        record = self._create_record()
        self.assertEqual(record.status, 'borrowed')

    def test_is_overdue_future_due(self):
        record = self._create_record(
            due_date=date.today() + timedelta(days=14),
        )
        self.assertFalse(record.is_overdue())

    def test_is_overdue_past_due(self):
        record = self._create_record(
            due_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(record.is_overdue())

    def test_is_overdue_returned(self):
        record = self._create_record(
            due_date=date.today() - timedelta(days=1),
            status='returned',
        )
        self.assertFalse(record.is_overdue())

    def test_default_fine_amount(self):
        record = self._create_record()
        self.assertEqual(record.fine_amount, 0)
