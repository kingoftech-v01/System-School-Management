"""
Events Serializers - DRF serializers for events API.

This module provides serializers for:
- Event CRUD operations
- Nested user information
- List and detail views

All serializers return JSON-compatible data for API responses.
"""

from rest_framework import serializers
from .models import Event
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
# EVENT SERIALIZERS
# ============================================================================

class EventSerializer(serializers.ModelSerializer):
    """
    Full serializer for Event with nested user info.

    Used for detail views and updates.
    """

    created_by = UserMinimalSerializer(read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'tenant',
            'title',
            'description',
            'event_type',
            'event_type_display',
            'start_date',
            'end_date',
            'location',
            'target_audience',
            'target_audience_display',
            'send_reminder',
            'reminder_sent',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['id', 'tenant', 'created_by', 'created_at', 'reminder_sent']


class EventListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.

    Includes minimal information for performance.
    """

    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    target_audience_display = serializers.CharField(source='get_target_audience_display', read_only=True)

    class Meta:
        model = Event
        fields = [
            'id',
            'title',
            'event_type',
            'event_type_display',
            'start_date',
            'end_date',
            'location',
            'target_audience',
            'target_audience_display',
            'created_by_name',
        ]
        read_only_fields = fields


class EventCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating events.

    Validates input and provides clear error messages.
    """

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'event_type',
            'start_date',
            'end_date',
            'location',
            'target_audience',
            'send_reminder',
        ]

    def validate_end_date(self, value):
        """Ensure end date is after start date."""
        start_date = self.initial_data.get('start_date')

        if value and start_date and value < start_date:
            raise serializers.ValidationError('End date must be after start date.')

        return value

    def validate(self, attrs):
        """Cross-field validation."""
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })

        return attrs
