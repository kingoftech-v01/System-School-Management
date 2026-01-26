"""
Discipline Serializers - DRF serializers for disciplinary action API.

This module provides serializers for:
- DisciplinaryAction CRUD operations
- Nested user information
- List and detail views

All serializers return JSON-compatible data for API responses.
"""

from rest_framework import serializers
from .models import DisciplinaryAction
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# USER NESTED SERIALIZERS
# ============================================================================

class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
        read_only_fields = fields

    def get_full_name(self, obj):
        """Get user's full name."""
        return obj.get_full_name() if hasattr(obj, 'get_full_name') else obj.username


# ============================================================================
# DISCIPLINARY ACTION SERIALIZERS
# ============================================================================

class DisciplinaryActionSerializer(serializers.ModelSerializer):
    """
    Full serializer for DisciplinaryAction with nested user info.

    Used for detail views and updates.
    """

    student = UserMinimalSerializer(read_only=True)
    reported_by = UserMinimalSerializer(read_only=True)
    updated_by = UserMinimalSerializer(read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = DisciplinaryAction
        fields = [
            'id',
            'tenant',
            'student',
            'reported_by',
            'updated_by',
            'incident_type',
            'description',
            'action_taken',
            'severity',
            'severity_display',
            'incident_date',
            'resolution_date',
            'is_resolved',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'reported_by', 'updated_by', 'created_at', 'updated_at']


class DisciplinaryActionListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.

    Includes minimal information for performance.
    """

    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    reported_by_name = serializers.CharField(source='reported_by.get_full_name', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = DisciplinaryAction
        fields = [
            'id',
            'student',
            'student_name',
            'reported_by_name',
            'incident_type',
            'severity',
            'severity_display',
            'incident_date',
            'is_resolved',
            'created_at',
        ]
        read_only_fields = fields


class DisciplinaryActionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating disciplinary actions.

    Validates input and provides clear error messages.
    """

    class Meta:
        model = DisciplinaryAction
        fields = [
            'student',
            'incident_type',
            'description',
            'action_taken',
            'severity',
            'incident_date',
            'resolution_date',
            'is_resolved',
        ]

    def validate_incident_date(self, value):
        """Ensure incident date is not in the future."""
        from django.utils import timezone

        if value > timezone.now().date():
            raise serializers.ValidationError('Incident date cannot be in the future.')

        return value

    def validate_resolution_date(self, value):
        """Ensure resolution date is after incident date."""
        incident_date = self.initial_data.get('incident_date')

        if value and incident_date and value < incident_date:
            raise serializers.ValidationError('Resolution date must be after incident date.')

        return value

    def validate(self, attrs):
        """Cross-field validation."""
        # If is_resolved is True, resolution_date must be provided
        if attrs.get('is_resolved') and not attrs.get('resolution_date'):
            raise serializers.ValidationError({
                'resolution_date': 'Resolution date is required when marking action as resolved.'
            })

        return attrs
