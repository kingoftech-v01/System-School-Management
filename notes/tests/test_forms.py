"""Tests for notes app forms."""

from django.test import TestCase

from tests.helpers import TestDataMixin
from notes.forms import ProfessorNoteForm, NoteApprovalForm, NoteCommentForm


class ProfessorNoteFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.student = self.create_student_user()
        self.course = self.create_course()

    def test_valid_form(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'note_type': 'final',
            'score': '15.00',
            'max_score': '100.00',
            'coefficient': '2.00',
        }
        form = ProfessorNoteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = ProfessorNoteForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('student', form.errors)
        self.assertIn('subject', form.errors)
        self.assertIn('note_type', form.errors)
        self.assertIn('score', form.errors)

    def test_with_optional_comment(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'note_type': 'quiz',
            'score': '18.50',
            'max_score': '100.00',
            'coefficient': '1.00',
            'comment': 'Excellent work!',
            'private_note': 'Needs more practice in certain areas.',
        }
        form = ProfessorNoteForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_meta_fields(self):
        form = ProfessorNoteForm()
        expected = ['student', 'subject', 'note_type', 'score', 'max_score', 'coefficient', 'comment', 'private_note']
        for field_name in expected:
            self.assertIn(field_name, form.fields)


class NoteApprovalFormTest(TestDataMixin, TestCase):
    def test_valid_approval(self):
        data = {
            'status': 'approved',
            'approval_notes': 'Looks good.',
        }
        form = NoteApprovalForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_rejection(self):
        data = {
            'status': 'rejected',
            'approval_notes': 'Score seems incorrect.',
        }
        form = NoteApprovalForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_meta_fields(self):
        form = NoteApprovalForm()
        self.assertIn('status', form.fields)
        self.assertIn('approval_notes', form.fields)


class NoteCommentFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {'comment': 'Please review this score.'}
        form = NoteCommentForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_comment_invalid(self):
        form = NoteCommentForm(data={'comment': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)
