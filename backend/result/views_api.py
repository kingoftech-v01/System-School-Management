"""
Result App API Views - DRF ViewSets for result models.

This module provides API endpoints for:
- Student grade management
- Results and GPA calculation
- Grade appeals workflow
- Transcript generation

API URL namespace: api:v1:result:resource-name
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import (
    TakenCourse, Result, GradeComponentWeight,
    GradeAppeal, GradeHistory, Transcript
)
from .serializers import (
    TakenCourseSerializer, TakenCourseUpdateSerializer,
    ResultSerializer, GradeComponentWeightSerializer,
    GradeAppealSerializer, GradeHistorySerializer,
    TranscriptSerializer, StudentGPASerializer
)
from accounts.models import Student
from core.models import Semester


class TakenCourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for student taken courses and grades.
    """
    queryset = TakenCourse.objects.select_related('student', 'course').all()
    serializer_class = TakenCourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'course', 'grade', 'comment']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'course__title', 'course__code']
    ordering_fields = ['total', 'grade', 'course__title']
    ordering = ['-total']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['update', 'partial_update']:
            return TakenCourseUpdateSerializer
        return TakenCourseSerializer

    @action(detail=False, methods=['get'])
    def my_grades(self, request):
        """Get grades for the current student."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        taken_courses = TakenCourse.objects.filter(student=student).select_related('course')
        serializer = self.get_serializer(taken_courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_semester(self, request):
        """Get courses by semester."""
        semester_id = request.query_params.get('semester_id')
        if not semester_id:
            return Response(
                {'detail': 'semester_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        semester = get_object_or_404(Semester, id=semester_id)
        taken_courses = TakenCourse.objects.filter(
            course__semester=semester.semester
        ).select_related('student', 'course')

        serializer = self.get_serializer(taken_courses, many=True)
        return Response(serializer.data)


class ResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for semester results and GPA.
    """
    queryset = Result.objects.select_related('student').all()
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'semester', 'session', 'level']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'student__id_number']
    ordering_fields = ['gpa', 'cgpa', 'session']
    ordering = ['-session']

    @action(detail=False, methods=['get'])
    def my_results(self, request):
        """Get results for the current student."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        results = Result.objects.filter(student=student)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calculate_gpa(self, request):
        """Calculate GPA for current student."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get current semester
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            return Response(
                {'detail': 'No active semester found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate GPA
        taken_courses = TakenCourse.objects.filter(
            student=student,
            course__level=student.level,
            course__semester=current_semester.semester
        )

        total_points = sum(tc.point for tc in taken_courses)
        total_credits = sum(tc.course.credit for tc in taken_courses)

        current_gpa = 0.0
        if total_credits > 0:
            current_gpa = float(total_points / total_credits)

        # Calculate CGPA
        all_taken_courses = TakenCourse.objects.filter(student=student)
        all_total_points = sum(tc.point for tc in all_taken_courses)
        all_total_credits = sum(tc.course.credit for tc in all_taken_courses)

        cgpa = 0.0
        if all_total_credits > 0:
            cgpa = float(all_total_points / all_total_credits)

        return Response({
            'student_id': student.id,
            'student_name': student.student.get_full_name,
            'current_gpa': round(current_gpa, 2),
            'cumulative_gpa': round(cgpa, 2),
            'total_credits': all_total_credits,
            'completed_courses': all_taken_courses.count()
        })


class GradeComponentWeightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for grade component weights configuration.
    """
    queryset = GradeComponentWeight.objects.select_related('course', 'program').all()
    serializer_class = GradeComponentWeightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['course', 'program']


class GradeAppealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for grade appeal workflow.
    """
    queryset = GradeAppeal.objects.select_related('taken_course', 'student', 'reviewed_by').all()
    serializer_class = GradeAppealSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'student']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'taken_course__course__title']
    ordering_fields = ['submitted_at', 'status']
    ordering = ['-submitted_at']

    @action(detail=False, methods=['get'])
    def my_appeals(self, request):
        """Get appeals for the current student."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        appeals = GradeAppeal.objects.filter(student=student).select_related('taken_course')
        serializer = self.get_serializer(appeals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a grade appeal (lecturer/admin only)."""
        if not (request.user.is_lecturer or request.user.is_staff):
            return Response(
                {'detail': 'Only lecturers and admins can approve appeals.'},
                status=status.HTTP_403_FORBIDDEN
            )

        appeal = self.get_object()
        notes = request.data.get('notes', '')

        appeal.approve(reviewer=request.user, notes=notes)

        serializer = self.get_serializer(appeal)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a grade appeal (lecturer/admin only)."""
        if not (request.user.is_lecturer or request.user.is_staff):
            return Response(
                {'detail': 'Only lecturers and admins can reject appeals.'},
                status=status.HTTP_403_FORBIDDEN
            )

        appeal = self.get_object()
        notes = request.data.get('notes', '')

        appeal.reject(reviewer=request.user, notes=notes)

        serializer = self.get_serializer(appeal)
        return Response(serializer.data)


class GradeHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for grade history (read-only audit trail).
    """
    queryset = GradeHistory.objects.select_related('taken_course', 'changed_by').all()
    serializer_class = GradeHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['taken_course', 'changed_by']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']


class TranscriptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for transcript generation and management.
    """
    queryset = Transcript.objects.select_related('student', 'generated_by').all()
    serializer_class = TranscriptSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'transcript_type', 'is_certified']
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']

    @action(detail=False, methods=['get'])
    def my_transcripts(self, request):
        """Get transcripts for the current student."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        transcripts = Transcript.objects.filter(student=student)
        serializer = self.get_serializer(transcripts, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def certify(self, request, pk=None):
        """Certify a transcript (admin only)."""
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only administrators can certify transcripts.'},
                status=status.HTTP_403_FORBIDDEN
            )

        transcript = self.get_object()
        certification_number = request.data.get('certification_number')

        if not certification_number:
            return Response(
                {'detail': 'certification_number is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        transcript.is_certified = True
        transcript.certification_number = certification_number
        transcript.save()

        serializer = self.get_serializer(transcript, context={'request': request})
        return Response(serializer.data)
