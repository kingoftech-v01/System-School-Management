"""
Tests for notes signal handlers.

Signals tested:
1. track_note_changes (pre_save on ProfessorNote) - creates NoteHistory when
   score or status changes on an existing note
2. log_note_creation (post_save on ProfessorNote) - logs when a new note is created
"""

import logging
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase

from notes.models import ProfessorNote, NoteHistory
from tests.helpers import TestDataMixin


class TrackNoteChangesSignalTest(TestDataMixin, TestCase):
    """Tests for the track_note_changes pre_save signal."""

    def test_score_change_creates_history(self):
        """Changing the score on an existing note creates a NoteHistory entry."""
        note = self.create_professor_note(score=Decimal('15.00'))
        self.assertEqual(NoteHistory.objects.count(), 0)

        note.score = Decimal('18.00')
        note.save()

        self.assertEqual(NoteHistory.objects.count(), 1)
        history = NoteHistory.objects.first()
        self.assertEqual(history.note, note)
        self.assertEqual(history.action, 'updated')

    def test_status_change_creates_history(self):
        """Changing the status on an existing note creates a NoteHistory entry."""
        note = self.create_professor_note(status='draft')
        self.assertEqual(NoteHistory.objects.count(), 0)

        note.status = 'pending'
        note.save()

        self.assertEqual(NoteHistory.objects.count(), 1)
        history = NoteHistory.objects.first()
        self.assertEqual(history.action, 'updated')

    def test_both_score_and_status_change_creates_one_history(self):
        """Changing both score and status creates exactly one NoteHistory entry."""
        note = self.create_professor_note(score=Decimal('10.00'), status='draft')
        self.assertEqual(NoteHistory.objects.count(), 0)

        note.score = Decimal('12.00')
        note.status = 'pending'
        note.save()

        self.assertEqual(NoteHistory.objects.count(), 1)

    def test_no_change_skips_history(self):
        """Re-saving without changing score or status creates no NoteHistory."""
        note = self.create_professor_note(score=Decimal('15.00'), status='draft')
        self.assertEqual(NoteHistory.objects.count(), 0)

        # Save again without changes to score or status
        note.comment = 'Just updating a comment'
        note.save()

        self.assertEqual(NoteHistory.objects.count(), 0)

    def test_history_old_values_recorded(self):
        """NoteHistory stores the old score and status."""
        note = self.create_professor_note(score=Decimal('14.00'), status='draft')

        note.score = Decimal('16.00')
        note.save()

        history = NoteHistory.objects.first()
        self.assertEqual(history.old_values['score'], '14.00')
        self.assertEqual(history.old_values['status'], 'draft')

    def test_history_new_values_recorded(self):
        """NoteHistory stores the new score and status."""
        note = self.create_professor_note(score=Decimal('14.00'), status='draft')

        note.score = Decimal('16.00')
        note.status = 'approved'
        note.save()

        history = NoteHistory.objects.first()
        self.assertEqual(history.new_values['score'], '16.00')
        self.assertEqual(history.new_values['status'], 'approved')

    def test_history_change_summary_includes_scores(self):
        """NoteHistory change_summary mentions old and new scores."""
        note = self.create_professor_note(score=Decimal('12.00'))

        note.score = Decimal('17.50')
        note.save()

        history = NoteHistory.objects.first()
        self.assertIn('12.00', history.change_summary)
        self.assertIn('17.50', history.change_summary)

    def test_changed_by_attribute_recorded(self):
        """If _changed_by is set on the instance, it appears in history."""
        note = self.create_professor_note(score=Decimal('10.00'))
        admin_user = self.create_admin_user()

        note._changed_by = admin_user
        note.score = Decimal('11.00')
        note.save()

        history = NoteHistory.objects.first()
        self.assertEqual(history.changed_by, admin_user)

    def test_changed_by_none_when_not_set(self):
        """If _changed_by is not set, changed_by is None."""
        note = self.create_professor_note(score=Decimal('10.00'))

        note.score = Decimal('11.00')
        note.save()

        history = NoteHistory.objects.first()
        self.assertIsNone(history.changed_by)

    def test_new_note_creation_no_history(self):
        """Creating a new note does NOT produce a NoteHistory entry
        from the track_note_changes signal (only updates do)."""
        self.create_professor_note(score=Decimal('15.00'))
        self.assertEqual(NoteHistory.objects.count(), 0)


class LogNoteCreationSignalTest(TestDataMixin, TestCase):
    """Tests for the log_note_creation post_save signal."""

    def test_new_note_logs_info(self):
        """Creating a new ProfessorNote logs an INFO message."""
        with self.assertLogs('notes.signals', level='INFO') as cm:
            self.create_professor_note()

        log_output = '\n'.join(cm.output)
        self.assertIn('New note created', log_output)

    def test_log_includes_professor_username(self):
        """Log message includes the professor's username."""
        professor = self.create_professor_user()
        # Refresh from DB since post_save signal may auto-generate username
        professor.refresh_from_db()

        with self.assertLogs('notes.signals', level='INFO') as cm:
            self.create_professor_note(professor=professor)

        log_output = '\n'.join(cm.output)
        self.assertIn(professor.username, log_output)

    def test_log_includes_student_username(self):
        """Log message includes the student's username."""
        student = self.create_student_user()
        # Refresh from DB since post_save signal may auto-generate username
        student.refresh_from_db()

        with self.assertLogs('notes.signals', level='INFO') as cm:
            self.create_professor_note(student=student)

        log_output = '\n'.join(cm.output)
        self.assertIn(student.username, log_output)

    def test_update_note_does_not_log_creation(self):
        """Updating an existing note does NOT log 'New note created'."""
        note = self.create_professor_note()

        logger = logging.getLogger('notes.signals')
        with patch.object(logger, 'info') as mock_info:
            note.comment = 'Updated comment'
            note.save()

            for call in mock_info.call_args_list:
                self.assertNotIn('New note created', str(call))

    def test_multiple_creations_log_each(self):
        """Each new note creation produces its own log entry."""
        with self.assertLogs('notes.signals', level='INFO') as cm:
            self.create_professor_note()
            self.create_professor_note()

        creation_logs = [msg for msg in cm.output if 'New note created' in msg]
        self.assertEqual(len(creation_logs), 2)
