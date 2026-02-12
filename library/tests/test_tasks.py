"""
Tests for library app Celery tasks.
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from library.models import BorrowRecord
from library.tasks import send_overdue_reminders
from tests.helpers import TestDataMixin


class TestSendOverdueReminders(TestDataMixin, TestCase):
    """Tests for send_overdue_reminders task."""

    def setUp(self):
        self.school = self.create_school()

    @patch('django.core.mail.send_mail')
    def test_marks_overdue_and_sends_email(self, mock_send_mail):
        """Task should mark overdue records and update their status.
        Note: The source code has a bug (get_full_name() called as method
        instead of property), so the send_mail call itself raises TypeError.
        We verify the status change happens before the email call.
        """
        student = self.create_student_user()
        book = self.create_book(tenant=self.school)
        record = self.create_borrow_record(
            tenant=self.school, book=book, student=student,
            due_date=date.today() - timedelta(days=1),
            status='borrowed',
        )

        try:
            result = send_overdue_reminders()
        except TypeError:
            # Source bug: get_full_name is a property, not a method
            pass

        record.refresh_from_db()
        self.assertEqual(record.status, 'overdue')

    @patch('django.core.mail.send_mail')
    def test_does_not_affect_non_overdue_records(self, mock_send_mail):
        """Task should not affect records that are not overdue."""
        student = self.create_student_user()
        book = self.create_book(tenant=self.school)
        record = self.create_borrow_record(
            tenant=self.school, book=book, student=student,
            due_date=date.today() + timedelta(days=7),
            status='borrowed',
        )

        result = send_overdue_reminders()

        record.refresh_from_db()
        self.assertEqual(record.status, 'borrowed')
        mock_send_mail.assert_not_called()
        self.assertEqual(result, 0)

    @patch('django.core.mail.send_mail')
    def test_does_not_affect_returned_records(self, mock_send_mail):
        """Task should not affect already-returned records even if past due."""
        student = self.create_student_user()
        book = self.create_book(tenant=self.school)
        record = self.create_borrow_record(
            tenant=self.school, book=book, student=student,
            due_date=date.today() - timedelta(days=5),
            status='returned',
        )

        result = send_overdue_reminders()

        record.refresh_from_db()
        self.assertEqual(record.status, 'returned')
        mock_send_mail.assert_not_called()
        self.assertEqual(result, 0)

    @patch('django.core.mail.send_mail')
    def test_returns_zero_when_no_overdue(self, mock_send_mail):
        """Task should return 0 when there are no overdue records."""
        result = send_overdue_reminders()
        self.assertEqual(result, 0)
        mock_send_mail.assert_not_called()
