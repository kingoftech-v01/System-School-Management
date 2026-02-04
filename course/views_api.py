"""
Course App API Views - DRF ViewSets for course models.

This module provides API endpoints for:
- Programs management
- Courses management
- Course allocations
- Course documentation (files and videos)
- Course registration

API URL namespace: api:v1:course:resource-name
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import Program, Course, CourseAllocation, Upload, UploadVideo
from .serializers import (
    ProgramSerializer, CourseSerializer, CourseAllocationSerializer,
    UploadSerializer, UploadVideoSerializer,
    CourseRegistrationSerializer, CourseDropSerializer
)
from accounts.models import Student
from result.models import TakenCourse
from core.models import Semester


class ProgramViewSet(viewsets.ModelViewSet):
    """
    ViewSet for programs.
    """
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'summary']
    ordering_fields = ['title', 'id']
    ordering = ['title']

    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Get all courses for this program."""
        program = self.get_object()
        courses = Course.objects.filter(program=program).order_by('-year', 'semester')
        serializer = CourseSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for courses.
    """
    queryset = Course.objects.select_related('program').all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['program', 'level', 'year', 'semester', 'is_elective']
    search_fields = ['title', 'code', 'summary']
    ordering_fields = ['title', 'code', 'year', 'semester']
    ordering = ['program', 'year', 'semester']
    lookup_field = 'slug'

    @action(detail=True, methods=['get'])
    def documentation(self, request, slug=None):
        """Get all uploaded files for this course."""
        course = self.get_object()
        files = Upload.objects.filter(course=course)
        serializer = UploadSerializer(files, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def videos(self, request, slug=None):
        """Get all videos for this course."""
        course = self.get_object()
        videos = UploadVideo.objects.filter(course=course)
        serializer = UploadVideoSerializer(videos, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lecturers(self, request, slug=None):
        """Get lecturers allocated to this course."""
        course = self.get_object()
        allocations = CourseAllocation.objects.filter(courses=course)
        serializer = CourseAllocationSerializer(allocations, many=True, context={'request': request})
        return Response(serializer.data)


class CourseAllocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for course allocations.
    """
    queryset = CourseAllocation.objects.select_related('lecturer', 'session').prefetch_related('courses').all()
    serializer_class = CourseAllocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lecturer', 'session']
    search_fields = ['lecturer__first_name', 'lecturer__last_name', 'courses__title']
    ordering_fields = ['id', 'lecturer__first_name']
    ordering = ['lecturer__first_name']

    @action(detail=True, methods=['post'])
    def deallocate(self, request, pk=None):
        """Remove course allocation."""
        allocation = self.get_object()
        allocation.delete()
        return Response({'detail': 'Course allocation removed successfully.'}, status=status.HTTP_204_NO_CONTENT)


class UploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for course documentation uploads.
    """
    queryset = Upload.objects.select_related('course').all()
    serializer_class = UploadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course']
    search_fields = ['title', 'course__title', 'course__code']
    ordering_fields = ['title', 'upload_time', 'updated_date']
    ordering = ['-upload_time']

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Get download URL for the file."""
        upload = self.get_object()
        return Response({
            'file_url': request.build_absolute_uri(upload.file.url) if upload.file else None,
            'file_extension': upload.get_extension_short(),
            'title': upload.title
        })


class UploadVideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet for course video uploads.
    """
    queryset = UploadVideo.objects.select_related('course').all()
    serializer_class = UploadVideoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course']
    search_fields = ['title', 'summary', 'course__title', 'course__code']
    ordering_fields = ['title', 'timestamp']
    ordering = ['-timestamp']
    lookup_field = 'slug'


class CourseRegistrationViewSet(viewsets.ViewSet):
    """
    ViewSet for student course registration.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def available_courses(self, request):
        """Get available courses for the current student."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            return Response(
                {'detail': 'No active semester found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get already taken courses
        taken_courses = TakenCourse.objects.filter(student=student)
        taken_course_ids = [tc.course.id for tc in taken_courses]

        # Get available courses
        available_courses = Course.objects.filter(
            program=student.program,
            level=student.level,
            semester=current_semester.semester
        ).exclude(id__in=taken_course_ids).order_by('year', 'code')

        serializer = CourseSerializer(available_courses, many=True, context={'request': request})
        return Response({
            'semester': current_semester.semester,
            'available_courses': serializer.data,
            'total_courses': available_courses.count()
        })

    @action(detail=False, methods=['get'])
    def registered_courses(self, request):
        """Get courses the current student has registered for."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        taken_courses = TakenCourse.objects.filter(student=student).select_related('course')
        registered_course_ids = [tc.course.id for tc in taken_courses]
        registered_courses = Course.objects.filter(id__in=registered_course_ids, level=student.level)

        serializer = CourseSerializer(registered_courses, many=True, context={'request': request})

        # Calculate total credits
        total_credits = sum(course.credit for course in registered_courses)

        return Response({
            'registered_courses': serializer.data,
            'total_courses': registered_courses.count(),
            'total_credits': total_credits
        })

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register for courses."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            course_ids = serializer.validated_data['course_ids']

            registered_count = 0
            for course_id in course_ids:
                try:
                    course = Course.objects.get(pk=course_id)
                    TakenCourse.objects.create(student=student, course=course)
                    registered_count += 1
                except Course.DoesNotExist:
                    pass

            return Response({
                'detail': f'Successfully registered for {registered_count} course(s).',
                'registered_count': registered_count
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def drop(self, request):
        """Drop courses."""
        try:
            student = get_object_or_404(Student, student__id=request.user.id)
        except:
            return Response(
                {'detail': 'Student profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseDropSerializer(data=request.data)
        if serializer.is_valid():
            course_ids = serializer.validated_data['course_ids']

            dropped_count = 0
            for course_id in course_ids:
                try:
                    course = Course.objects.get(pk=course_id)
                    deleted_count, _ = TakenCourse.objects.filter(student=student, course=course).delete()
                    if deleted_count > 0:
                        dropped_count += 1
                except Course.DoesNotExist:
                    pass

            return Response({
                'detail': f'Successfully dropped {dropped_count} course(s).',
                'dropped_count': dropped_count
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
