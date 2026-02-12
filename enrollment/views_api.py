"""
Enrollment API Views - REST API endpoints.

This module provides API endpoints for:
- Student registration (public and authenticated)
- Registration review and approval
- Document upload and verification
- Enrollment status tracking

All views return JSON responses.
API URL namespace: api:v1:enrollment:resource-name
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.utils import timezone

from .models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory
from .serializers import (
    RegistrationFormSerializer,
    RegistrationFormListSerializer,
    RegistrationFormCreateSerializer,
    RegistrationReviewSerializer,
    EnrollmentDocumentSerializer,
    EnrollmentDocumentUploadSerializer,
    DocumentVerificationSerializer,
    EnrollmentStatusHistorySerializer,
)
from accounts.permissions import IsDirectionUser


# ============================================================================
# REGISTRATION FORM VIEWSET
# ============================================================================

class RegistrationFormViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing registration forms.

    Features:
    - Public registration (POST without auth)
    - List registrations (direction only)
    - Review and approve applications (direction only)
    - Update registration status

    Filtering: status, enrollment_type, filiere, academic_year
    Search: student_name, email
    Ordering: created_at, student_name
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'enrollment_type', 'filiere', 'academic_year']
    search_fields = ['student_name', 'email', 'parent_name']
    ordering_fields = ['created_at', 'student_name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Direction sees all, others see their own."""
        queryset = RegistrationForm.objects.all().select_related(
            'filiere', 'reviewed_by', 'tenant'
        )

        # Filter by tenant if available
        if hasattr(self.request, 'tenant'):
            queryset = queryset.filter(tenant=self.request.tenant)

        # Non-direction users can only see their own registration
        if self.request.user.is_authenticated:
            user = self.request.user
            if not (hasattr(user, 'role') and user.role in ('direction', 'admin', 'secretary')):
                # Filter by user FK where available, fall back to email
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(enrolled_user=user) | Q(email=user.email)
                )

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return RegistrationFormListSerializer
        elif self.action == 'create':
            return RegistrationFormCreateSerializer
        elif self.action == 'review':
            return RegistrationReviewSerializer
        return RegistrationFormSerializer

    def get_permissions(self):
        """Allow public registration, require direction for review."""
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['review', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDirectionUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Set tenant when creating registration."""
        if hasattr(self.request, 'tenant'):
            serializer.save(tenant=self.request.tenant)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirectionUser])
    def review(self, request, pk=None):
        """Review and update registration status."""
        registration = self.get_object()
        old_status = registration.status

        serializer = RegistrationReviewSerializer(registration, data=request.data, partial=True)

        if serializer.is_valid():
            new_status = serializer.validated_data.get('status', registration.status)

            registration = serializer.save(reviewed_by=request.user)

            # Create history record
            EnrollmentStatusHistory.objects.create(
                registration=registration,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                notes=serializer.validated_data.get('review_notes', '')
            )

            # Send notification email (via Celery task)
            from .tasks import send_enrollment_status_email
            send_enrollment_status_email.delay(registration.id, new_status)

            return Response(RegistrationFormSerializer(registration).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsDirectionUser])
    def pending(self, request):
        """Get registrations pending review."""
        pending_registrations = self.get_queryset().filter(status='pending')
        page = self.paginate_queryset(pending_registrations)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsDirectionUser])
    def statistics(self, request):
        """Get enrollment statistics."""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'by_status': {},
            'by_enrollment_type': {},
            'by_filiere': {},
        }

        # Status breakdown
        for status_choice in RegistrationForm.STATUS_CHOICES:
            status_code = status_choice[0]
            stats['by_status'][status_code] = queryset.filter(status=status_code).count()

        # Enrollment type breakdown
        for type_choice in RegistrationForm.ENROLLMENT_TYPE_CHOICES:
            type_code = type_choice[0]
            stats['by_enrollment_type'][type_code] = queryset.filter(enrollment_type=type_code).count()

        return Response(stats)


# ============================================================================
# ENROLLMENT DOCUMENT VIEWSET
# ============================================================================

class EnrollmentDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing enrollment documents.

    Features:
    - Upload documents
    - Verify documents (direction only)
    - List documents for a registration

    Filtering: registration, document_type, is_verified
    Ordering: uploaded_at
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['registration', 'document_type', 'is_verified']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        """Filter documents based on user role."""
        queryset = EnrollmentDocument.objects.all().select_related(
            'registration', 'verified_by'
        )

        # Filter by tenant through registration
        if hasattr(self.request, 'tenant'):
            queryset = queryset.filter(registration__tenant=self.request.tenant)

        # Non-direction users can only see their own documents
        user = self.request.user
        if not (hasattr(user, 'role') and user.role in ('direction', 'admin', 'secretary')):
            from django.db.models import Q
            queryset = queryset.filter(
                Q(registration__enrolled_user=user) | Q(registration__email=user.email)
            )

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return EnrollmentDocumentUploadSerializer
        elif self.action == 'verify':
            return DocumentVerificationSerializer
        return EnrollmentDocumentSerializer

    def get_permissions(self):
        """Direction only for verification."""
        if self.action in ['verify', 'destroy']:
            return [IsAuthenticated(), IsDirectionUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsDirectionUser])
    def verify(self, request, pk=None):
        """Verify a document."""
        document = self.get_object()

        serializer = DocumentVerificationSerializer(document, data=request.data, partial=True)

        if serializer.is_valid():
            document = serializer.save(
                verified_by=request.user,
                verified_at=timezone.now() if serializer.validated_data.get('is_verified') else None
            )

            return Response(EnrollmentDocumentSerializer(document, context={'request': request}).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# ENROLLMENT STATUS HISTORY VIEWSET
# ============================================================================

class EnrollmentStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for enrollment status history.

    Features:
    - List status changes
    - Get history for a specific registration

    Filtering: registration
    Ordering: changed_at
    """
    queryset = EnrollmentStatusHistory.objects.all()
    serializer_class = EnrollmentStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['registration']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']

    def get_queryset(self):
        """Filter history by tenant and user role."""
        queryset = EnrollmentStatusHistory.objects.all().select_related(
            'registration', 'changed_by'
        )

        # Filter by tenant through registration
        if hasattr(self.request, 'tenant'):
            queryset = queryset.filter(registration__tenant=self.request.tenant)

        # Non-direction users can only see history for their own registration
        user = self.request.user
        if not (hasattr(user, 'role') and user.role in ('direction', 'admin', 'secretary')):
            from django.db.models import Q
            queryset = queryset.filter(
                Q(registration__enrolled_user=user) | Q(registration__email=user.email)
            )

        return queryset
