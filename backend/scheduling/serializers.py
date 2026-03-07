from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    Room, TimeSlot, ProfessorAvailability, ScheduleEntry,
    ScheduleException, SubstitutionRequest, ScheduleNotification,
    TimetableGeneration,
)

User = get_user_model()


# ============================================================================
# Room Serializers
# ============================================================================

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            'id', 'name', 'code', 'building', 'floor', 'capacity',
            'room_type', 'equipment', 'is_active',
        ]
        read_only_fields = ['id']


class RoomListSerializer(serializers.ModelSerializer):
    """Compact serializer for dropdowns and lists."""
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'name', 'code', 'capacity', 'room_type', 'display_name']

    def get_display_name(self, obj):
        return str(obj)


# ============================================================================
# TimeSlot Serializers
# ============================================================================

class TimeSlotSerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(
        source='get_day_of_week_display', read_only=True
    )
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = TimeSlot
        fields = [
            'id', 'name', 'start_time', 'end_time', 'day_of_week',
            'day_of_week_display', 'slot_type', 'order', 'is_active',
            'duration_minutes',
        ]
        read_only_fields = ['id']


# ============================================================================
# ProfessorAvailability Serializers
# ============================================================================

class ProfessorAvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessorAvailability
        fields = ['id', 'professor', 'time_slot', 'preference']
        read_only_fields = ['id']


# ============================================================================
# ScheduleEntry Serializers
# ============================================================================

class ScheduleEntrySerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    professor_name = serializers.SerializerMethodField()
    room_name = serializers.CharField(source='room.name', read_only=True, default='')
    filiere_name = serializers.CharField(source='filiere.name', read_only=True, default='')
    time_slot_display = serializers.CharField(source='time_slot.__str__', read_only=True)

    class Meta:
        model = ScheduleEntry
        fields = [
            'id', 'course', 'course_title', 'course_code',
            'professor', 'professor_name', 'room', 'room_name',
            'time_slot', 'time_slot_display', 'filiere', 'filiere_name',
            'group_name', 'session', 'semester',
            'effective_from', 'effective_until', 'recurrence',
            'status', 'color', 'is_locked',
        ]
        read_only_fields = ['id']

    def get_professor_name(self, obj):
        return obj.professor.get_full_name


class ScheduleEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = [
            'course', 'professor', 'room', 'time_slot', 'filiere',
            'group_name', 'session', 'semester',
            'effective_from', 'effective_until', 'recurrence',
            'status', 'color', 'is_locked',
        ]


class CalendarEventSerializer(serializers.Serializer):
    """FullCalendar-compatible event format."""
    id = serializers.CharField()
    title = serializers.CharField()
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    color = serializers.CharField()
    textColor = serializers.CharField(default='#ffffff')
    editable = serializers.BooleanField(default=False)
    extendedProps = serializers.DictField()


# ============================================================================
# ScheduleException Serializers
# ============================================================================

class ScheduleExceptionSerializer(serializers.ModelSerializer):
    schedule_entry_display = serializers.CharField(
        source='schedule_entry.__str__', read_only=True
    )

    class Meta:
        model = ScheduleException
        fields = [
            'id', 'schedule_entry', 'schedule_entry_display',
            'exception_type', 'date', 'new_room',
            'substitute_professor', 'new_start_time', 'new_end_time',
            'reason', 'is_approved', 'notify_students', 'notification_sent',
        ]
        read_only_fields = ['id', 'notification_sent']


# ============================================================================
# SubstitutionRequest Serializers
# ============================================================================

class SubstitutionRequestSerializer(serializers.ModelSerializer):
    requesting_professor_name = serializers.SerializerMethodField()
    assigned_substitute_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(
        source='schedule_entry.course.title', read_only=True
    )

    class Meta:
        model = SubstitutionRequest
        fields = [
            'id', 'schedule_entry', 'course_title', 'date',
            'requesting_professor', 'requesting_professor_name',
            'suggested_substitute', 'assigned_substitute', 'assigned_substitute_name',
            'reason', 'status', 'reviewed_by', 'reviewed_at',
        ]
        read_only_fields = ['id', 'reviewed_at']

    def get_requesting_professor_name(self, obj):
        return obj.requesting_professor.get_full_name

    def get_assigned_substitute_name(self, obj):
        if obj.assigned_substitute:
            return obj.assigned_substitute.get_full_name
        return ''


# ============================================================================
# ScheduleNotification Serializers
# ============================================================================

class ScheduleNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleNotification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'related_entry', 'related_exception',
            'is_read', 'read_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ============================================================================
# TimetableGeneration Serializers
# ============================================================================

class TimetableGenerationSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TimetableGeneration
        fields = [
            'id', 'session', 'semester', 'status', 'status_display',
            'config', 'entries_created', 'conflicts_found',
            'conflict_details', 'is_published',
            'started_at', 'completed_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'entries_created', 'conflicts_found', 'conflict_details',
            'started_at', 'completed_at', 'created_at',
        ]
