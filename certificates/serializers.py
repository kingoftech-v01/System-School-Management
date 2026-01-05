"""
Serializers for certificates app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CertificateTemplate, Certificate, CertificateVerification, BatchCertificateGeneration

User = get_user_model()


class CertificateTemplateSerializer(serializers.ModelSerializer):
    """Serializer for certificate templates."""
    class Meta:
        model = CertificateTemplate
        fields = ['id', 'name', 'description', 'certificate_type', 'template_file',
                 'background_image', 'logo', 'signature_image', 'signatory_name',
                 'signatory_title', 'is_active', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Ensure only one default template per type."""
        if data.get('is_default'):
            cert_type = data.get('certificate_type')
            existing_default = CertificateTemplate.objects.filter(
                certificate_type=cert_type,
                is_default=True
            ).exclude(id=self.instance.id if self.instance else None)

            if existing_default.exists():
                raise serializers.ValidationError(
                    f"A default template already exists for {cert_type} certificates."
                )
        return data


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for certificates."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    verification_count = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ['id', 'student', 'student_name', 'course', 'course_name',
                 'template', 'template_name', 'certificate_number', 'issue_date',
                 'grade', 'honors', 'additional_info', 'certificate_file',
                 'hash_signature', 'blockchain_hash', 'qr_code', 'is_revoked',
                 'revoked_at', 'revocation_reason', 'verification_count',
                 'is_valid', 'created_at', 'updated_at']
        read_only_fields = ['certificate_number', 'hash_signature', 'blockchain_hash',
                           'qr_code', 'created_at', 'updated_at', 'revoked_at']

    def get_verification_count(self, obj):
        return obj.verifications.count()

    def get_is_valid(self, obj):
        return not obj.is_revoked

    def create(self, validated_data):
        """Create certificate with auto-generated fields."""
        certificate = Certificate.objects.create(**validated_data)

        # Generate certificate number
        certificate.certificate_number = certificate.generate_certificate_number()

        # Generate hash signature
        certificate.hash_signature = certificate.calculate_hash()

        certificate.save()
        return certificate


class CertificateVerificationSerializer(serializers.ModelSerializer):
    """Serializer for certificate verifications."""
    certificate_number = serializers.CharField(source='certificate.certificate_number', read_only=True)
    student_name = serializers.CharField(source='certificate.student.student.get_full_name', read_only=True)

    class Meta:
        model = CertificateVerification
        fields = ['id', 'certificate', 'certificate_number', 'student_name',
                 'verified_by', 'verification_method', 'is_valid', 'ip_address',
                 'user_agent', 'notes', 'verified_at']
        read_only_fields = ['verified_at']

    def create(self, validated_data):
        """Record verification with IP and user agent from request."""
        request = self.context.get('request')
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                validated_data['ip_address'] = x_forwarded_for.split(',')[0]
            else:
                validated_data['ip_address'] = request.META.get('REMOTE_ADDR')

            # Get user agent
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]

        return CertificateVerification.objects.create(**validated_data)


class BatchCertificateGenerationSerializer(serializers.ModelSerializer):
    """Serializer for batch certificate generation."""
    course_name = serializers.CharField(source='course.name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = BatchCertificateGeneration
        fields = ['id', 'course', 'course_name', 'template', 'template_name',
                 'created_by', 'created_by_name', 'status', 'total_students',
                 'processed_count', 'success_count', 'failed_count',
                 'progress_percentage', 'grade_threshold', 'include_honors_only',
                 'error_log', 'created_at', 'started_at', 'completed_at']
        read_only_fields = ['created_by', 'status', 'total_students', 'processed_count',
                           'success_count', 'failed_count', 'error_log', 'created_at',
                           'started_at', 'completed_at']

    def get_progress_percentage(self, obj):
        if obj.total_students == 0:
            return 0
        return round((obj.processed_count / obj.total_students) * 100, 2)

    def create(self, validated_data):
        """Create batch generation task."""
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['status'] = 'pending'
        return BatchCertificateGeneration.objects.create(**validated_data)


class PublicCertificateVerificationSerializer(serializers.Serializer):
    """Serializer for public certificate verification (by number)."""
    certificate_number = serializers.CharField(max_length=100)

    def validate_certificate_number(self, value):
        """Check if certificate exists."""
        try:
            certificate = Certificate.objects.get(certificate_number=value)
        except Certificate.DoesNotExist:
            raise serializers.ValidationError("Certificate not found.")
        return value


class CertificateDownloadSerializer(serializers.Serializer):
    """Serializer for certificate download requests."""
    format = serializers.ChoiceField(choices=['pdf', 'png'], default='pdf')
