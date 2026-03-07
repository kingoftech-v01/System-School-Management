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
        fields = ['id', 'name', 'description', 'template_file',
                 'background_image', 'title_text', 'body_template',
                 'signature_1_name', 'signature_1_title', 'signature_1_image',
                 'signature_2_name', 'signature_2_title', 'signature_2_image',
                 'orientation', 'page_size', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for certificates."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.title', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    verification_count = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ['id', 'student', 'student_name', 'course', 'course_name',
                 'template', 'template_name', 'certificate_number', 'issue_date',
                 'completion_date', 'grade', 'gpa', 'credits', 'pdf_file',
                 'hash_signature', 'blockchain_hash', 'qr_code', 'status',
                 'is_revoked', 'revoked_at', 'revocation_reason',
                 'verification_count', 'is_valid', 'created_at', 'updated_at']
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
                 'verified_by_user', 'verification_method', 'is_valid', 'ip_address',
                 'user_agent', 'verification_notes', 'verified_at']
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
    course_name = serializers.CharField(source='course.title', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    initiated_by_name = serializers.CharField(source='initiated_by.get_full_name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = BatchCertificateGeneration
        fields = ['id', 'course', 'course_name', 'template', 'template_name',
                 'initiated_by', 'initiated_by_name', 'status', 'total_students',
                 'processed_count', 'success_count', 'failure_count',
                 'progress_percentage', 'min_grade', 'min_gpa',
                 'error_log', 'created_at', 'started_at', 'completed_at']
        read_only_fields = ['initiated_by', 'status', 'total_students', 'processed_count',
                           'success_count', 'failure_count', 'error_log', 'created_at',
                           'started_at', 'completed_at']

    def get_progress_percentage(self, obj):
        if obj.total_students == 0:
            return 0
        return round((obj.processed_count / obj.total_students) * 100, 2)

    def create(self, validated_data):
        """Create batch generation task."""
        request = self.context.get('request')
        validated_data['initiated_by'] = request.user
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
