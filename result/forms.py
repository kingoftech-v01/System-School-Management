"""
Result App Forms - Django ModelForms for grading and assessment.

This module provides forms for:
- Score entry and grade management
- Grade component weight configuration
- Grade appeals
- Transcript requests
"""

from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import (
    TakenCourse,
    Result,
    GradeComponentWeight,
    GradeAppeal,
    GradeHistory,
    Transcript
)


class TakenCourseForm(forms.ModelForm):
    """Form for entering and updating course scores."""

    class Meta:
        model = TakenCourse
        fields = [
            'student',
            'course',
            'assignment',
            'mid_exam',
            'quiz',
            'attendance',
            'final_exam'
        ]
        widgets = {
            'assignment': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.01}),
            'mid_exam': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.01}),
            'quiz': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.01}),
            'attendance': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.01}),
            'final_exam': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': 0.01}),
        }

    def clean(self):
        """Validate score ranges."""
        cleaned_data = super().clean()
        score_fields = ['assignment', 'mid_exam', 'quiz', 'attendance', 'final_exam']

        for field in score_fields:
            value = cleaned_data.get(field)
            if value is not None:
                if value < Decimal('0.00') or value > Decimal('100.00'):
                    raise ValidationError({
                        field: _(f'{field.replace("_", " ").title()} must be between 0 and 100.')
                    })

        return cleaned_data


class ScoreEntryForm(forms.ModelForm):
    """Simplified form for quick score entry (lecturer use)."""

    class Meta:
        model = TakenCourse
        fields = ['assignment', 'mid_exam', 'quiz', 'attendance', 'final_exam']
        widgets = {
            'assignment': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': 0.01}),
            'mid_exam': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': 0.01}),
            'quiz': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': 0.01}),
            'attendance': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': 0.01}),
            'final_exam': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'step': 0.01}),
        }


class ResultForm(forms.ModelForm):
    """Form for managing semester results."""

    class Meta:
        model = Result
        fields = ['student', 'gpa', 'cgpa', 'semester', 'session', 'level']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'cgpa': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'session': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }


class GradeComponentWeightForm(forms.ModelForm):
    """Form for configuring grade component weights."""

    class Meta:
        model = GradeComponentWeight
        fields = [
            'course',
            'program',
            'assignment_weight',
            'mid_exam_weight',
            'quiz_weight',
            'attendance_weight',
            'final_exam_weight'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'program': forms.Select(attrs={'class': 'form-control'}),
            'assignment_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'mid_exam_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'quiz_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'attendance_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
            'final_exam_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': 0.01}),
        }
        help_texts = {
            'course': _('Leave blank to set program-wide defaults'),
            'program': _('Leave blank if setting course-specific weights'),
        }

    def clean(self):
        """Ensure weights sum to 100 and either course or program is set."""
        cleaned_data = super().clean()

        # Check that exactly one of course or program is set
        course = cleaned_data.get('course')
        program = cleaned_data.get('program')

        if not course and not program:
            raise ValidationError(_('Either course or program must be specified.'))

        if course and program:
            raise ValidationError(_('Cannot set both course and program. Choose one.'))

        # Validate weight sum
        weight_fields = [
            'assignment_weight',
            'mid_exam_weight',
            'quiz_weight',
            'attendance_weight',
            'final_exam_weight'
        ]

        total = sum(cleaned_data.get(field, Decimal('0.00')) for field in weight_fields)

        if total != Decimal('100.00'):
            raise ValidationError(_(
                'Component weights must sum to exactly 100%. Current total: %(total)s%%'
            ) % {'total': total})

        return cleaned_data


class GradeAppealForm(forms.ModelForm):
    """Form for students to submit grade appeals."""

    class Meta:
        model = GradeAppeal
        fields = ['taken_course', 'reason', 'supporting_documents']
        widgets = {
            'taken_course': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Explain why you are appealing this grade...')
            }),
            'supporting_documents': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'reason': _('Provide a detailed explanation for your appeal.'),
            'supporting_documents': _('Optional: Upload any documents that support your appeal.'),
        }

    def __init__(self, *args, student=None, **kwargs):
        """Initialize form with student's courses."""
        super().__init__(*args, **kwargs)

        if student:
            # Only show courses this student has taken
            self.fields['taken_course'].queryset = TakenCourse.objects.filter(
                student=student
            ).select_related('course')


class GradeAppealReviewForm(forms.ModelForm):
    """Form for faculty to review grade appeals."""

    class Meta:
        model = GradeAppeal
        fields = ['status', 'review_notes', 'decision']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'review_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Provide your review notes and decision reasoning...')
            }),
            'decision': forms.Select(attrs={'class': 'form-control'}),
        }


class TranscriptRequestForm(forms.ModelForm):
    """Form for requesting transcript generation."""

    class Meta:
        model = Transcript
        fields = ['student', 'transcript_type', 'start_semester', 'end_semester']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'transcript_type': forms.Select(attrs={'class': 'form-control'}),
            'start_semester': forms.Select(attrs={'class': 'form-control'}),
            'end_semester': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'transcript_type': _('Official transcripts require registrar certification.'),
            'start_semester': _('First semester to include in transcript.'),
            'end_semester': _('Last semester to include in transcript.'),
        }

    def clean(self):
        """Validate semester range."""
        cleaned_data = super().clean()
        start_semester = cleaned_data.get('start_semester')
        end_semester = cleaned_data.get('end_semester')

        if start_semester and end_semester:
            # You might want to add logic here to ensure start is before end
            pass

        return cleaned_data


class BulkScoreUploadForm(forms.Form):
    """Form for uploading scores via CSV/Excel."""

    course = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_('Select the course for score upload')
    )
    score_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx'}),
        help_text=_('Upload CSV or Excel file with student scores')
    )

    def __init__(self, *args, lecturer=None, **kwargs):
        """Initialize form with lecturer's courses."""
        super().__init__(*args, **kwargs)

        if lecturer:
            from course.models import Course
            # Only show courses this lecturer teaches
            self.fields['course'].queryset = Course.objects.filter(
                allocated_course__lecturer=lecturer
            ).distinct()
