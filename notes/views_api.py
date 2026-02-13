"""
Notes API Views - REST API endpoints.

This module provides API endpoints for:
- Professor notes CRUD
- Note approval workflow
- Note history tracking

All views return JSON responses.
API URL namespace: api:v1:notes:resource-name
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .models import ProfessorNote, NoteHistory
from .serializers import (
    ProfessorNoteSerializer,
    ProfessorNoteListSerializer,
    ProfessorNoteCreateSerializer,
    NoteHistorySerializer,
    NoteApprovalSerializer
)
from accounts.permissions import IsProfessorUser, IsDirectionUser


# ============================================================================
# PROFESSOR NOTE VIEWSET
# ============================================================================

class ProfessorNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing professor notes.

    Features:
    - List notes (filtered by professor for non-direction users)
    - Create notes (professor only)
    - Update notes (professor only, not approved notes)
    - Delete notes (soft delete, professor only, not approved notes)
    - Approve/reject notes (direction only)

    Filtering: status, student, subject, is_deleted
    Search: comment
    Ordering: created_at, score
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'student', 'subject', 'is_deleted']
    search_fields = ['comment']
    ordering_fields = ['created_at', 'score']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter notes based on user role."""
        user = self.request.user
        queryset = ProfessorNote.objects.filter(
            tenant=self.request.tenant
        ).select_related('professor', 'student', 'subject', 'approved_by')

        # Professors can only see their own notes
        if getattr(user, 'role', '') not in ('direction', 'admin'):
            queryset = queryset.filter(professor=user)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProfessorNoteListSerializer
        elif self.action == 'create':
            return ProfessorNoteCreateSerializer
        elif self.action == 'approve':
            return NoteApprovalSerializer
        return ProfessorNoteSerializer

    def perform_create(self, serializer):
        """Set professor and tenant when creating note."""
        note = serializer.save(
            professor=self.request.user,
            tenant=self.request.tenant
        )

        # Create history record
        NoteHistory.objects.create(
            note=note,
            action='created',
            changed_by=self.request.user,
            new_values={'score': str(note.score), 'comment': note.comment}
        )

    def perform_update(self, serializer):
        """Track changes when updating note."""
        note = self.get_object()

        # Cannot update approved notes
        if note.status == 'approved':
            raise serializers.ValidationError('Cannot update an approved note.')

        old_score = note.score
        old_comment = note.comment

        updated_note = serializer.save()

        # Create history record if changed
        if old_score != updated_note.score or old_comment != updated_note.comment:
            NoteHistory.objects.create(
                note=updated_note,
                action='updated',
                changed_by=self.request.user,
                old_values={'score': str(old_score), 'comment': old_comment},
                new_values={'score': str(updated_note.score), 'comment': updated_note.comment},
                change_summary=f'Score changed from {old_score} to {updated_note.score}'
            )

    def perform_destroy(self, instance):
        """Soft delete note."""
        if instance.status == 'approved':
            raise serializers.ValidationError('Cannot delete an approved note.')

        instance.is_deleted = True
        instance.save()

        NoteHistory.objects.create(
            note=instance,
            action='deleted',
            changed_by=self.request.user,
            change_summary='Note marked as deleted'
        )

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsDirectionUser])
    def pending(self, request):
        """Get notes pending approval."""
        notes = self.get_queryset().filter(status='pending', is_deleted=False)
        page = self.paginate_queryset(notes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirectionUser])
    def approve(self, request, pk=None):
        """Approve, reject, or request revision for a note."""
        note = self.get_object()
        serializer = NoteApprovalSerializer(note, data=request.data, partial=True)

        if serializer.is_valid():
            old_status = note.status

            note = serializer.save(
                approved_by=request.user,
                approved_at=timezone.now()
            )

            # Create history record
            NoteHistory.objects.create(
                note=note,
                action='status_changed',
                changed_by=request.user,
                old_values={'status': old_status},
                new_values={'status': note.status},
                change_summary=f'Status changed from {old_status} to {note.status}'
            )

            # Send notification via Celery
            from .tasks import notify_note_status_change
            notify_note_status_change.delay(note.id, note.status)

            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get note history."""
        note = self.get_object()
        history = NoteHistory.objects.filter(note=note).order_by('-changed_at')
        serializer = NoteHistorySerializer(history, many=True)
        return Response(serializer.data)


# ============================================================================
# NOTE HISTORY VIEWSET
# ============================================================================

class NoteHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for note history.

    Features:
    - List history records
    - Retrieve individual history record

    Filtering: note, action, changed_by
    Ordering: changed_at
    """
    queryset = NoteHistory.objects.all()
    serializer_class = NoteHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['note', 'action', 'changed_by']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']

    def get_queryset(self):
        """Filter history by tenant."""
        return NoteHistory.objects.filter(
            note__tenant=self.request.tenant
        ).select_related('note', 'changed_by')
