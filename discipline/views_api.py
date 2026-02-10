"""
Discipline API Views - REST API endpoints.

This module provides REST API views using Django Rest Framework:
- ViewSets for CRUD operations on disciplinary actions
- Filtering, search, and pagination
- Permission-based access control

All views return JSON responses.
API URL namespace: api:v1:discipline:resource-name
"""

from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import DisciplinaryAction
from .serializers import (
    DisciplinaryActionSerializer,
    DisciplinaryActionListSerializer,
    DisciplinaryActionCreateSerializer
)


# ============================================================================
# VIEWSETS
# ============================================================================

class DisciplinaryActionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DisciplinaryAction CRUD operations.

    Provides:
    - list: GET /api/v1/discipline/actions/
    - retrieve: GET /api/v1/discipline/actions/{id}/
    - create: POST /api/v1/discipline/actions/
    - update: PUT /api/v1/discipline/actions/{id}/
    - partial_update: PATCH /api/v1/discipline/actions/{id}/
    - destroy: DELETE /api/v1/discipline/actions/{id}/

    Custom actions:
    - resolve: POST /api/v1/discipline/actions/{id}/resolve/
    - student_history: GET /api/v1/discipline/actions/student_history/?student_id=<id>

    Filtering:
    - ?severity=minor|moderate|serious|critical
    - ?is_resolved=true|false
    - ?student=<student_id>

    Search:
    - ?search=keyword (searches incident_type, description, action_taken)

    Ordering:
    - ?ordering=incident_date
    - ?ordering=-created_at
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['severity', 'is_resolved', 'student', 'reported_by']
    search_fields = ['incident_type', 'description', 'action_taken']
    ordering_fields = ['incident_date', 'created_at', 'severity']
    ordering = ['-incident_date']
    lookup_field = 'pk'

    def get_queryset(self):
        """
        Return queryset based on user permissions and tenant.

        - Direction/Staff: All disciplinary actions for their tenant
        - Students/Parents: Only their own records
        """
        user = self.request.user

        # Filter by tenant
        queryset = DisciplinaryAction.objects.filter(
            tenant=self.request.tenant
        ).select_related('student', 'reported_by', 'updated_by')

        # Filter by permissions
        if user.is_staff or user.is_direction or getattr(user, 'role', '') == 'prefet':
            # Staff, direction, and discipline officers can see all records
            return queryset
        elif user.is_student:
            # Students can only see their own records
            return queryset.filter(student=user)
        elif user.is_parent:
            # Parents can see their children's records
            # Assuming parent has a relationship to students
            return queryset.filter(student__parent=user)
        else:
            # Default: no records
            return queryset.none()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DisciplinaryActionListSerializer
        elif self.action == 'create':
            return DisciplinaryActionCreateSerializer
        return DisciplinaryActionSerializer

    def perform_create(self, serializer):
        """Set tenant and reported_by on create."""
        serializer.save(
            tenant=self.request.tenant,
            reported_by=self.request.user
        )

    def perform_update(self, serializer):
        """Track who updated the record."""
        serializer.save(
            updated_by=self.request.user,
            updated_at=timezone.now()
        )

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Mark a disciplinary action as resolved.

        POST /api/v1/discipline/actions/{id}/resolve/

        Body (optional):
        {
            "resolution_date": "2025-01-25"
        }

        Returns:
            200: Action resolved successfully
            403: No permission
            404: Action not found
        """
        action = self.get_object()

        # Permission check (only staff/direction/discipline officer)
        if not (request.user.is_staff or request.user.is_direction or getattr(request.user, 'role', '') == 'prefet'):
            return Response(
                {'error': 'Only staff, direction, and discipline officers can resolve disciplinary actions'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get resolution date from request or use today
        resolution_date = request.data.get('resolution_date', timezone.now().date())

        action.is_resolved = True
        action.resolution_date = resolution_date
        action.updated_by = request.user
        action.save(update_fields=['is_resolved', 'resolution_date', 'updated_by', 'updated_at'])

        serializer = self.get_serializer(action)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def student_history(self, request):
        """
        Get disciplinary history for a specific student.

        GET /api/v1/discipline/actions/student_history/?student_id=<id>

        Returns:
            200: List of disciplinary actions for the student
            400: Missing student_id parameter
        """
        student_id = request.query_params.get('student_id')

        if not student_id:
            return Response(
                {'error': 'student_id query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter by student
        queryset = self.get_queryset().filter(student_id=student_id)

        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = DisciplinaryActionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = DisciplinaryActionListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get overall statistics for disciplinary actions.

        GET /api/v1/discipline/actions/stats/

        Returns:
            200: Statistics object with counts by severity, resolution status
        """
        from django.db.models import Count

        queryset = self.get_queryset()

        stats = {
            'total_count': queryset.count(),
            'resolved_count': queryset.filter(is_resolved=True).count(),
            'pending_count': queryset.filter(is_resolved=False).count(),
            'by_severity': list(
                queryset.values('severity')
                .annotate(count=Count('id'))
                .order_by('severity')
            ),
        }

        return Response(stats)
