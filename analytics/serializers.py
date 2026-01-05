"""
Serializers for analytics app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent
)
from accounts.models import Student
from course.models import Course

User = get_user_model()


class StudentEngagementSerializer(serializers.ModelSerializer):
    """Serializer for student engagement metrics."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    engagement_level = serializers.SerializerMethodField()

    class Meta:
        model = StudentEngagement
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name', 'date',
            'login_count', 'total_time_minutes', 'pages_viewed', 'videos_watched',
            'documents_downloaded', 'forum_posts', 'forum_replies',
            'questions_asked', 'questions_answered', 'quizzes_attempted',
            'quizzes_completed', 'assignments_submitted', 'engagement_score',
            'engagement_level', 'created_at', 'updated_at'
        ]
        read_only_fields = ['engagement_score', 'created_at', 'updated_at']

    def get_engagement_level(self, obj):
        """Return engagement level based on score."""
        score = float(obj.engagement_score)
        if score >= 80:
            return 'High'
        elif score >= 50:
            return 'Medium'
        elif score >= 20:
            return 'Low'
        else:
            return 'Very Low'


class CourseCompletionSerializer(serializers.ModelSerializer):
    """Serializer for course completion tracking."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    days_since_enrollment = serializers.SerializerMethodField()
    average_daily_time = serializers.SerializerMethodField()
    completion_status = serializers.SerializerMethodField()

    class Meta:
        model = CourseCompletion
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name',
            'enrolled_at', 'started_at', 'completed_at', 'total_modules',
            'completed_modules', 'completion_percentage', 'total_time_spent',
            'last_activity_at', 'is_completed', 'certificate_issued',
            'days_since_enrollment', 'average_daily_time', 'completion_status'
        ]
        read_only_fields = ['completion_percentage', 'is_completed']

    def get_days_since_enrollment(self, obj):
        """Calculate days since enrollment."""
        from django.utils import timezone
        delta = timezone.now() - obj.enrolled_at
        return delta.days

    def get_average_daily_time(self, obj):
        """Calculate average daily time spent."""
        days = self.get_days_since_enrollment(obj)
        if days > 0:
            return round(obj.total_time_spent / days, 2)
        return 0

    def get_completion_status(self, obj):
        """Return completion status."""
        if obj.is_completed:
            return 'Completed'
        elif obj.completion_percentage >= 75:
            return 'Near Completion'
        elif obj.completion_percentage >= 50:
            return 'In Progress'
        elif obj.completion_percentage >= 25:
            return 'Started'
        elif obj.started_at:
            return 'Just Started'
        else:
            return 'Not Started'


class LearningOutcomeSerializer(serializers.ModelSerializer):
    """Serializer for learning outcomes."""
    course_name = serializers.CharField(source='course.name', read_only=True)
    total_measurements = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = LearningOutcome
        fields = [
            'id', 'course', 'course_name', 'outcome_name', 'description',
            'assessment_method', 'target_percentage', 'is_active',
            'created_at', 'total_measurements', 'success_rate'
        ]
        read_only_fields = ['created_at']

    def get_total_measurements(self, obj):
        """Count total measurements."""
        return obj.measurements.count()

    def get_success_rate(self, obj):
        """Calculate success rate."""
        total = obj.measurements.count()
        if total > 0:
            successful = obj.measurements.filter(meets_target=True).count()
            return round((successful / total) * 100, 2)
        return 0


class OutcomeMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for outcome measurements."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    outcome_name = serializers.CharField(source='outcome.outcome_name', read_only=True)
    target_percentage = serializers.DecimalField(
        source='outcome.target_percentage',
        max_digits=5,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OutcomeMeasurement
        fields = [
            'id', 'outcome', 'outcome_name', 'student', 'student_name',
            'score', 'max_score', 'percentage', 'assessment_name',
            'assessed_at', 'meets_target', 'target_percentage'
        ]
        read_only_fields = ['percentage', 'meets_target']


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for activity logs."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        model = ActivityLog
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name',
            'activity_type', 'activity_type_display', 'activity_description',
            'url', 'ip_address', 'user_agent', 'duration_seconds',
            'metadata', 'created_at'
        ]
        read_only_fields = ['created_at']


class AtRiskStudentSerializer(serializers.ModelSerializer):
    """Serializer for at-risk students."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    contacted_by_name = serializers.CharField(source='contacted_by.get_full_name', read_only=True)
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
    risk_factors = serializers.SerializerMethodField()

    class Meta:
        model = AtRiskStudent
        fields = [
            'id', 'student', 'student_name', 'course', 'course_name',
            'risk_level', 'risk_level_display', 'risk_score', 'low_engagement',
            'low_attendance', 'failing_grades', 'no_recent_activity',
            'missing_assignments', 'intervention_needed', 'intervention_notes',
            'contacted_at', 'contacted_by', 'contacted_by_name', 'is_active',
            'resolved_at', 'identified_at', 'updated_at', 'risk_factors'
        ]
        read_only_fields = ['risk_score', 'risk_level', 'identified_at', 'updated_at']

    def get_risk_factors(self, obj):
        """Return list of active risk factors."""
        factors = []
        if obj.low_engagement:
            factors.append('Low Engagement')
        if obj.low_attendance:
            factors.append('Low Attendance')
        if obj.failing_grades:
            factors.append('Failing Grades')
        if obj.no_recent_activity:
            factors.append('No Recent Activity')
        if obj.missing_assignments > 0:
            factors.append(f'{obj.missing_assignments} Missing Assignments')
        return factors


class EngagementTrendSerializer(serializers.Serializer):
    """Serializer for engagement trend data."""
    date = serializers.DateField()
    engagement_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    login_count = serializers.IntegerField()
    total_time_minutes = serializers.IntegerField()
    forum_activity = serializers.IntegerField()
    assessment_activity = serializers.IntegerField()


class CourseDashboardSerializer(serializers.Serializer):
    """Serializer for course analytics dashboard."""
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    average_completion = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_engagement = serializers.DecimalField(max_digits=5, decimal_places=2)
    at_risk_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()


class StudentDashboardSerializer(serializers.Serializer):
    """Serializer for student analytics dashboard."""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    enrolled_courses = serializers.IntegerField()
    completed_courses = serializers.IntegerField()
    average_engagement = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_time_spent = serializers.IntegerField()
    recent_activity_count = serializers.IntegerField()
    at_risk_courses = serializers.ListField(child=serializers.CharField())
