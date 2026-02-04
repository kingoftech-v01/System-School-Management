"""
Core App Serializers - DRF serializers for core models.
"""

from rest_framework import serializers
from .models import Session, Semester, NewsAndEvents, ActivityLog


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for academic sessions."""

    class Meta:
        model = Session
        fields = ['id', 'session', 'is_current_session', 'next_session_begins']
        read_only_fields = []


class SemesterSerializer(serializers.ModelSerializer):
    """Serializer for academic semesters."""

    session_name = serializers.CharField(source='session.session', read_only=True)

    class Meta:
        model = Semester
        fields = ['id', 'semester', 'is_current_semester', 'session', 'session_name', 'next_semester_begins']
        read_only_fields = []


class NewsAndEventsSerializer(serializers.ModelSerializer):
    """Serializer for news and events."""

    posted_as_display = serializers.CharField(source='get_posted_as_display', read_only=True)

    class Meta:
        model = NewsAndEvents
        fields = ['id', 'title', 'summary', 'posted_as', 'posted_as_display', 'updated_date', 'upload_time']
        read_only_fields = ['updated_date', 'upload_time']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs."""

    class Meta:
        model = ActivityLog
        fields = ['id', 'message', 'created_at']
        read_only_fields = ['created_at']
