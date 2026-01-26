"""
Events API Views - REST API endpoints.

This module provides REST API views using Django Rest Framework:
- ViewSets for CRUD operations on events
- Filtering by event type, target audience, date range
- Permission-based access control

All views return JSON responses.
API URL namespace: api:v1:events:resource-name
"""

from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Event
from .serializers import (
    EventSerializer,
    EventListSerializer,
    EventCreateSerializer
)


# ============================================================================
# VIEWSETS
# ============================================================================

class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Event CRUD operations.

    Provides:
    - list: GET /api/v1/events/events/
    - retrieve: GET /api/v1/events/events/{id}/
    - create: POST /api/v1/events/events/
    - update: PUT /api/v1/events/events/{id}/
    - partial_update: PATCH /api/v1/events/events/{id}/
    - destroy: DELETE /api/v1/events/events/{id}/

    Custom actions:
    - upcoming: GET /api/v1/events/events/upcoming/
    - calendar: GET /api/v1/events/events/calendar/?month=2025-01

    Filtering:
    - ?event_type=exam|holiday|meeting|activity|ceremony|deadline
    - ?target_audience=all|students|parents|staff
    - ?start_date__gte=2025-01-01

    Search:
    - ?search=keyword (searches title, description)

    Ordering:
    - ?ordering=start_date
    - ?ordering=-created_at
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['event_type', 'target_audience', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['start_date']
    lookup_field = 'pk'

    def get_queryset(self):
        """
        Return queryset based on user permissions and tenant.

        Filters by tenant and target audience based on user role.
        """
        user = self.request.user

        # Filter by tenant
        queryset = Event.objects.filter(
            tenant=self.request.tenant
        ).select_related('created_by')

        # Filter by target audience
        if user.is_student:
            queryset = queryset.filter(target_audience__in=['all', 'students'])
        elif user.is_parent:
            queryset = queryset.filter(target_audience__in=['all', 'parents'])
        elif user.is_lecturer or user.is_professor:
            queryset = queryset.filter(target_audience__in=['all', 'staff'])
        # Direction and staff can see all events

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return EventListSerializer
        elif self.action == 'create':
            return EventCreateSerializer
        return EventSerializer

    def perform_create(self, serializer):
        """Set tenant and created_by on create."""
        serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming events (from now onwards).

        GET /api/v1/events/events/upcoming/

        Query Parameters:
        - limit: Maximum events to return (default: 10)

        Returns:
            200: List of upcoming events
        """
        limit = int(request.query_params.get('limit', 10))

        queryset = self.get_queryset().filter(
            start_date__gte=timezone.now()
        ).order_by('start_date')[:limit]

        serializer = EventListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """
        Get events for a specific month (calendar view).

        GET /api/v1/events/events/calendar/?month=2025-01

        Query Parameters:
        - month: Month in YYYY-MM format (required)

        Returns:
            200: Events grouped by day for the month
            400: Missing or invalid month parameter
        """
        month_str = request.query_params.get('month')

        if not month_str:
            return Response(
                {'error': 'month parameter is required (format: YYYY-MM)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Parse month
            from datetime import datetime
            month_date = datetime.strptime(month_str, '%Y-%m')

            # Get first and last day of month
            import calendar
            _, last_day = calendar.monthrange(month_date.year, month_date.month)

            month_start = month_date.replace(day=1)
            month_end = month_date.replace(day=last_day, hour=23, minute=59, second=59)

            # Get events in this month
            queryset = self.get_queryset().filter(
                start_date__range=[month_start, month_end]
            ).order_by('start_date')

            serializer = EventListSerializer(queryset, many=True)

            return Response({
                'month': month_str,
                'events': serializer.data
            })

        except ValueError:
            return Response(
                {'error': 'Invalid month format. Use YYYY-MM'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get overall event statistics.

        GET /api/v1/events/events/stats/

        Returns:
            200: Statistics with event counts by type and audience
        """
        from django.db.models import Count

        queryset = self.get_queryset()

        stats = {
            'total_count': queryset.count(),
            'upcoming_count': queryset.filter(start_date__gte=timezone.now()).count(),
            'past_count': queryset.filter(start_date__lt=timezone.now()).count(),
            'by_type': list(
                queryset.values('event_type')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
            'by_audience': list(
                queryset.values('target_audience')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }

        return Response(stats)
