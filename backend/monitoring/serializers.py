"""
Monitoring Serializers - DRF serializers for statistics output.

This module provides serializers for:
- Dashboard statistics structure
- User count aggregations
- Library and discipline stats

Note: Monitoring doesn't have models, these are output-only serializers.
"""

from rest_framework import serializers


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user count statistics."""
    students = serializers.IntegerField()
    professors = serializers.IntegerField()
    parents = serializers.IntegerField()


class GenderDistributionSerializer(serializers.Serializer):
    """Serializer for gender distribution stats."""
    gender = serializers.CharField()
    count = serializers.IntegerField()


class EnrollmentStatsSerializer(serializers.Serializer):
    """Serializer for enrollment statistics."""
    status = serializers.CharField()
    level = serializers.CharField(required=False)
    count = serializers.IntegerField()


class LibraryStatsSerializer(serializers.Serializer):
    """Serializer for library statistics."""
    total_books = serializers.IntegerField()
    borrowed = serializers.IntegerField()
    overdue = serializers.IntegerField()


class DisciplineStatsSerializer(serializers.Serializer):
    """Serializer for discipline statistics."""
    total = serializers.IntegerField()
    unresolved = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    """Combined dashboard statistics serializer."""
    users = UserStatsSerializer()
    gender_distribution = GenderDistributionSerializer(many=True)
    enrollment = EnrollmentStatsSerializer(many=True)
    library = LibraryStatsSerializer(required=False, allow_null=True)
    discipline = DisciplineStatsSerializer(required=False, allow_null=True)


class BooksByCategorySerializer(serializers.Serializer):
    """Serializer for books grouped by category."""
    category = serializers.CharField()
    count = serializers.IntegerField()


class BorrowStatusSerializer(serializers.Serializer):
    """Serializer for borrow records grouped by status."""
    status = serializers.CharField()
    count = serializers.IntegerField()


class DetailedLibraryStatsSerializer(serializers.Serializer):
    """Detailed library statistics."""
    books_by_category = BooksByCategorySerializer(many=True)
    borrow_status = BorrowStatusSerializer(many=True)
