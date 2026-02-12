"""Tests for notes app serializers."""

from django.test import TestCase

from tests.helpers import TestDataMixin
from notes.serializers import (
    ProfessorNoteSerializer,
    ProfessorNoteListSerializer,
    ProfessorNoteCreateSerializer,
    NoteApprovalSerializer,
    NoteHistorySerializer,
)
from notes.models import ProfessorNote, NoteHistory


class ProfessorNoteSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.note = self.create_professor_note()

    def test_serializes(self):
        serializer = ProfessorNoteSerializer(self.note)
        self.assertIn('id', serializer.data)
        self.assertIn('professor_name', serializer.data)
        self.assertIn('student_name', serializer.data)
        self.assertIn('subject_name', serializer.data)
        self.assertIn('status_display', serializer.data)
        self.assertIn('note_type_display', serializer.data)

    def test_read_only_fields(self):
        serializer = ProfessorNoteSerializer(self.note)
        self.assertIn('created_at', serializer.data)
        self.assertIn('updated_at', serializer.data)

    def test_score_value(self):
        serializer = ProfessorNoteSerializer(self.note)
        self.assertEqual(float(serializer.data['score']), 15.0)

    def test_coefficient_value(self):
        serializer = ProfessorNoteSerializer(self.note)
        self.assertEqual(float(serializer.data['coefficient']), 2.0)


class ProfessorNoteListSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        note = self.create_professor_note()
        serializer = ProfessorNoteListSerializer(note)
        self.assertIn('student_name', serializer.data)
        self.assertIn('subject_name', serializer.data)
        self.assertIn('score', serializer.data)
        self.assertIn('status_display', serializer.data)

    def test_lightweight_fields(self):
        note = self.create_professor_note()
        serializer = ProfessorNoteListSerializer(note)
        # Should not include full detail fields
        self.assertNotIn('professor_name', serializer.data)
        self.assertNotIn('comment', serializer.data)


class ProfessorNoteCreateSerializerTest(TestDataMixin, TestCase):
    def setUp(self):
        self.student = self.create_student_user()
        self.course = self.create_course()

    def test_valid_data(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'score': '15.00',
            'coefficient': '2.00',
            'note_type': 'final',
        }
        serializer = ProfessorNoteCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_score_below_zero_invalid(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'score': '-1',
            'coefficient': '2.00',
            'note_type': 'final',
        }
        serializer = ProfessorNoteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('score', serializer.errors)

    def test_score_above_20_invalid(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'score': '25',
            'coefficient': '2.00',
            'note_type': 'final',
        }
        serializer = ProfessorNoteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('score', serializer.errors)

    def test_coefficient_zero_invalid(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'score': '15',
            'coefficient': '0',
            'note_type': 'final',
        }
        serializer = ProfessorNoteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coefficient', serializer.errors)

    def test_negative_coefficient_invalid(self):
        data = {
            'student': self.student.pk,
            'subject': self.course.pk,
            'score': '15',
            'coefficient': '-1',
            'note_type': 'final',
        }
        serializer = ProfessorNoteCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coefficient', serializer.errors)

    def test_missing_required_fields(self):
        serializer = ProfessorNoteCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('student', serializer.errors)
        self.assertIn('subject', serializer.errors)
        self.assertIn('score', serializer.errors)


class NoteApprovalSerializerTest(TestDataMixin, TestCase):
    def test_valid_approved(self):
        serializer = NoteApprovalSerializer(data={'status': 'approved'})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_rejected(self):
        serializer = NoteApprovalSerializer(data={'status': 'rejected'})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_revision_requested(self):
        serializer = NoteApprovalSerializer(data={'status': 'revision_requested'})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_status(self):
        serializer = NoteApprovalSerializer(data={'status': 'draft'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)


class NoteHistorySerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        note = self.create_professor_note()
        user = self.create_admin_user()
        history = NoteHistory.objects.create(
            note=note, action='created', changed_by=user,
        )
        serializer = NoteHistorySerializer(history)
        self.assertIn('note', serializer.data)
        self.assertIn('action', serializer.data)
        self.assertIn('changed_by_name', serializer.data)
        self.assertIn('note_title', serializer.data)
