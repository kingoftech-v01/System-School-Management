from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Incident, IncidentAttachment, VisitorLog, StudentCaseNote

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name if hasattr(obj, 'get_full_name') else obj.username


# ---- Incident Serializers ----

class IncidentAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentAttachment
        fields = ['id', 'file', 'description', 'uploaded_by', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class IncidentListSerializer(serializers.ModelSerializer):
    reported_by_name = serializers.CharField(
        source='reported_by.get_full_name', read_only=True
    )
    incident_type_display = serializers.CharField(
        source='get_incident_type_display', read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Incident
        fields = [
            'id', 'title', 'incident_type', 'incident_type_display',
            'severity', 'severity_display', 'status', 'status_display',
            'incident_date', 'location', 'reported_by_name',
            'follow_up_needed', 'created_at',
        ]
        read_only_fields = fields


class IncidentDetailSerializer(serializers.ModelSerializer):
    reported_by = UserMinimalSerializer(read_only=True)
    updated_by = UserMinimalSerializer(read_only=True)
    attachments = IncidentAttachmentSerializer(many=True, read_only=True)
    incident_type_display = serializers.CharField(
        source='get_incident_type_display', read_only=True
    )
    severity_display = serializers.CharField(
        source='get_severity_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = [
            'id', 'tenant', 'reported_by', 'updated_by',
            'created_at', 'updated_at',
        ]


class IncidentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = [
            'incident_type', 'title', 'description', 'severity',
            'incident_date', 'incident_time', 'location',
            'students_involved', 'staff_involved',
            'external_parties', 'witnesses', 'actions_taken',
            'follow_up_needed', 'follow_up_date', 'disciplinary_action',
        ]

    def validate_incident_date(self, value):
        from django.utils import timezone
        if value > timezone.now().date():
            raise serializers.ValidationError(
                'Incident date cannot be in the future.'
            )
        return value


# ---- Visitor Log Serializers ----

class VisitorLogListSerializer(serializers.ModelSerializer):
    visitor_type_display = serializers.CharField(
        source='get_visitor_type_display', read_only=True
    )
    host_staff_name = serializers.SerializerMethodField()
    is_currently_on_site = serializers.BooleanField(read_only=True)

    class Meta:
        model = VisitorLog
        fields = [
            'id', 'visitor_name', 'visitor_type', 'visitor_type_display',
            'organization', 'purpose', 'time_in', 'time_out',
            'host_staff_name', 'id_verified', 'is_currently_on_site',
        ]
        read_only_fields = fields

    def get_host_staff_name(self, obj):
        if obj.host_staff:
            return obj.host_staff.get_full_name
        return None


class VisitorLogDetailSerializer(serializers.ModelSerializer):
    host_staff = UserMinimalSerializer(read_only=True)
    logged_by = UserMinimalSerializer(read_only=True)
    approved_by = UserMinimalSerializer(read_only=True)
    visitor_type_display = serializers.CharField(
        source='get_visitor_type_display', read_only=True
    )

    class Meta:
        model = VisitorLog
        fields = '__all__'
        read_only_fields = [
            'id', 'tenant', 'logged_by', 'created_at', 'updated_at',
        ]


class VisitorLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorLog
        fields = [
            'visitor_name', 'visitor_type', 'organization', 'badge_number',
            'id_verified', 'phone', 'purpose', 'time_in',
            'host_staff', 'students_involved', 'notes', 'approved_by',
        ]


# ---- Case Note Serializers ----

class StudentCaseNoteListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )
    confidentiality_display = serializers.CharField(
        source='get_confidentiality_display', read_only=True
    )
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentCaseNote
        fields = [
            'id', 'student', 'student_name', 'title', 'category',
            'category_display', 'confidentiality', 'confidentiality_display',
            'follow_up_date', 'follow_up_completed', 'created_by_name',
            'created_at',
        ]
        read_only_fields = fields

    def get_student_name(self, obj):
        return obj.student.student.get_full_name

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name


class StudentCaseNoteDetailSerializer(serializers.ModelSerializer):
    created_by = UserMinimalSerializer(read_only=True)
    category_display = serializers.CharField(
        source='get_category_display', read_only=True
    )

    class Meta:
        model = StudentCaseNote
        fields = '__all__'
        read_only_fields = [
            'id', 'tenant', 'created_by', 'created_at', 'updated_at',
        ]


class StudentCaseNoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentCaseNote
        fields = [
            'student', 'category', 'confidentiality', 'title', 'content',
            'follow_up_date', 'related_incident',
        ]
