from django.db.models import Count
from django.utils import timezone
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Incident, IncidentAttachment, VisitorLog, StudentCaseNote
from .serializers import (
    IncidentAttachmentSerializer,
    IncidentCreateSerializer,
    IncidentDetailSerializer,
    IncidentListSerializer,
    StudentCaseNoteCreateSerializer,
    StudentCaseNoteDetailSerializer,
    StudentCaseNoteListSerializer,
    VisitorLogCreateSerializer,
    VisitorLogDetailSerializer,
    VisitorLogListSerializer,
)


class IncidentViewSet(viewsets.ModelViewSet):
    """CRUD for incidents with close and stats actions."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['incident_date', 'created_at', 'severity']
    ordering = ['-incident_date']

    def get_queryset(self):
        qs = Incident.objects.select_related(
            'reported_by', 'updated_by'
        ).prefetch_related(
            'students_involved', 'staff_involved', 'attachments'
        )
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)

        incident_type = self.request.query_params.get('incident_type')
        if incident_type:
            qs = qs.filter(incident_type=incident_type)
        severity = self.request.query_params.get('severity')
        if severity:
            qs = qs.filter(severity=severity)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return IncidentListSerializer
        elif self.action == 'create':
            return IncidentCreateSerializer
        return IncidentDetailSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant, reported_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        incident = self.get_object()
        resolution = request.data.get('resolution', '')
        incident.status = 'closed'
        incident.resolution = resolution
        incident.updated_by = request.user
        incident.save(update_fields=[
            'status', 'resolution', 'updated_by', 'updated_at',
        ])
        return Response(IncidentDetailSerializer(incident).data)

    @action(
        detail=True, methods=['post'],
        serializer_class=IncidentAttachmentSerializer,
    )
    def upload_attachment(self, request, pk=None):
        incident = self.get_object()
        serializer = IncidentAttachmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(incident=incident, uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        qs = self.get_queryset()
        return Response({
            'total': qs.count(),
            'open': qs.filter(status='open').count(),
            'investigating': qs.filter(status='investigating').count(),
            'closed': qs.filter(status='closed').count(),
            'by_type': list(
                qs.values('incident_type').annotate(count=Count('id'))
            ),
            'by_severity': list(
                qs.values('severity').annotate(count=Count('id'))
            ),
        })


class VisitorLogViewSet(viewsets.ModelViewSet):
    """CRUD for visitor logs with checkout and on_site actions."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['visitor_name', 'organization', 'purpose']
    ordering = ['-time_in']

    def get_queryset(self):
        qs = VisitorLog.objects.select_related(
            'host_staff', 'logged_by', 'approved_by'
        )
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)

        visitor_type = self.request.query_params.get('visitor_type')
        if visitor_type:
            qs = qs.filter(visitor_type=visitor_type)

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return VisitorLogListSerializer
        elif self.action == 'create':
            return VisitorLogCreateSerializer
        return VisitorLogDetailSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant, logged_by=self.request.user)

    @action(detail=True, methods=['post'])
    def checkout(self, request, pk=None):
        visitor = self.get_object()
        if visitor.time_out:
            return Response(
                {'error': 'Visitor already checked out.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        visitor.time_out = timezone.now()
        notes = request.data.get('notes', '')
        if notes:
            existing = visitor.notes or ''
            visitor.notes = (existing + '\n' + notes).strip()
        visitor.save(update_fields=['time_out', 'notes', 'updated_at'])
        return Response(VisitorLogDetailSerializer(visitor).data)

    @action(detail=False, methods=['get'])
    def on_site(self, request):
        """List visitors currently on site (no time_out)."""
        qs = self.get_queryset().filter(time_out__isnull=True)
        serializer = VisitorLogListSerializer(qs, many=True)
        return Response(serializer.data)


class StudentCaseNoteViewSet(viewsets.ModelViewSet):
    """CRUD for student case notes with confidentiality filtering."""

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = StudentCaseNote.objects.select_related(
            'student__student', 'created_by'
        )
        tenant = getattr(self.request, 'tenant', None)
        if tenant:
            qs = qs.filter(tenant=tenant)

        user = self.request.user
        if user.has_perm('safeguarding.view_highly_restricted_notes'):
            pass
        elif user.has_perm('safeguarding.view_restricted_notes'):
            qs = qs.exclude(confidentiality='highly_restricted')
        else:
            qs = qs.filter(confidentiality='standard')

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        student_id = self.request.query_params.get('student')
        if student_id:
            qs = qs.filter(student_id=student_id)

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return StudentCaseNoteListSerializer
        elif self.action == 'create':
            return StudentCaseNoteCreateSerializer
        return StudentCaseNoteDetailSerializer

    def perform_create(self, serializer):
        tenant = getattr(self.request, 'tenant', None)
        serializer.save(tenant=tenant, created_by=self.request.user)
