from decimal import Decimal
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from accounts.models import Student
from core.models import Semester
from course.models import Course

User = get_user_model()

A_PLUS = "A+"
A = "A"
A_MINUS = "A-"
B_PLUS = "B+"
B = "B"
B_MINUS = "B-"
C_PLUS = "C+"
C = "C"
C_MINUS = "C-"
D = "D"
F = "F"
NG = "NG"

GRADE_CHOICES = (
    (A_PLUS, "A+"),
    (A, "A"),
    (A_MINUS, "A-"),
    (B_PLUS, "B+"),
    (B, "B"),
    (B_MINUS, "B-"),
    (C_PLUS, "C+"),
    (C, "C"),
    (C_MINUS, "C-"),
    (D, "D"),
    (F, "F"),
    (NG, "NG"),
)

PASS = "PASS"
FAIL = "FAIL"

COMMENT_CHOICES = (
    (PASS, "PASS"),
    (FAIL, "FAIL"),
)

GRADE_BOUNDARIES = [
    (90, A_PLUS),
    (85, A),
    (80, A_MINUS),
    (75, B_PLUS),
    (70, B),
    (65, B_MINUS),
    (60, C_PLUS),
    (55, C),
    (50, C_MINUS),
    (45, D),
    (0, F),
]

GRADE_POINT_MAPPING = {
    A_PLUS: 4.0,
    A: 4.0,
    A_MINUS: 3.75,
    B_PLUS: 3.5,
    B: 3.0,
    B_MINUS: 2.75,
    C_PLUS: 2.5,
    C: 2.0,
    C_MINUS: 1.75,
    D: 1.0,
    F: 0.0,
    NG: 0.0,
}


class TakenCourse(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="taken_courses"
    )
    assignment = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    mid_exam = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    quiz = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    attendance = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    final_exam = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    grade = models.CharField(
        choices=GRADE_CHOICES, max_length=2, blank=True, editable=False
    )
    point = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    comment = models.CharField(
        choices=COMMENT_CHOICES, max_length=200, blank=True, editable=False
    )

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.course.slug})

    def __str__(self):
        return f"{self.course.title} ({self.course.code})"

    def get_total(self):
        return sum(
            [
                Decimal(self.assignment),
                Decimal(self.mid_exam),
                Decimal(self.quiz),
                Decimal(self.attendance),
                Decimal(self.final_exam),
            ]
        )

    def get_grade(self):
        total = self.total
        for boundary, grade in GRADE_BOUNDARIES:
            if total >= boundary:
                return grade
        return NG

    def get_comment(self):
        if self.grade in [F, NG]:
            return FAIL
        return PASS

    def get_point(self):
        credit = self.course.credit
        grade_point = GRADE_POINT_MAPPING.get(self.grade, 0.0)
        return Decimal(credit) * Decimal(grade_point)

    def save(self, *args, **kwargs):
        self.total = self.get_total()
        self.grade = self.get_grade()
        self.point = self.get_point()
        self.comment = self.get_comment()
        super().save(*args, **kwargs)

    def calculate_gpa(self):
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            return Decimal("0.00")

        taken_courses = TakenCourse.objects.filter(
            student=self.student,
            course__level=self.student.level,
            course__semester=current_semester.semester,
        )

        total_points = sum(tc.point for tc in taken_courses)
        total_credits = sum(tc.course.credit for tc in taken_courses)

        if total_credits > 0:
            gpa = total_points / Decimal(total_credits)
            return round(gpa, 2)
        return Decimal("0.00")

    def calculate_cgpa(self):
        taken_courses = TakenCourse.objects.filter(student=self.student)

        total_points = sum(tc.point for tc in taken_courses)
        total_credits = sum(tc.course.credit for tc in taken_courses)

        if total_credits > 0:
            cgpa = total_points / Decimal(total_credits)
            return round(cgpa, 2)
        return Decimal("0.00")


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    gpa = models.FloatField(null=True)
    cgpa = models.FloatField(null=True)
    semester = models.CharField(max_length=100, choices=settings.SEMESTER_CHOICES)
    session = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=25, choices=settings.LEVEL_CHOICES, null=True)

    def __str__(self):
        return f"Result for {self.student} - Semester: {self.semester}, Level: {self.level}"


