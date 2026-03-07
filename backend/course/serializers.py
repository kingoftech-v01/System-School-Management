"""
Course App Serializers - DRF serializers for course models.

Provides API serialization for:
- Programs
- Courses
- Course allocations
- Course documentation (files and videos)
"""

from rest_framework import serializers
from .models import Program, Course, CourseAllocation, Upload, UploadVideo


class ProgramSerializer(serializers.ModelSerializer):
    """Serializer for Program model."""
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Program
        fields = ['id', 'title', 'summary', 'course_count']

    def get_course_count(self, obj):
        return obj.course_set.count()


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    program_name = serializers.CharField(source='program.title', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    year_display = serializers.CharField(source='get_year_display', read_only=True)
    semester_display = serializers.CharField(source='get_semester_display', read_only=True)
    is_current_semester = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'slug', 'title', 'code', 'credit', 'summary',
            'program', 'program_name', 'level', 'level_display',
            'year', 'year_display', 'semester', 'semester_display',
            'is_elective', 'is_current_semester'
        ]
        read_only_fields = ['slug']


class CourseAllocationSerializer(serializers.ModelSerializer):
    """Serializer for CourseAllocation model."""
    lecturer_name = serializers.CharField(source='lecturer.get_full_name', read_only=True)
    lecturer_email = serializers.CharField(source='lecturer.email', read_only=True)
    course_details = CourseSerializer(source='courses', many=True, read_only=True)
    session_name = serializers.CharField(source='session.session', read_only=True)

    class Meta:
        model = CourseAllocation
        fields = [
            'id', 'lecturer', 'lecturer_name', 'lecturer_email',
            'courses', 'course_details', 'session', 'session_name'
        ]


class UploadSerializer(serializers.ModelSerializer):
    """Serializer for Upload (course documentation) model."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    file_extension = serializers.CharField(source='get_extension_short', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Upload
        fields = [
            'id', 'title', 'course', 'course_title', 'course_code',
            'file', 'file_url', 'file_extension', 'updated_date', 'upload_time'
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class UploadVideoSerializer(serializers.ModelSerializer):
    """Serializer for UploadVideo model."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadVideo
        fields = [
            'id', 'slug', 'title', 'course', 'course_title', 'course_code',
            'video', 'video_url', 'summary', 'timestamp'
        ]
        read_only_fields = ['slug']

    def get_video_url(self, obj):
        request = self.context.get('request')
        if request and obj.video:
            return request.build_absolute_uri(obj.video.url)
        return None


class CourseRegistrationSerializer(serializers.Serializer):
    """Serializer for course registration (bulk operation)."""
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    def validate_course_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one course must be selected.")
        return value


class CourseDropSerializer(serializers.Serializer):
    """Serializer for course drop (bulk operation)."""
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )

    def validate_course_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one course must be selected.")
        return value
