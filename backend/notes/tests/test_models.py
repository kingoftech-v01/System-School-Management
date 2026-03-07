"""Tests for notes app models."""

from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from notes.models import ProfessorNote, NoteHistory, NoteComment
from tests.helpers import TestDataMixin


class ProfessorNoteTest(TestDataMixin, TestCase):
    def _create_note(self, **kwargs):
        tenant = kwargs.pop('tenant', None) or self.create_school()
        student = kwargs.pop('student', None) or self.create_user(role='student')
        professor = kwargs.pop('professor', None) or self.create_user(role='professor')
        filiere = kwargs.pop('filiere', None) or self.create_filiere(tenant=tenant)
        subject = kwargs.pop('subject', None) or self.create_course()
        defaults = {
            'tenant': tenant,
            'student': student,
            'professor': professor,
            'filiere': filiere,
            'subject': subject,
            'note_type': 'quiz',
            'score': Decimal('15.00'),
            'max_score': Decimal('20.00'),
            'coefficient': Decimal('2.00'),
        }
        defaults.update(kwargs)
        return ProfessorNote.objects.create(**defaults)

    def test_create(self):
        note = self._create_note()
        self.assertIsNotNone(note.pk)

    def test_defaults(self):
        note = self._create_note()
        self.assertEqual(note.status, 'draft')
        self.assertFalse(note.submitted_for_approval)
        self.assertFalse(note.is_deleted)

    def test_weighted_score_calculated_on_save(self):
        note = self._create_note(score=Decimal('15.00'), max_score=Decimal('20.00'), coefficient=Decimal('2.00'))
        # normalized = (15/20)*100 = 75, weighted = 75 * 2 = 150
        self.assertEqual(note.weighted_score, Decimal('150.00'))

    def test_submit_for_approval(self):
        note = self._create_note()
        result = note.submit_for_approval()
        self.assertTrue(result)
        note.refresh_from_db()
        self.assertEqual(note.status, 'pending')
        self.assertTrue(note.submitted_for_approval)

    def test_submit_for_approval_only_from_draft(self):
        note = self._create_note()
        note.status = 'approved'
        note.save()
        result = note.submit_for_approval()
        self.assertFalse(result)

    def test_approve(self):
        note = self._create_note()
        approver = self.create_user(role='direction')
        note.approve(approver, notes='Looks good')
        note.refresh_from_db()
        self.assertEqual(note.status, 'approved')
        self.assertEqual(note.approved_by, approver)
        self.assertIsNotNone(note.approved_at)
        self.assertEqual(note.approval_notes, 'Looks good')

    def test_reject(self):
        note = self._create_note()
        rejector = self.create_user(role='direction')
        note.reject(rejector, notes='Wrong data')
        note.refresh_from_db()
        self.assertEqual(note.status, 'rejected')

    def test_request_revision(self):
        note = self._create_note()
        reviewer = self.create_user(role='direction')
        note.request_revision(reviewer, notes='Fix score')
        note.refresh_from_db()
        self.assertEqual(note.status, 'revision_requested')

    def test_soft_delete_approved(self):
        note = self._create_note()
        approver = self.create_user(role='direction')
        note.approve(approver)
        note.delete()
        # Should still exist (soft delete)
        self.assertTrue(ProfessorNote.objects.filter(pk=note.pk).exists())
        note.refresh_from_db()
        self.assertTrue(note.is_deleted)

    def test_hard_delete_draft(self):
        note = self._create_note()
        pk = note.pk
        note.delete()
        self.assertFalse(ProfessorNote.objects.filter(pk=pk).exists())

    def test_can_edit_professor_own_draft(self):
        professor = self.create_user(role='professor')
        note = self._create_note(professor=professor)
        self.assertTrue(note.can_edit(professor))

    def test_can_edit_direction_approved(self):
        note = self._create_note()
        approver = self.create_user(role='direction')
        note.approve(approver)
        direction = self.create_user(role='direction')
        self.assertTrue(note.can_edit(direction))

    def test_cannot_edit_professor_approved(self):
        professor = self.create_user(role='professor')
        note = self._create_note(professor=professor)
        approver = self.create_user(role='direction')
        note.approve(approver)
        self.assertFalse(note.can_edit(professor))

    def test_can_delete_draft(self):
        professor = self.create_user(role='professor')
        note = self._create_note(professor=professor)
        self.assertTrue(note.can_delete(professor))

    def test_cannot_delete_approved(self):
        professor = self.create_user(role='professor')
        note = self._create_note(professor=professor)
        approver = self.create_user(role='direction')
        note.approve(approver)
        self.assertFalse(note.can_delete(professor))


class NoteHistoryTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        tenant = self.create_school()
        student = self.create_user(role='student')
        professor = self.create_user(role='professor')
        filiere = self.create_filiere(tenant=tenant)
        subject = self.create_course()
        note = ProfessorNote.objects.create(
            tenant=tenant, student=student, professor=professor,
            filiere=filiere, subject=subject, note_type='quiz',
            score=Decimal('10'), max_score=Decimal('20'), coefficient=Decimal('1'),
        )
        history = NoteHistory.objects.create(
            note=note, action='created', changed_by=professor,
        )
        self.assertIn('Created', str(history))


class NoteCommentTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        tenant = self.create_school()
        student = self.create_user(role='student')
        professor = self.create_user(role='professor')
        filiere = self.create_filiere(tenant=tenant)
        subject = self.create_course()
        note = ProfessorNote.objects.create(
            tenant=tenant, student=student, professor=professor,
            filiere=filiere, subject=subject, note_type='quiz',
            score=Decimal('10'), max_score=Decimal('20'), coefficient=Decimal('1'),
        )
        comment = NoteComment.objects.create(
            note=note, author=professor, comment='Needs revision',
        )
        self.assertIn('Comment on', str(comment))
