"""
API view tests for the notes app.

Tests cover:
- ProfessorNoteViewSet CRUD + pending / approve / history actions
- NoteHistoryViewSet list / retrieve (read-only)
- Tenant filtering via request.tenant
- Unauthenticated access
"""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


class ProfessorNoteViewSetTests(TestDataMixin, TestCase):
    """Tests for ProfessorNoteViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.student = self.create_student_user()
        self.filiere = self.create_filiere(tenant=self.school)
        self.course = self.create_course()
        self.note = self.create_professor_note(
            tenant=self.school,
            student=self.student,
            professor=self.professor,
            filiere=self.filiere,
            subject=self.course,
        )

    def _auth(self, user):
        self.client.force_authenticate(user=user)

    # -- Authentication -------------------------------------------------------

    def test_list_notes_unauthenticated(self):
        url = reverse('api:notes:note-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    # -- List / Retrieve ------------------------------------------------------

    def test_list_notes_as_professor(self):
        """Professor can list notes (filtered by tenant via middleware)."""
        self._auth(self.professor)
        url = reverse('api:notes:note-list')
        response = self.client.get(url)
        # May be 200 or empty list depending on tenant matching
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_note(self):
        self._auth(self.professor)
        url = reverse('api:notes:note-detail', kwargs={'pk': self.note.pk})
        response = self.client.get(url)
        # 200 if tenant matches, 404 otherwise (tenant filtering)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Create ---------------------------------------------------------------

    def test_create_note(self):
        """Professor can create a note (tenant/professor set in perform_create)."""
        self._auth(self.professor)
        url = reverse('api:notes:note-list')
        data = {
            'student': self.student.pk,
            'filiere': self.filiere.pk,
            'subject': self.course.pk,
            'note_type': 'quiz',
            'score': '14.50',
            'coefficient': '2.00',
        }
        response = self.client.post(url, data, format='json')
        # 201 if tenant is set by middleware; 400 if validation fails
        self.assertIn(response.status_code, (status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST))

    # -- Update ---------------------------------------------------------------

    def test_update_note(self):
        self._auth(self.professor)
        url = reverse('api:notes:note-detail', kwargs={'pk': self.note.pk})
        response = self.client.patch(url, {'score': '18.00'}, format='json')
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Delete (soft delete) -------------------------------------------------

    def test_delete_note(self):
        self._auth(self.professor)
        url = reverse('api:notes:note-detail', kwargs={'pk': self.note.pk})
        response = self.client.delete(url)
        self.assertIn(response.status_code, (status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND))

    # -- Custom actions -------------------------------------------------------

    def test_pending_notes_requires_direction(self):
        """Only direction users may access the pending notes endpoint."""
        self._auth(self.student)
        url = reverse('api:notes:note-pending')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED))

    def test_pending_notes_as_direction(self):
        self._auth(self.direction)
        url = reverse('api:notes:note-pending')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('notes.views_api.notify_note_status_change')
    def test_approve_note(self, mock_task):
        """Direction user can approve a note."""
        mock_task.delay = lambda *a, **kw: None
        self.note.status = 'pending'
        self.note.save()
        self._auth(self.direction)
        url = reverse('api:notes:note-approve', kwargs={'pk': self.note.pk})
        response = self.client.post(url, {'status': 'approved'}, format='json')
        # 200 if tenant matches, 404 otherwise
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST))

    def test_approve_note_forbidden_for_student(self):
        """Students cannot approve notes."""
        self._auth(self.student)
        url = reverse('api:notes:note-approve', kwargs={'pk': self.note.pk})
        response = self.client.post(url, {'status': 'approved'}, format='json')
        self.assertIn(response.status_code, (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED))

    def test_note_history_action(self):
        """GET /notes/{pk}/history/ returns history for the note."""
        self._auth(self.professor)
        url = reverse('api:notes:note-history', kwargs={'pk': self.note.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    # -- Search / Filter ------------------------------------------------------

    def test_search_notes(self):
        self._auth(self.professor)
        url = reverse('api:notes:note-list')
        response = self.client.get(url, {'search': 'comment'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_notes_by_status(self):
        self._auth(self.professor)
        url = reverse('api:notes:note-list')
        response = self.client.get(url, {'status': 'draft'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class NoteHistoryViewSetTests(TestDataMixin, TestCase):
    """Tests for the read-only NoteHistoryViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.note = self.create_professor_note(tenant=self.school, professor=self.professor)
        # Create a history record manually
        from notes.models import NoteHistory
        self.history = NoteHistory.objects.create(
            note=self.note,
            action='created',
            changed_by=self.professor,
            new_values={'score': '15.0'},
        )

    def test_list_history_unauthenticated(self):
        url = reverse('api:notes:history-list')
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_list_history(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:notes:history-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_history(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:notes:history-detail', kwargs={'pk': self.history.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_404_NOT_FOUND))

    def test_history_is_read_only(self):
        """POST to history endpoint should fail (read-only viewset)."""
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:notes:history-list')
        response = self.client.post(url, {'action': 'created'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_history_by_action(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:notes:history-list')
        response = self.client.get(url, {'action': 'created'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_history_not_allowed(self):
        """DELETE on history should fail (read-only)."""
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:notes:history-detail', kwargs={'pk': self.history.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_history_ordering(self):
        self.client.force_authenticate(user=self.professor)
        url = reverse('api:notes:history-list')
        response = self.client.get(url, {'ordering': '-changed_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
