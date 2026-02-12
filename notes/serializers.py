"""
Notes Serializers - DRF serializers for professor notes API.

This module provides serializers for:
- ProfessorNote model (CRUD operations)
- NoteHistory model (read-only)
- Note approval workflow
"""

from rest_framework import serializers
from .models import ProfessorNote, NoteHistory


# ============================================================================
# PROFESSOR NOTE SERIALIZERS
# ============================================================================

class ProfessorNoteSerializer(serializers.ModelSerializer):
    """
    Full serializer for professor notes.
    Includes all fields and nested relationships.
    """
    professor_name = serializers.CharField(source='professor.get_full_name', read_only=True)
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.title', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)

    class Meta:
        model = ProfessorNote
        fields = [
            'id', 'tenant', 'student', 'student_name', 'professor', 'professor_name',
            'subject', 'subject_name', 'score', 'coefficient', 'note_type',
            'note_type_display', 'comment', 'status', 'status_display',
            'approved_by', 'approved_by_name', 'approved_at', 'approval_notes',
            'is_deleted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['professor', 'tenant', 'approved_by', 'approved_at', 'created_at', 'updated_at']


class ProfessorNoteListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing notes.
    Reduced fields for performance.
    """
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ProfessorNote
        fields = [
            'id', 'student_name', 'subject_name', 'score', 'coefficient',
            'note_type', 'status', 'status_display', 'created_at'
        ]


class ProfessorNoteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating professor notes.
    Excludes read-only and auto-populated fields.
    """
    class Meta:
        model = ProfessorNote
        fields = [
            'student', 'subject', 'score', 'coefficient', 'note_type', 'comment', 'status'
        ]

    def validate_score(self, value):
        """Validate score is within valid range."""
        if value < 0 or value > 20:
            raise serializers.ValidationError('Score must be between 0 and 20.')
        return value

    def validate_coefficient(self, value):
        """Validate coefficient is positive."""
        if value <= 0:
            raise serializers.ValidationError('Coefficient must be greater than 0.')
        return value


class NoteApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for approving/rejecting notes.
    Direction only.
    """
    class Meta:
        model = ProfessorNote
        fields = ['status', 'approval_notes']

    def validate_status(self, value):
        """Ensure status is valid for approval action."""
        allowed_statuses = ['approved', 'rejected', 'revision_requested']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f'Status must be one of: {", ".join(allowed_statuses)}'
            )
        return value


# ============================================================================
# NOTE HISTORY SERIALIZERS
# ============================================================================

class NoteHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for note history records.
    Read-only.
    """
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    note_title = serializers.SerializerMethodField()

    class Meta:
        model = NoteHistory
        fields = [
            'id', 'note', 'note_title', 'action', 'changed_by', 'changed_by_name',
            'changed_at', 'old_values', 'new_values', 'change_summary'
        ]

    def get_note_title(self, obj):
        """Get a descriptive title for the note."""
        return f"{obj.note.student.get_full_name} - {obj.note.subject.title}"
