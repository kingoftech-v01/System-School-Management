"""
Views for analytics app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q, Sum, Max
from django.utils import timezone
from datetime import timedelta, datetime

from .models import (
    StudentEngagement, CourseCompletion, LearningOutcome,
    OutcomeMeasurement, ActivityLog, AtRiskStudent
)
from .serializers import (
    StudentEngagementSerializer, CourseCompletionSerializer,
    LearningOutcomeSerializer, OutcomeMeasurementSerializer,
    ActivityLogSerializer, AtRiskStudentSerializer,
    EngagementTrendSerializer, CourseDashboardSerializer,
    StudentDashboardSerializer
)
from .permissions import (
    CanViewAnalytics, CanViewOwnAnalytics, CanManageAtRiskStudents,
    CanViewActivityLogs, CanViewLearningOutcomes, CanManageLearningOutcomes,
    CanExportAnalytics
)
from accounts.models import Student
from course.models import Course


class StudentEngagementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for student engagement metrics.
    """
    queryset = StudentEngagement.objects.select_related('student', 'course').all()
    serializer_class = StudentEngagementSerializer
    permission_classes = [IsAuthenticated, CanViewOwnAnalytics]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'date']
    ordering_fields = ['date', 'engagement_score', 'total_time_minutes']
    ordering = ['-date']

    def get_queryset(self):
        """Filter engagement based on user role."""
        user = self.request.user

        # Staff and teachers can see all engagement data
        if user.is_staff or user.is_lecturer:
            return self.queryset

        # Students can only see their own engagement
        try:
            student = Student.objects.get(student=user)
            return self.queryset.filter(student=student)
        except Student.DoesNotExist:
            return self.queryset.none()

    @action(detail=False, methods=['get'])
    def my_engagement(self, request):
        """Get current user's engagement metrics."""
        try:
            student = Student.objects.get(student=request.user)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get last 30 days engagement
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        engagement = self.queryset.filter(
            student=student,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('-date')

        serializer = self.get_serializer(engagement, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanViewAnalytics])
    def trends(self, request):
        """Get engagement trends over time."""
        days = int(request.query_params.get('days', 30))
        course_id = request.query_params.get('course')

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        queryset = self.queryset.filter(date__gte=start_date, date__lte=end_date)

        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Aggregate by date
        trends = queryset.values('date').annotate(
            avg_engagement=Avg('engagement_score'),
            total_logins=Sum('login_count'),
            total_time=Sum('total_time_minutes'),
            total_forum_activity=Sum('forum_posts') + Sum('forum_replies'),
            total_assessments=Sum('quizzes_completed') + Sum('assignments_submitted')
        ).order_by('date')

        data = []
        for trend in trends:
            data.append({
                'date': trend['date'],
                'engagement_score': trend['avg_engagement'] or 0,
                'login_count': trend['total_logins'] or 0,
                'total_time_minutes': trend['total_time'] or 0,
                'forum_activity': trend['total_forum_activity'] or 0,
                'assessment_activity': trend['total_assessments'] or 0
            })

        serializer = EngagementTrendSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """Recalculate engagement scores for all records."""
        engagement_records = self.get_queryset()

        for record in engagement_records:
            record.calculate_engagement_score()

        return Response({
            'detail': f'Recalculated {engagement_records.count()} engagement records.'
        })


class CourseCompletionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for course completion tracking.
    """
    queryset = CourseCompletion.objects.select_related('student', 'course').all()
    serializer_class = CourseCompletionSerializer
    permission_classes = [IsAuthenticated, CanViewOwnAnalytics]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'is_completed', 'certificate_issued']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'course__name']
    ordering_fields = ['enrolled_at', 'completion_percentage', 'last_activity_at']
    ordering = ['-enrolled_at']

    def get_queryset(self):
        """Filter completions based on user role."""
        user = self.request.user

        # Staff and teachers can see all completion data
        if user.is_staff or user.is_lecturer:
            return self.queryset

        # Students can only see their own completions
        try:
            student = Student.objects.get(student=user)
            return self.queryset.filter(student=student)
        except Student.DoesNotExist:
            return self.queryset.none()

    @action(detail=False, methods=['get'])
    def my_progress(self, request):
        """Get current user's course progress."""
        try:
            student = Student.objects.get(student=request.user)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        completions = self.queryset.filter(student=student)
        serializer = self.get_serializer(completions, many=True)

        return Response({
            'total_courses': completions.count(),
            'completed_courses': completions.filter(is_completed=True).count(),
            'in_progress': completions.filter(is_completed=False).count(),
            'average_completion': completions.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
            'courses': serializer.data
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanViewAnalytics])
    def update_progress(self, request, pk=None):
        """Update course completion progress."""
        completion = self.get_object()
        completion.update_progress()

        return Response({
            'detail': 'Progress updated successfully.',
            'completion_percentage': completion.completion_percentage,
            'is_completed': completion.is_completed
        })


class LearningOutcomeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for learning outcomes.
    """
    queryset = LearningOutcome.objects.select_related('course').all()
    serializer_class = LearningOutcomeSerializer
    permission_classes = [IsAuthenticated, CanViewLearningOutcomes, CanManageLearningOutcomes]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'assessment_method', 'is_active']
    search_fields = ['outcome_name', 'description']
    ordering_fields = ['created_at', 'target_percentage']
    ordering = ['course', 'outcome_name']

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, CanViewAnalytics])
    def achievement_report(self, request, pk=None):
        """Get achievement report for this outcome."""
        outcome = self.get_object()

        measurements = outcome.measurements.all()
        total_students = measurements.values('student').distinct().count()
        successful = measurements.filter(meets_target=True).values('student').distinct().count()

        success_rate = (successful / total_students * 100) if total_students > 0 else 0

        return Response({
            'outcome_name': outcome.outcome_name,
            'target_percentage': outcome.target_percentage,
            'total_students': total_students,
            'successful_students': successful,
            'success_rate': round(success_rate, 2),
            'average_score': measurements.aggregate(Avg('percentage'))['percentage__avg'] or 0,
            'total_measurements': measurements.count()
        })


class OutcomeMeasurementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for outcome measurements.
    """
    queryset = OutcomeMeasurement.objects.select_related('outcome', 'student').all()
    serializer_class = OutcomeMeasurementSerializer
    permission_classes = [IsAuthenticated, CanViewOwnAnalytics]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['outcome', 'student', 'meets_target']
    ordering_fields = ['assessed_at', 'percentage']
    ordering = ['-assessed_at']

    def get_queryset(self):
        """Filter measurements based on user role."""
        user = self.request.user

        # Staff and teachers can see all measurements
        if user.is_staff or user.is_lecturer:
            return self.queryset

        # Students can only see their own measurements
        try:
            student = Student.objects.get(student=user)
            return self.queryset.filter(student=student)
        except Student.DoesNotExist:
            return self.queryset.none()


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for activity logs (read-only).
    """
    queryset = ActivityLog.objects.select_related('student', 'course').all()
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated, CanViewActivityLogs]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'activity_type']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Filter activity logs based on user role."""
        user = self.request.user

        # Staff can see all activity logs
        if user.is_staff:
            return self.queryset

        # Students can only see their own activity logs
        try:
            student = Student.objects.get(student=user)
            return self.queryset.filter(student=student)
        except Student.DoesNotExist:
            return self.queryset.none()

    @action(detail=False, methods=['get'])
    def my_activity(self, request):
        """Get current user's recent activity."""
        try:
            student = Student.objects.get(student=request.user)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        activities = self.queryset.filter(
            student=student,
            created_at__gte=start_date
        )

        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, CanViewAnalytics])
    def activity_summary(self, request):
        """Get activity summary statistics."""
        course_id = request.query_params.get('course')
        days = int(request.query_params.get('days', 30))

        start_date = timezone.now() - timedelta(days=days)
        queryset = self.queryset.filter(created_at__gte=start_date)

        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Aggregate by activity type
        summary = queryset.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'period_days': days,
            'total_activities': queryset.count(),
            'unique_students': queryset.values('student').distinct().count(),
            'by_type': list(summary)
        })


class AtRiskStudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for at-risk students.
    """
    queryset = AtRiskStudent.objects.select_related(
        'student', 'course', 'contacted_by'
    ).all()
    serializer_class = AtRiskStudentSerializer
    permission_classes = [IsAuthenticated, CanManageAtRiskStudents]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'risk_level', 'intervention_needed', 'is_active']
    search_fields = ['student__student__first_name', 'student__student__last_name']
    ordering_fields = ['identified_at', 'risk_score']
    ordering = ['-risk_score', '-identified_at']

    @action(detail=True, methods=['post'])
    def contact(self, request, pk=None):
        """Mark student as contacted for intervention."""
        at_risk = self.get_object()

        notes = request.data.get('notes', '')

        at_risk.contacted_at = timezone.now()
        at_risk.contacted_by = request.user
        at_risk.intervention_notes = notes
        at_risk.save()

        return Response({
            'detail': 'Student marked as contacted.',
            'contacted_at': at_risk.contacted_at
        })

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark at-risk status as resolved."""
        at_risk = self.get_object()

        at_risk.is_active = False
        at_risk.resolved_at = timezone.now()
        at_risk.save()

        return Response({
            'detail': 'At-risk status resolved.',
            'resolved_at': at_risk.resolved_at
        })

    @action(detail=False, methods=['post'])
    def recalculate_all(self, request):
        """Recalculate risk scores for all at-risk students."""
        at_risk_students = self.queryset.filter(is_active=True)

        for student in at_risk_students:
            student.calculate_risk_score()

        return Response({
            'detail': f'Recalculated {at_risk_students.count()} at-risk student records.'
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get at-risk student dashboard summary."""
        queryset = self.get_queryset().filter(is_active=True)

        summary = {
            'total_at_risk': queryset.count(),
            'by_risk_level': {
                'critical': queryset.filter(risk_level='critical').count(),
                'high': queryset.filter(risk_level='high').count(),
                'medium': queryset.filter(risk_level='medium').count(),
                'low': queryset.filter(risk_level='low').count(),
            },
            'need_intervention': queryset.filter(intervention_needed=True).count(),
            'contacted': queryset.filter(contacted_at__isnull=False).count(),
            'not_contacted': queryset.filter(contacted_at__isnull=True).count(),
        }

        return Response(summary)


class AnalyticsDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics dashboards.
    """
    permission_classes = [IsAuthenticated, CanViewAnalytics]

    @action(detail=False, methods=['get'])
    def course_dashboard(self, request):
        """Get course analytics dashboard."""
        course_id = request.query_params.get('course')

        if not course_id:
            return Response(
                {'detail': 'course parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Course not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get course statistics
        completions = CourseCompletion.objects.filter(course=course)
        engagements = StudentEngagement.objects.filter(course=course)

        # Active students (activity in last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        active_students = engagements.filter(date__gte=week_ago.date()).values('student').distinct().count()

        dashboard_data = {
            'course_id': course.id,
            'course_name': course.name,
            'total_students': completions.count(),
            'active_students': active_students,
            'average_completion': completions.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0,
            'average_engagement': engagements.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0,
            'at_risk_count': AtRiskStudent.objects.filter(course=course, is_active=True).count(),
            'completed_count': completions.filter(is_completed=True).count(),
        }

        serializer = CourseDashboardSerializer(dashboard_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def student_dashboard(self, request):
        """Get student analytics dashboard."""
        try:
            student = Student.objects.get(student=request.user)
        except Student.DoesNotExist:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get student statistics
        completions = CourseCompletion.objects.filter(student=student)
        engagements = StudentEngagement.objects.filter(student=student)
        at_risk = AtRiskStudent.objects.filter(student=student, is_active=True)

        # Recent activity (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_activity = ActivityLog.objects.filter(
            student=student,
            created_at__gte=week_ago
        ).count()

        dashboard_data = {
            'student_id': student.id,
            'student_name': student.student.get_full_name,
            'enrolled_courses': completions.count(),
            'completed_courses': completions.filter(is_completed=True).count(),
            'average_engagement': engagements.aggregate(Avg('engagement_score'))['engagement_score__avg'] or 0,
            'total_time_spent': completions.aggregate(Sum('total_time_spent'))['total_time_spent__sum'] or 0,
            'recent_activity_count': recent_activity,
            'at_risk_courses': list(at_risk.values_list('course__name', flat=True))
        }

        serializer = StudentDashboardSerializer(dashboard_data)
        return Response(serializer.data)
