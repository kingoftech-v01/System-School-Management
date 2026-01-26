"""
Enrollment Serializers - DRF serializers for student enrollment API.

This module provides serializers for:
- RegistrationForm model (student enrollment applications)
- EnrollmentDocument model (document uploads)
- EnrollmentStatusHistory model (status change tracking)
"""

from rest_framework import serializers
from .models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory


# ============================================================================
# REGISTRATION FORM SERIALIZERS
# ============================================================================

class RegistrationFormSerializer(serializers.ModelSerializer):
    """
    Full serializer for registration forms.
    """
    filiere_name = serializers.CharField(source='filiere.name', read_only=True, allow_null=True)
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name',
        read_only=True,
        allow_null=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    enrollment_type_display = serializers.CharField(source='get_enrollment_type_display', read_only=True)
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = RegistrationForm
        fields = [
            'id', 'tenant', 'student_name', 'date_of_birth', 'gender', 'gender_display',
            'nationality', 'email', 'phone', 'address', 'parent_name', 'parent_email',
            'parent_phone', 'parent_relationship', 'filiere', 'filiere_name',
            'academic_year', 'level', 'previous_school', 'enrollment_type',
            'enrollment_type_display', 'status', 'status_display', 'reviewed_by',
            'reviewed_by_name', 'review_notes', 'rejection_reason', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['tenant', 'reviewed_by', 'created_at', 'updated_at']


class RegistrationFormListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing registration forms.
    """
    filiere_name = serializers.CharField(source='filiere.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = RegistrationForm
        fields = [
            'id', 'student_name', 'email', 'filiere_name', 'academic_year',
            'status', 'status_display', 'enrollment_type', 'created_at'
        ]


class RegistrationFormCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating registration forms (public registration).
    """
    class Meta:
        model = RegistrationForm
        fields = [
            'student_name', 'date_of_birth', 'gender', 'nationality', 'email',
            'phone', 'address', 'parent_name', 'parent_email', 'parent_phone',
            'parent_relationship', 'filiere', 'academic_year', 'level',
            'previous_school', 'enrollment_type'
        ]

    def validate_email(self, value):
        """Ensure email is unique and valid."""
        if RegistrationForm.objects.filter(email=value, status='enrolled').exists():
            raise serializers.ValidationError('A student with this email is already enrolled.')
        return value.lower()


class RegistrationReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviewing registration applications (direction only).
    """
    class Meta:
        model = RegistrationForm
        fields = ['status', 'review_notes', 'rejection_reason']

    def validate_status(self, value):
        """Ensure status is valid for review."""
        allowed_statuses = ['under_review', 'approved', 'rejected', 'enrolled']
        if value not in allowed_statuses:
            raise serializers.ValidationError(
                f'Status must be one of: {", ".join(allowed_statuses)}'
            )
        return value

    def validate(self, data):
        """Ensure rejection reason is provided when rejecting."""
        if data.get('status') == 'rejected' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting an application.'
            })
        return data


# ============================================================================
# ENROLLMENT DOCUMENT SERIALIZERS
# ============================================================================

class EnrollmentDocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for enrollment documents.
    """
    registration_student_name = serializers.CharField(
        source='registration.student_name',
        read_only=True
    )
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    file_url = serializers.SerializerMethodField()
    verified_by_name = serializers.CharField(
        source='verified_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = EnrollmentDocument
        fields = [
            'id', 'registration', 'registration_student_name', 'document_type',
            'document_type_display', 'file', 'file_url', 'file_name', 'file_size',
            'is_verified', 'verified_by', 'verified_by_name', 'verified_at',
            'verification_notes', 'uploaded_at'
        ]
        read_only_fields = ['verified_by', 'verified_at', 'uploaded_at', 'file_size']

    def get_file_url(self, obj):
        """Return absolute URL for the document file."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class EnrollmentDocumentUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for uploading documents.
    """
    class Meta:
        model = EnrollmentDocument
        fields = ['registration', 'document_type', 'file']

    def validate_file(self, value):
        """Validate file size and extension."""
        # Max 5MB
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('File size cannot exceed 5MB.')

        # Allowed extensions
        allowed_extensions = ['pdf', 'jpg', 'jpeg', 'png']
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'
            )

        return value


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """
    Serializer for document verification (direction only).
    """
    class Meta:
        model = EnrollmentDocument
        fields = ['is_verified', 'verification_notes']


# ============================================================================
# ENROLLMENT STATUS HISTORY SERIALIZERS
# ============================================================================

class EnrollmentStatusHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for enrollment status history.
    """
    registration_student_name = serializers.CharField(
        source='registration.student_name',
        read_only=True
    )
    changed_by_name = serializers.CharField(
        source='changed_by.get_full_name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = EnrollmentStatusHistory
        fields = [
            'id', 'registration', 'registration_student_name', 'old_status',
            'new_status', 'changed_by', 'changed_by_name', 'changed_at',
            'notes'
        ]
        read_only_fields = ['changed_by', 'changed_at']
