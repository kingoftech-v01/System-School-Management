"""
Search Serializers - DRF serializers for search API.

This module provides serializers for:
- Unified search results across multiple models
- Individual model serializers

All serializers return JSON-compatible data for API responses.
"""

from rest_framework import serializers
from core.models import NewsAndEvents
from course.models import Program, Course
from quiz.models import Quiz


# ============================================================================
# UNIFIED SEARCH RESULT SERIALIZER
# ============================================================================

class UnifiedSearchResultSerializer(serializers.Serializer):
    """
    Serializer for unified search results.

    Handles different model types and provides consistent output format.
    Each result includes:
    - id: Object identifier
    - title: Object title/name
    - type: Model type (news, program, course, quiz)
    - url: Object detail URL (optional)
    - summary: Short description (optional)
    """

    id = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_id(self, obj):
        """Get object primary key."""
        return obj.pk

    def get_title(self, obj):
        """Get object title."""
        return getattr(obj, 'title', str(obj))

    def get_type(self, obj):
        """Determine object type based on model class."""
        model_name = obj.__class__.__name__.lower()

        type_mapping = {
            'newsandevents': 'news',
            'program': 'program',
            'course': 'course',
            'quiz': 'quiz'
        }

        return type_mapping.get(model_name, 'unknown')

    def get_url(self, obj):
        """Get object detail URL if available."""
        # Return slug or pk for URL construction
        if hasattr(obj, 'slug'):
            return obj.slug
        return None

    def get_summary(self, obj):
        """Get object summary or description."""
        if hasattr(obj, 'summary'):
            return obj.summary
        elif hasattr(obj, 'description'):
            return obj.description
        return None

    def get_created_at(self, obj):
        """Get creation timestamp if available."""
        if hasattr(obj, 'created_at'):
            return obj.created_at
        elif hasattr(obj, 'upload_time'):
            return obj.upload_time  # NewsAndEvents
        elif hasattr(obj, 'timestamp'):
            return obj.timestamp  # Quiz
        return None


# ============================================================================
# MODEL-SPECIFIC SERIALIZERS (Optional - for future use)
# ============================================================================

class NewsSearchSerializer(serializers.ModelSerializer):
    """Serializer for NewsAndEvents search results."""

    class Meta:
        model = NewsAndEvents
        fields = ['id', 'title', 'summary', 'created_at', 'updated_at']
        read_only_fields = fields


class ProgramSearchSerializer(serializers.ModelSerializer):
    """Serializer for Program search results."""

    class Meta:
        model = Program
        fields = ['id', 'title', 'summary', 'created_at']
        read_only_fields = fields


class CourseSearchSerializer(serializers.ModelSerializer):
    """Serializer for Course search results."""

    class Meta:
        model = Course
        fields = ['id', 'title', 'code', 'slug', 'summary', 'created_at']
        read_only_fields = fields


class QuizSearchSerializer(serializers.ModelSerializer):
    """Serializer for Quiz search results."""

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at']
        read_only_fields = fields
