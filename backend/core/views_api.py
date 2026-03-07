"""
Core App API Views - DRF ViewSets for core models.

This module provides API endpoints for:
- Academic sessions management
- Semester management
- News and events
- Activity logs

API URL namespace: api:v1:core:resource-name
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import Session, Semester, NewsAndEvents, ActivityLog
from .serializers import (
    SessionSerializer, SemesterSerializer,
    NewsAndEventsSerializer, ActivityLogSerializer
)


class SessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for academic sessions.
    """
    queryset = Session.objects.all().order_by('-is_current_session', '-session')
    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_current_session']
    search_fields = ['session']
    ordering_fields = ['session', 'is_current_session']
    ordering = ['-is_current_session', '-session']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current session."""
        current_session = Session.objects.filter(is_current_session=True).first()
        if not current_session:
            return Response(
                {'detail': 'No current session set.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(current_session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this session as current."""
        session = self.get_object()

        # Unset all other current sessions
        Session.objects.filter(is_current_session=True).update(is_current_session=False)

        # Set this as current
        session.is_current_session = True
        session.save()

        return Response({'detail': 'Session set as current successfully.'})


class SemesterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for academic semesters.
    """
    queryset = Semester.objects.select_related('session').all().order_by('-is_current_semester', '-semester')
    serializer_class = SemesterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_current_semester', 'session']
    search_fields = ['semester']
    ordering_fields = ['semester', 'is_current_semester']
    ordering = ['-is_current_semester', '-semester']

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current semester."""
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            return Response(
                {'detail': 'No current semester set.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(current_semester)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this semester as current."""
        semester = self.get_object()

        # Unset all other current semesters
        Semester.objects.filter(is_current_semester=True).update(is_current_semester=False)

        # Also set the session as current
        if semester.session:
            Session.objects.filter(is_current_session=True).update(is_current_session=False)
            semester.session.is_current_session = True
            semester.session.save()

        # Set this as current
        semester.is_current_semester = True
        semester.save()

        return Response({'detail': 'Semester set as current successfully.'})


class NewsAndEventsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for news and events.
    """
    queryset = NewsAndEvents.objects.all().order_by('-updated_date')
    serializer_class = NewsAndEventsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['posted_as']
    search_fields = ['title', 'summary']
    ordering_fields = ['updated_date', 'upload_time', 'title']
    ordering = ['-updated_date']

    @action(detail=False, methods=['get'])
    def news(self, request):
        """Get only news posts."""
        news_posts = self.queryset.filter(posted_as='News')
        serializer = self.get_serializer(news_posts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def events(self, request):
        """Get only events."""
        events = self.queryset.filter(posted_as='Event')
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for activity logs (read-only).
    """
    queryset = ActivityLog.objects.all().order_by('-created_at')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
