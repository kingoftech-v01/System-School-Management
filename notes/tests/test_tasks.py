"""
Tests for notes app Celery tasks.

Note: The source code has a bug where get_full_name (a @property) is called
as get_full_name() (a method call). We work around this by patching the
User model's get_full_name to be callable in affected tests.
"""

from decimal import Decimal
from unittest.mock import patch, PropertyMock

from django.test import TestCase

from notes.models import ProfessorNote
from notes.tasks import notify_note_status_change
from tests.helpers import TestDataMixin


def _make_get_full_name_callable(user):
    """Patch user so get_full_name works both as property and as method call."""
    class CallableStr(str):
        def __call__(self):
            return str(self)
    original = user.get_full_name
    user.__class__.get_full_name = property(
        lambda self: CallableStr(
            ' '.join(p for p in [self.first_name, self.last_name] if p) or self.username
        )
    )


class TestNotifyNoteStatusChange(TestDataMixin, TestCase):
    """Tests for notify_note_status_change task."""

    def setUp(self):
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.student = self.create_student_user()
        self.filiere = self.create_filiere(tenant=self.school)
        self.course = self.create_course()
        # Patch so get_full_name() works as both property and method call
        _make_get_full_name_callable(self.student)

    def _create_note(self, **kwargs):
        """Helper to create a professor note with Decimal values."""
        return self.create_professor_note(
            tenant=self.school,
            student=self.student,
            professor=self.professor,
            filiere=self.filiere,
            subject=self.course,
            score=Decimal('15.00'),
            coefficient=Decimal('2.00'),
            **kwargs,
        )

    @patch('notes.tasks.send_mail')
    def test_notifies_professor_on_status_change(self, mock_send_mail):
        """Task should send notification email to professor."""
        note = self._create_note()

        notify_note_status_change(note.id, 'approved')

        # At least one call to professor
        self.assertTrue(mock_send_mail.called)

    @patch('notes.tasks.send_mail')
    def test_notifies_student_when_approved(self, mock_send_mail):
        """Task should send notification to student when note is approved."""
        note = self._create_note()

        notify_note_status_change(note.id, 'approved')

        # Should be called twice: once for professor, once for student
        self.assertEqual(mock_send_mail.call_count, 2)

    @patch('notes.tasks.send_mail')
    def test_does_not_notify_student_when_rejected(self, mock_send_mail):
        """Task should not send notification to student when note is rejected."""
        note = self._create_note()

        notify_note_status_change(note.id, 'rejected')

        # Should be called only once (for professor)
        self.assertEqual(mock_send_mail.call_count, 1)

    @patch('notes.tasks.send_mail')
    def test_handles_nonexistent_note(self, mock_send_mail):
        """Task should silently handle non-existent note IDs."""
        # Should not raise an exception
        notify_note_status_change(99999, 'approved')
        mock_send_mail.assert_not_called()

    @patch('notes.tasks.send_mail')
    def test_notifies_professor_on_pending_status(self, mock_send_mail):
        """Task should notify professor when status changes to pending."""
        note = self._create_note()

        notify_note_status_change(note.id, 'pending')

        # Only professor is notified (not student)
        self.assertEqual(mock_send_mail.call_count, 1)
