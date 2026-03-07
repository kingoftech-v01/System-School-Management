"""
Filieres API Views - REST API endpoints.

This module provides API endpoints for:
- Filiere CRUD (academic programs)
- FiliereSubject management
- FiliereRequirement management

All views return JSON responses.
API URL namespace: api:v1:filieres:resource-name
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count, Q

from .models import Filiere, FiliereSubject, FiliereRequirement
from .serializers import (
    FiliereSerializer,
    FiliereListSerializer,
    FiliereCreateSerializer,
    FiliereSubjectSerializer,
    FiliereSubjectCreateSerializer,
    FiliereRequirementSerializer,
    FiliereRequirementCreateSerializer,
)
from accounts.permissions import IsDirectionUser


# ============================================================================
# FILIERE VIEWSET
# ============================================================================

class FiliereViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing filieres (academic programs).

    Features:
    - List filieres with search and filters
    - Create filieres (direction only)
    - Update/delete filieres (direction only)
    - Get filiere details with subjects

    Filtering: level, is_active
    Search: name, code
    Ordering: name, code, created_at
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        """Get filieres with aggregated counts."""
        return Filiere.objects.filter(
            tenant=self.request.tenant
        ).select_related('coordinator').annotate(
            subject_count=Count('subjects'),
            enrolled_count=Count('registrations', filter=Q(registrations__status='enrolled'))
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return FiliereListSerializer
        elif self.action == 'create':
            return FiliereCreateSerializer
        return FiliereSerializer

    def get_permissions(self):
        """Direction only for create/update/delete."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDirectionUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Set tenant when creating filiere."""
        serializer.save(tenant=self.request.tenant)

    def destroy(self, request, *args, **kwargs):
        """Prevent deletion if filiere has enrolled students."""
        filiere = self.get_object()

        enrolled_count = filiere.registrations.filter(status='enrolled').count()
        if enrolled_count > 0:
            return Response(
                {'error': 'Cannot delete filiere with enrolled students. Mark as inactive instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        """Get all subjects for a filiere grouped by year/semester."""
        filiere = self.get_object()
        subjects = filiere.subjects.all().select_related('subject')
        serializer = FiliereSubjectSerializer(subjects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def requirements(self, request, pk=None):
        """Get all admission requirements for a filiere."""
        filiere = self.get_object()
        requirements = filiere.requirements.all()
        serializer = FiliereRequirementSerializer(requirements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active filieres."""
        active_filieres = self.get_queryset().filter(is_active=True)
        page = self.paginate_queryset(active_filieres)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# ============================================================================
# FILIERE SUBJECT VIEWSET
# ============================================================================

class FiliereSubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subjects within filieres.

    Features:
    - List subjects for a filiere
    - Add/remove subjects (direction only)
    - Update subject details (coefficient, year, semester)

    Filtering: filiere, year, semester, is_mandatory
    Ordering: year, semester, order
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['filiere', 'year', 'semester', 'is_mandatory']
    ordering_fields = ['year', 'semester', 'order']
    ordering = ['year', 'semester', 'order']

    def get_queryset(self):
        """Filter subjects by tenant through filiere."""
        return FiliereSubject.objects.filter(
            filiere__tenant=self.request.tenant
        ).select_related('filiere', 'subject')

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return FiliereSubjectCreateSerializer
        return FiliereSubjectSerializer

    def get_permissions(self):
        """Direction only for modifications."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDirectionUser()]
        return [IsAuthenticated()]


# ============================================================================
# FILIERE REQUIREMENT VIEWSET
# ============================================================================

class FiliereRequirementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing filiere admission requirements.

    Features:
    - List requirements for a filiere
    - Add/remove requirements (direction only)

    Filtering: filiere, requirement_type, is_mandatory
    Ordering: created_at
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['filiere', 'requirement_type', 'is_mandatory']
    ordering_fields = ['created_at']
    ordering = ['created_at']

    def get_queryset(self):
        """Filter requirements by tenant through filiere."""
        return FiliereRequirement.objects.filter(
            filiere__tenant=self.request.tenant
        ).select_related('filiere')

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return FiliereRequirementCreateSerializer
        return FiliereRequirementSerializer

    def get_permissions(self):
        """Direction only for modifications."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDirectionUser()]
        return [IsAuthenticated()]