class GradeComponentWeight(models.Model):
    """Configurable weights for grade components per course or program."""
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='component_weights',
        null=True,
        blank=True,
        help_text=_('Course-specific weights (overrides program defaults)')
    )
    program = models.OneToOneField(
        'course.Program',
        on_delete=models.CASCADE,
        related_name='component_weights',
        null=True,
        blank=True,
        help_text=_('Program-wide default weights')
    )

    # Component weights (must sum to 100)
    assignment_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text=_('Weight percentage for assignments')
    )
    mid_exam_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        help_text=_('Weight percentage for mid-term exam')
    )
    quiz_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text=_('Weight percentage for quizzes')
    )
    attendance_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text=_('Weight percentage for attendance')
    )
    final_exam_weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("50.00"),
        help_text=_('Weight percentage for final exam')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Grade Component Weight')
        verbose_name_plural = _('Grade Component Weights')

    def __str__(self):
        if self.course:
            return f"Weights for {self.course.title}"
        elif self.program:
            return f"Default weights for {self.program.title}"
        return "Grade Component Weights"

    def clean(self):
        """Ensure weights sum to 100."""
        from django.core.exceptions import ValidationError
        total = sum([
            self.assignment_weight,
            self.mid_exam_weight,
            self.quiz_weight,
            self.attendance_weight,
            self.final_exam_weight
        ])
        if total != 100:
            raise ValidationError(
                _('Component weights must sum to 100%. Current total: %(total)s%%'),
                params={'total': total}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class GradeAppeal(models.Model):
    """Grade appeal workflow for students to request grade reviews."""
    STATUS_CHOICES = (
        ('submitted', _('Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('resolved', _('Resolved')),
    )

    taken_course = models.ForeignKey(
        TakenCourse,
        on_delete=models.CASCADE,
        related_name='appeals'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grade_appeals'
    )

    # Appeal details
    reason = models.TextField(
        help_text=_('Student\'s reason for the appeal')
    )
    supporting_documents = models.FileField(
        upload_to='grade_appeals/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text=_('Optional supporting documents')
    )

    # Workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_appeals',
        help_text=_('Faculty member who reviewed the appeal')
    )
    review_notes = models.TextField(
        blank=True,
        help_text=_('Faculty review notes and decision reasoning')
    )
    decision = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True
    )

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('Grade Appeal')
        verbose_name_plural = _('Grade Appeals')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', '-submitted_at']),
            models.Index(fields=['student', '-submitted_at']),
        ]

    def __str__(self):
        return f"Appeal for {self.taken_course.course.title} by {self.student}"

    def approve(self, reviewer, notes=''):
        """Approve the appeal."""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer, notes=''):
        """Reject the appeal."""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

    def resolve(self):
        """Mark appeal as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()


class GradeHistory(models.Model):
    """Immutable audit trail for all grade changes."""
    taken_course = models.ForeignKey(
        TakenCourse,
        on_delete=models.CASCADE,
        related_name='grade_history'
    )

    # Grade components before change
    old_assignment = models.DecimalField(max_digits=5, decimal_places=2)
    old_mid_exam = models.DecimalField(max_digits=5, decimal_places=2)
    old_quiz = models.DecimalField(max_digits=5, decimal_places=2)
    old_attendance = models.DecimalField(max_digits=5, decimal_places=2)
    old_final_exam = models.DecimalField(max_digits=5, decimal_places=2)
    old_total = models.DecimalField(max_digits=5, decimal_places=2)
    old_grade = models.CharField(max_length=2)

    # Grade components after change
    new_assignment = models.DecimalField(max_digits=5, decimal_places=2)
    new_mid_exam = models.DecimalField(max_digits=5, decimal_places=2)
    new_quiz = models.DecimalField(max_digits=5, decimal_places=2)
    new_attendance = models.DecimalField(max_digits=5, decimal_places=2)
    new_final_exam = models.DecimalField(max_digits=5, decimal_places=2)
    new_total = models.DecimalField(max_digits=5, decimal_places=2)
    new_grade = models.CharField(max_length=2)

    # Audit info
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grade_changes'
    )
    change_reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Grade History')
        verbose_name_plural = _('Grade Histories')
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['taken_course', '-changed_at']),
        ]

    def __str__(self):
        return f"Grade change for {self.taken_course} on {self.changed_at}"


class Transcript(models.Model):
    """Generated PDF transcript storage."""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='transcripts'
    )

    # Transcript details
    transcript_type = models.CharField(
        max_length=20,
        choices=(
            ('official', _('Official Transcript')),
            ('unofficial', _('Unofficial Transcript')),
            ('partial', _('Partial Transcript')),
        ),
        default='unofficial'
    )

    # Semester range
    start_semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transcripts_start'
    )
    end_semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transcripts_end'
    )

    # Generated file
    pdf_file = models.FileField(
        upload_to='transcripts/%Y/%m/%d/',
        blank=True,
        help_text=_('Generated PDF transcript')
    )

    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_transcripts'
    )
    is_certified = models.BooleanField(
        default=False,
        help_text=_('Has been officially certified by registrar')
    )
    certification_number = models.CharField(
        max_length=100,
        blank=True,
        unique=True,
        null=True,
        help_text=_('Unique certification number for official transcripts')
    )

    class Meta:
        verbose_name = _('Transcript')
        verbose_name_plural = _('Transcripts')
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['student', '-generated_at']),
            models.Index(fields=['is_certified', '-generated_at']),
        ]

    def __str__(self):
        return f"{self.transcript_type.title()} transcript for {self.student} ({self.generated_at.date()})"
