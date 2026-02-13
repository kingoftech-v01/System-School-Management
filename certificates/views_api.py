"""
Views for certificates app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    CertificateTemplate, Certificate, CertificateVerification,
    BatchCertificateGeneration
)
from .serializers import (
    CertificateTemplateSerializer, CertificateSerializer,
    CertificateVerificationSerializer, BatchCertificateGenerationSerializer,
    PublicCertificateVerificationSerializer
)
from .permissions import (
    CanIssueCertificates, CanVerifyCertificates, CanRevokeCertificates,
    IsStudentOrStaffReadOnly, CanManageTemplates
)


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for certificate templates.
    """
    queryset = CertificateTemplate.objects.all()
    serializer_class = CertificateTemplateSerializer
    permission_classes = [CanManageTemplates]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['certificate_type', 'is_active', 'is_default']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanIssueCertificates])
    def set_default(self, request, pk=None):
        """Set template as default for its certificate type."""
        template = self.get_object()

        # Remove default from all templates of same type
        CertificateTemplate.objects.filter(
            certificate_type=template.certificate_type,
            is_default=True
        ).update(is_default=False)

        # Set this template as default
        template.is_default = True
        template.save()

        return Response({'detail': 'Template set as default successfully.'})


class CertificateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for certificates.
    """
    queryset = Certificate.objects.select_related(
        'student', 'course', 'template'
    ).all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsStudentOrStaffReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'template', 'is_revoked', 'issue_date']
    search_fields = ['certificate_number', 'student__student__first_name',
                    'student__student__last_name', 'course__name']
    ordering_fields = ['issue_date', 'created_at']
    ordering = ['-issue_date']

    def get_queryset(self):
        """Filter certificates based on user role."""
        user = self.request.user

        # Staff can see all certificates
        if user.is_staff:
            return self.queryset

        # Students can only see their own certificates
        return self.queryset.filter(student__student=user)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def verify(self, request, pk=None):
        """Verify certificate authenticity."""
        certificate = self.get_object()

        # Check if revoked
        if certificate.is_revoked:
            return Response({
                'valid': False,
                'reason': 'Certificate has been revoked',
                'revoked_at': certificate.revoked_at,
                'revocation_reason': certificate.revocation_reason
            }, status=status.HTTP_200_OK)

        # Verify hash signature
        calculated_hash = certificate.calculate_hash()
        if certificate.hash_signature != calculated_hash:
            return Response({
                'valid': False,
                'reason': 'Certificate signature mismatch - possible tampering'
            }, status=status.HTTP_200_OK)

        # Record verification
        CertificateVerification.objects.create(
            certificate=certificate,
            verified_by=request.user.get_full_name if request.user.is_authenticated else 'Anonymous',
            verification_method='api',
            is_valid=True
        )

        return Response({
            'valid': True,
            'certificate_number': certificate.certificate_number,
            'student_name': certificate.student.student.get_full_name,
            'course_name': certificate.course.name,
            'issue_date': certificate.issue_date,
            'grade': certificate.grade,
            'honors': certificate.honors
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def verify_by_number(self, request):
        """Verify certificate by certificate number (public endpoint)."""
        serializer = PublicCertificateVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cert_number = serializer.validated_data['certificate_number']

        try:
            certificate = Certificate.objects.get(certificate_number=cert_number)
        except Certificate.DoesNotExist:
            return Response({
                'valid': False,
                'reason': 'Certificate not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if revoked
        if certificate.is_revoked:
            return Response({
                'valid': False,
                'reason': 'Certificate has been revoked',
                'revoked_at': certificate.revoked_at
            }, status=status.HTTP_200_OK)

        # Record verification
        CertificateVerification.objects.create(
            certificate=certificate,
            verified_by=request.user.get_full_name if request.user.is_authenticated else 'Anonymous',
            verification_method='certificate_number',
            is_valid=True
        )

        return Response({
            'valid': True,
            'certificate_number': certificate.certificate_number,
            'student_name': certificate.student.student.get_full_name,
            'course_name': certificate.course.name,
            'issue_date': certificate.issue_date
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanRevokeCertificates])
    def revoke(self, request, pk=None):
        """Revoke a certificate."""
        certificate = self.get_object()

        if certificate.is_revoked:
            return Response(
                {'detail': 'Certificate is already revoked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        certificate.is_revoked = True
        from django.utils import timezone
        certificate.revoked_at = timezone.now()
        certificate.revocation_reason = request.data.get('reason', 'No reason provided')
        certificate.save()

        return Response({
            'detail': 'Certificate revoked successfully.',
            'certificate_number': certificate.certificate_number
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanRevokeCertificates])
    def unrevoke(self, request, pk=None):
        """Unrevoke a certificate."""
        certificate = self.get_object()

        if not certificate.is_revoked:
            return Response(
                {'detail': 'Certificate is not revoked.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        certificate.is_revoked = False
        certificate.revoked_at = None
        certificate.revocation_reason = ''
        certificate.save()

        return Response({
            'detail': 'Certificate unrevoked successfully.',
            'certificate_number': certificate.certificate_number
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate PDF."""
        certificate = self.get_object()

        # Check permission (staff or own certificate)
        if not request.user.is_staff and certificate.student.student != request.user:
            return Response(
                {'detail': 'You do not have permission to download this certificate.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not certificate.certificate_file:
            return Response(
                {'detail': 'Certificate file not available.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return file
        response = FileResponse(
            certificate.certificate_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{certificate.certificate_number}.pdf"'
        return response


class CertificateVerificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for certificate verification records (read-only).
    """
    queryset = CertificateVerification.objects.select_related('certificate').all()
    serializer_class = CertificateVerificationSerializer
    permission_classes = [IsAuthenticated, CanIssueCertificates]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['certificate', 'verification_method', 'is_valid']
    ordering_fields = ['verified_at']
    ordering = ['-verified_at']


class BatchCertificateGenerationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for batch certificate generation.
    """
    queryset = BatchCertificateGeneration.objects.select_related(
        'course', 'template', 'created_by'
    ).all()
    serializer_class = BatchCertificateGenerationSerializer
    permission_classes = [IsAuthenticated, CanIssueCertificates]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def start_generation(self, request, pk=None):
        """Start batch certificate generation (triggers Celery task)."""
        batch = self.get_object()

        if batch.status != 'pending':
            return Response(
                {'detail': f'Batch is already {batch.status}.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        batch.status = 'processing'
        from django.utils import timezone
        batch.started_at = timezone.now()
        batch.save()

        # Trigger Celery task (to be implemented)
        # from .tasks import generate_batch_certificates
        # generate_batch_certificates.delay(batch.id)

        return Response({
            'detail': 'Batch generation started.',
            'batch_id': batch.id,
            'status': batch.status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get batch generation progress."""
        batch = self.get_object()

        progress_percentage = 0
        if batch.total_students > 0:
            progress_percentage = (batch.processed_count / batch.total_students) * 100

        return Response({
            'batch_id': batch.id,
            'status': batch.status,
            'total_students': batch.total_students,
            'processed_count': batch.processed_count,
            'success_count': batch.success_count,
            'failed_count': batch.failed_count,
            'progress_percentage': round(progress_percentage, 2)
        }, status=status.HTTP_200_OK)
