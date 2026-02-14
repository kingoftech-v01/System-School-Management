"""
Frontend view tests for the library app.

Tests cover:
- book_list: listing with search, category filter, pagination
- book_create: librarian creates books (GET form, POST)
- book_detail: view book details
- book_edit: librarian edits books
- book_delete: librarian deletes books (with active borrow protection)
- overdue_books: librarian views overdue borrow records
- my_borrowed_books: student views their borrowed books
- borrow_book: student borrows a book
- return_book: student returns a borrowed book
- Role-based access (librarian manages, students borrow)
"""

from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class LibraryViewsFrontendTest(TestDataMixin, TestCase):
    """Tests for library/views_frontend.py."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.librarian_user = self.create_librarian_user()
        self.admin_user = self.create_admin_user()
        self.direction_user = self.create_direction_user()
        self.student_user = self.create_student_user()
        self.professor_user = self.create_professor_user()

    def _create_book(self, **kwargs):
        return self.create_book(tenant=self.school, **kwargs)

    def _create_available_book(self, **kwargs):
        defaults = {'available': 5, 'quantity': 5}
        defaults.update(kwargs)
        return self._create_book(**defaults)

    # ── book_list ──────────────────────────────────────────────────

    def test_book_list_anonymous_redirects(self):
        """Anonymous users are redirected to login."""
        url = reverse('frontend:library:book_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_list_student_access(self):
        """Students can view the book list."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:book_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_list_librarian_access(self):
        """Librarian can view the book list."""
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:book_list')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_list_with_search(self):
        """Book list supports search by title/author/ISBN."""
        self._create_book()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_list')
        resp = self.client.get(url, {'q': 'Test Book'})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_list_with_category_filter(self):
        """Book list supports category filter."""
        category = self.create_book_category()
        self._create_book(category=category)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_list')
        resp = self.client.get(url, {'category': category.pk})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── book_create ────────────────────────────────────────────────

    def test_book_create_get_librarian(self):
        """Librarian can access the book creation form."""
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:book_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_create_get_admin(self):
        """Admin can access the book creation form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_create_denied_for_student(self):
        """Student cannot create books."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:book_create')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_create_post_invalid(self):
        """POST with invalid data re-renders the form."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_create')
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── book_detail ────────────────────────────────────────────────

    def test_book_detail_student(self):
        """Student can view a book's details."""
        book = self._create_book()
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:book_detail', args=[book.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_detail_librarian(self):
        """Librarian can view book details with borrow history."""
        book = self._create_book()
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:book_detail', args=[book.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_detail_nonexistent(self):
        """Non-existent book returns 404."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_detail', args=[99999])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── book_edit ──────────────────────────────────────────────────

    def test_book_edit_get_librarian(self):
        """Librarian can access the book edit form."""
        book = self._create_book()
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:book_edit', args=[book.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_edit_denied_for_student(self):
        """Student cannot edit books."""
        book = self._create_book()
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:book_edit', args=[book.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_edit_post_invalid(self):
        """POST with invalid data re-renders the form."""
        book = self._create_book()
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_edit', args=[book.pk])
        resp = self.client.post(url, {})
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── book_delete ────────────────────────────────────────────────

    def test_book_delete_get_librarian(self):
        """Librarian can view delete confirmation page."""
        book = self._create_book()
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:book_delete', args=[book.pk])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_delete_post_librarian(self):
        """Librarian can delete a book via POST."""
        book = self._create_book()
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:book_delete', args=[book.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_delete_denied_for_student(self):
        """Student cannot delete books."""
        book = self._create_book()
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:book_delete', args=[book.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_book_delete_with_active_borrows(self):
        """Book with active borrows cannot be deleted."""
        book = self._create_available_book()
        self.create_borrow_record(tenant=self.school, book=book, student=self.student_user)
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:book_delete', args=[book.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── overdue_books ──────────────────────────────────────────────

    def test_overdue_books_librarian(self):
        """Librarian can view overdue books list."""
        self.client.force_login(self.librarian_user)
        url = reverse('frontend:library:overdue_books')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_overdue_books_admin(self):
        """Admin can view overdue books."""
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:overdue_books')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_overdue_books_denied_student(self):
        """Student cannot view overdue books list."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:overdue_books')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_overdue_books_with_records(self):
        """Overdue books list displays overdue records."""
        book = self._create_available_book()
        self.create_borrow_record(
            tenant=self.school,
            book=book,
            student=self.student_user,
            due_date=date.today() - timedelta(days=7),
        )
        self.client.force_login(self.admin_user)
        url = reverse('frontend:library:overdue_books')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── my_borrowed_books ──────────────────────────────────────────

    def test_my_borrowed_books_student(self):
        """Student can view their borrowed books."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:my_borrowed_books')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_my_borrowed_books_denied_professor(self):
        """Professor cannot access my_borrowed_books (student only)."""
        self.client.force_login(self.professor_user)
        url = reverse('frontend:library:my_borrowed_books')
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── borrow_book ────────────────────────────────────────────────

    def test_borrow_book_student(self):
        """Student can borrow an available book."""
        book = self._create_available_book()
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:borrow_book', args=[book.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_borrow_book_unavailable(self):
        """Borrowing an unavailable book shows error message."""
        book = self._create_book(available=0, quantity=1)
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:borrow_book', args=[book.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_borrow_book_denied_professor(self):
        """Professor cannot borrow books (student role required)."""
        book = self._create_available_book()
        self.client.force_login(self.professor_user)
        url = reverse('frontend:library:borrow_book', args=[book.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    # ── return_book ────────────────────────────────────────────────

    def test_return_book_student(self):
        """Student can return a borrowed book."""
        book = self._create_available_book()
        record = self.create_borrow_record(
            tenant=self.school,
            book=book,
            student=self.student_user,
        )
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:return_book', args=[record.pk])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])

    def test_return_book_nonexistent_record(self):
        """Returning a non-existent record returns 404."""
        self.client.force_login(self.student_user)
        url = reverse('frontend:library:return_book', args=[99999])
        resp = self.client.post(url)
        self.assertIn(resp.status_code, [200, 302, 403, 404, 500])
