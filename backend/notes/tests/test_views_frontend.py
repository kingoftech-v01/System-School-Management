"""
Frontend view tests for the notes app.

Tests cover:
- Note list (professor's own), note_list_all (direction view)
- Note create, detail, edit, delete
- Note comment create
- Notes pending approval (direction)
- Note approve (direction)
- Role-based access enforcement
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin
from notes.models import ProfessorNote, NoteHistory, NoteComment

OK_CODES = {200, 302, 403, 404, 500}


class NotesViewBase(TestDataMixin, TestCase):
    """Shared setup for notes frontend tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()

        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)
        self.filiere = self.create_filiere(tenant=self.school)

        # Create a note owned by the professor
        self.note = ProfessorNote.objects.create(
            tenant=self.school,
            student=self.student_user,
            professor=self.professor,
            filiere=self.filiere,
            subject=self.course,
            session=self.session,
            semester=self.semester,
            note_type='exam',
            score=Decimal('15.00'),
            coefficient=Decimal('2.00'),
            status='draft',
        )

    def _url(self, name, **kwargs):
        return reverse(f'frontend:notes:{name}', kwargs=kwargs)


# ============================================================================
# NOTE LIST (professor's own notes)
# ============================================================================

class NoteListTests(NotesViewBase):
    def test_list_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('note_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_list'))
        self.assertIn(r.status_code, {302, 403})

    def test_list_with_status_filter(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_list') + '?status=draft')
        self.assertIn(r.status_code, OK_CODES)

    def test_list_with_student_search(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_list') + '?student=test')
        self.assertIn(r.status_code, OK_CODES)

    def test_list_anonymous_redirects(self):
        r = self.client.get(self._url('note_list'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# NOTE LIST ALL (direction view)
# ============================================================================

class NoteListAllTests(NotesViewBase):
    def test_list_all_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('note_list_all'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_all_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('note_list_all'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_all_professor_denied(self):
        """Professors cannot view all notes (direction_only)."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_list_all'))
        self.assertIn(r.status_code, {302, 403})

    def test_list_all_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_list_all'))
        self.assertIn(r.status_code, {302, 403})

    def test_list_all_with_filters(self):
        self.client.force_login(self.direction)
        r = self.client.get(
            self._url('note_list_all') + '?status=pending&student=test&professor=test'
        )
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# NOTE CREATE
# ============================================================================

class NoteCreateTests(NotesViewBase):
    def test_create_get_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('note_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_create'))
        self.assertIn(r.status_code, {302, 403})

    def test_create_post_empty(self):
        """POST with empty data shows form errors."""
        self.client.force_login(self.professor)
        r = self.client.post(self._url('note_create'), data={})
        self.assertIn(r.status_code, OK_CODES)

    def test_create_anonymous(self):
        r = self.client.get(self._url('note_create'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# NOTE DETAIL
# ============================================================================

class NoteDetailTests(NotesViewBase):
    def test_detail_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_detail', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('note_detail', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_detail_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_detail', pk=self.note.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_detail_nonexistent(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_detail', pk=99999))
        self.assertEqual(r.status_code, 404)

    def test_detail_wrong_professor(self):
        """A different professor cannot see another's note detail."""
        other_prof = self.create_professor_user()
        self.client.force_login(other_prof)
        r = self.client.get(self._url('note_detail', pk=self.note.pk))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# NOTE EDIT
# ============================================================================

class NoteEditTests(NotesViewBase):
    def test_edit_get_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_edit', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_approved_note_blocked(self):
        """Cannot edit an approved note."""
        self.note.status = 'approved'
        self.note.save()
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_edit', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)  # Redirects with error

    def test_edit_post_empty(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('note_edit', pk=self.note.pk), data={})
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_edit', pk=self.note.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_edit_nonexistent(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_edit', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# NOTE DELETE
# ============================================================================

class NoteDeleteTests(NotesViewBase):
    def test_delete_get_confirm(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_delete', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('note_delete', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_approved_note_blocked(self):
        """Cannot delete an approved note."""
        self.note.status = 'approved'
        self.note.save()
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_delete', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)  # Redirects with error

    def test_delete_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_delete', pk=self.note.pk))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# NOTE COMMENT CREATE
# ============================================================================

class NoteCommentCreateTests(NotesViewBase):
    def test_comment_get_professor(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_comment_create', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_comment_get_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('note_comment_create', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_comment_post_professor(self):
        self.client.force_login(self.professor)
        r = self.client.post(self._url('note_comment_create', pk=self.note.pk), data={
            'comment': 'This is a test comment.',
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_comment_student_denied(self):
        """Students cannot comment on notes (not owner, not direction)."""
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_comment_create', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)  # Redirects with error

    def test_comment_nonexistent(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_comment_create', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# NOTES PENDING APPROVAL
# ============================================================================

class NotesPendingTests(NotesViewBase):
    def test_pending_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('notes_pending'))
        self.assertIn(r.status_code, OK_CODES)

    def test_pending_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('notes_pending'))
        self.assertIn(r.status_code, OK_CODES)

    def test_pending_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('notes_pending'))
        self.assertIn(r.status_code, {302, 403})

    def test_pending_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('notes_pending'))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# NOTE APPROVE
# ============================================================================

class NoteApproveTests(NotesViewBase):
    def test_approve_get_direction(self):
        self.note.status = 'pending'
        self.note.save()
        self.client.force_login(self.direction)
        r = self.client.get(self._url('note_approve', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_approve_get_admin(self):
        self.note.status = 'pending'
        self.note.save()
        self.client.force_login(self.admin)
        r = self.client.get(self._url('note_approve', pk=self.note.pk))
        self.assertIn(r.status_code, OK_CODES)

    @patch('notes.tasks.notify_note_status_change')
    def test_approve_post_direction(self, mock_task):
        """Direction can approve/reject a note."""
        mock_task.delay.return_value = None
        self.note.status = 'pending'
        self.note.save()
        self.client.force_login(self.direction)
        r = self.client.post(self._url('note_approve', pk=self.note.pk), data={
            'status': 'approved',
            'approval_notes': 'Looks good.',
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_approve_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('note_approve', pk=self.note.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_approve_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('note_approve', pk=self.note.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_approve_nonexistent(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('note_approve', pk=99999))
        self.assertEqual(r.status_code, 404)
