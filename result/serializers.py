"""
Result App Serializers - DRF serializers for result models.

Provides API serialization for:
- TakenCourse (student course grades)
- Result (semester results)
- Grade component weights
- Grade appeals
- Transcripts
"""

from rest_framework import serializers
from .models import (
    TakenCourse, Result, GradeComponentWeight,
    GradeAppeal, GradeHistory, Transcript
)


class TakenCourseSerializer(serializers.ModelSerializer):
    """Serializer for TakenCourse model."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    student_number = serializers.CharField(source='student.id_number', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_credit = serializers.IntegerField(source='course.credit', read_only=True)

    # Computed fields
    total_score = serializers.DecimalField(source='total', max_digits=5, decimal_places=2, read_only=True)
    letter_grade = serializers.CharField(source='grade', read_only=True)
    grade_point = serializers.DecimalField(source='point', max_digits=5, decimal_places=2, read_only=True)
    pass_status = serializers.CharField(source='comment', read_only=True)

    class Meta:
        model = TakenCourse
        fields = [
            'id', 'student', 'student_name', 'student_number',
            'course', 'course_title', 'course_code', 'course_credit',
            'assignment', 'mid_exam', 'quiz', 'attendance', 'final_exam',
            'total_score', 'letter_grade', 'grade_point', 'pass_status'
        ]
        read_only_fields = ['total_score', 'letter_grade', 'grade_point', 'pass_status']


class TakenCourseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating TakenCourse scores."""

    class Meta:
        model = TakenCourse
        fields = ['assignment', 'mid_exam', 'quiz', 'attendance', 'final_exam']

    def validate(self, data):
        """Ensure all scores are between 0 and 100."""
        for field in ['assignment', 'mid_exam', 'quiz', 'attendance', 'final_exam']:
            value = data.get(field, 0)
            if value < 0 or value > 100:
                raise serializers.ValidationError({
                    field: f'{field} must be between 0 and 100.'
                })
        return data


class ResultSerializer(serializers.ModelSerializer):
    """Serializer for Result model."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    student_number = serializers.CharField(source='student.id_number', read_only=True)
    semester_display = serializers.CharField(source='get_semester_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)

    class Meta:
        model = Result
        fields = [
            'id', 'student', 'student_name', 'student_number',
            'gpa', 'cgpa', 'semester', 'semester_display',
            'session', 'level', 'level_display'
        ]


class GradeComponentWeightSerializer(serializers.ModelSerializer):
    """Serializer for GradeComponentWeight model."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    program_title = serializers.CharField(source='program.title', read_only=True)
    total_weight = serializers.SerializerMethodField()

    class Meta:
        model = GradeComponentWeight
        fields = [
            'id', 'course', 'course_title', 'program', 'program_title',
            'assignment_weight', 'mid_exam_weight', 'quiz_weight',
            'attendance_weight', 'final_exam_weight', 'total_weight',
            'created_at', 'updated_at'
        ]

    def get_total_weight(self, obj):
        """Calculate total weight percentage."""
        return (
            obj.assignment_weight + obj.mid_exam_weight +
            obj.quiz_weight + obj.attendance_weight + obj.final_exam_weight
        )

    def validate(self, data):
        """Ensure weights sum to 100."""
        total = sum([
            data.get('assignment_weight', 0),
            data.get('mid_exam_weight', 0),
            data.get('quiz_weight', 0),
            data.get('attendance_weight', 0),
            data.get('final_exam_weight', 0)
        ])
        if total != 100:
            raise serializers.ValidationError(
                f'Component weights must sum to 100%. Current total: {total}%'
            )
        return data


class GradeAppealSerializer(serializers.ModelSerializer):
    """Serializer for GradeAppeal model."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='taken_course.course.title', read_only=True)
    course_code = serializers.CharField(source='taken_course.course.code', read_only=True)
    current_grade = serializers.CharField(source='taken_course.grade', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reviewer_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)

    class Meta:
        model = GradeAppeal
        fields = [
            'id', 'taken_course', 'student', 'student_name',
            'course_title', 'course_code', 'current_grade',
            'reason', 'supporting_documents', 'status', 'status_display',
            'reviewed_by', 'reviewer_name', 'review_notes', 'decision',
            'submitted_at', 'reviewed_at', 'resolved_at'
        ]
        read_only_fields = [
            'submitted_at', 'reviewed_at', 'resolved_at',
            'reviewed_by', 'review_notes', 'decision'
        ]


class GradeHistorySerializer(serializers.ModelSerializer):
    """Serializer for GradeHistory model."""
    student_name = serializers.CharField(source='taken_course.student.student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='taken_course.course.title', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)

    class Meta:
        model = GradeHistory
        fields = [
            'id', 'taken_course', 'student_name', 'course_title',
            'old_assignment', 'old_mid_exam', 'old_quiz', 'old_attendance', 'old_final_exam',
            'old_total', 'old_grade',
            'new_assignment', 'new_mid_exam', 'new_quiz', 'new_attendance', 'new_final_exam',
            'new_total', 'new_grade',
            'changed_by', 'changed_by_name', 'change_reason', 'changed_at'
        ]
        read_only_fields = ['changed_at']


class TranscriptSerializer(serializers.ModelSerializer):
    """Serializer for Transcript model."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    student_number = serializers.CharField(source='student.id_number', read_only=True)
    transcript_type_display = serializers.CharField(source='get_transcript_type_display', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Transcript
        fields = [
            'id', 'student', 'student_name', 'student_number',
            'transcript_type', 'transcript_type_display',
            'start_semester', 'end_semester', 'pdf_file', 'pdf_url',
            'generated_at', 'generated_by', 'generated_by_name',
            'is_certified', 'certification_number'
        ]
        read_only_fields = ['generated_at', 'generated_by']

    def get_pdf_url(self, obj):
        """Get absolute URL for PDF file."""
        request = self.context.get('request')
        if request and obj.pdf_file:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None


class StudentGPASerializer(serializers.Serializer):
    """Serializer for student GPA calculation results."""
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    current_gpa = serializers.DecimalField(max_digits=5, decimal_places=2)
    cumulative_gpa = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_credits = serializers.IntegerField()
    completed_courses = serializers.IntegerField()
