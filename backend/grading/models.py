"""
Advanced Grading app models.
Rubric-based grading, peer assessment, and grade curves.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()


class GradingRubric(models.Model):
    """Grading rubric template."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Assignment type
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='grading_rubrics'
    )

    # Scale
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    passing_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('60.00'))

    # Settings
    is_active = models.BooleanField(default=True)
    allow_partial_credit = models.BooleanField(default=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rubrics')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course', 'name']
        indexes = [
            models.Index(fields=['course', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.course}"

    def get_total_weight(self):
        """Calculate total weight of all criteria."""
        return self.criteria.aggregate(models.Sum('weight'))['weight__sum'] or 0


class RubricCriterion(models.Model):
    """Individual grading criterion within a rubric."""
    rubric = models.ForeignKey(GradingRubric, on_delete=models.CASCADE, related_name='criteria')

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Weight and scoring
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Weight as percentage (0-100)"
    )
    max_points = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))

    # Levels of achievement
    excellent_description = models.TextField(blank=True, help_text="Description of excellent performance")
    good_description = models.TextField(blank=True)
    satisfactory_description = models.TextField(blank=True)
    needs_improvement_description = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['rubric', 'order']

    def __str__(self):
        return f"{self.rubric.name} - {self.name}"


class RubricGrade(models.Model):
    """Applied grade using a rubric."""
    rubric = models.ForeignKey(GradingRubric, on_delete=models.CASCADE, related_name='grades')
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE, related_name='rubric_grades')

    # Assignment reference (flexible)
    assignment_name = models.CharField(max_length=200)
    assignment_type = models.CharField(
        max_length=50,
        choices=(
            ('essay', 'Essay'),
            ('project', 'Project'),
            ('presentation', 'Presentation'),
            ('lab', 'Lab Work'),
            ('other', 'Other'),
        )
    )

    # Overall score
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    letter_grade = models.CharField(max_length=3, blank=True)

    # Grading details
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rubric_grades_given')
    graded_at = models.DateTimeField(auto_now_add=True)

    # Feedback
    overall_feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-graded_at']
        indexes = [
            models.Index(fields=['student', '-graded_at']),
            models.Index(fields=['rubric', '-graded_at']),
        ]

    def __str__(self):
        return f"{self.student} - {self.assignment_name}: {self.total_score}"

    def calculate_grade(self):
        """Calculate total score from criterion grades."""
        total = Decimal('0.00')
        for criterion_grade in self.criterion_grades.all():
            weighted_score = (criterion_grade.score / criterion_grade.criterion.max_points) * criterion_grade.criterion.weight
            total += weighted_score
        self.total_score = total
        self.percentage = (total / self.rubric.max_score) * Decimal('100.00')
        self.save()


class CriterionGrade(models.Model):
    """Grade for individual criterion."""
    rubric_grade = models.ForeignKey(RubricGrade, on_delete=models.CASCADE, related_name='criterion_grades')
    criterion = models.ForeignKey(RubricCriterion, on_delete=models.CASCADE)

    score = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ['rubric_grade', 'criterion']

    def __str__(self):
        return f"{self.rubric_grade} - {self.criterion.name}: {self.score}"


class PeerReview(models.Model):
    """Peer assessment system."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    )

    # Assignment details
    course = models.ForeignKey('course.Course', on_delete=models.CASCADE, related_name='peer_reviews')
    assignment_name = models.CharField(max_length=200)
    rubric = models.ForeignKey(GradingRubric, on_delete=models.SET_NULL, null=True, blank=True)

    # Student being reviewed
    reviewee = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='received_peer_reviews'
    )

    # Reviewer
    reviewer = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='submitted_peer_reviews'
    )

    # Review content
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)

    # Anonymous option
    is_anonymous = models.BooleanField(default=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['assignment_name', 'reviewee', 'reviewer']
        indexes = [
            models.Index(fields=['reviewee', '-created_at']),
            models.Index(fields=['reviewer', 'status']),
        ]

    def __str__(self):
        return f"Peer review: {self.reviewer} → {self.reviewee} ({self.assignment_name})"


class GradeCurve(models.Model):
    """Grade curve adjustments."""
    CURVE_TYPE_CHOICES = (
        ('linear', 'Linear Adjustment'),
        ('sqrt', 'Square Root Curve'),
        ('bell', 'Bell Curve'),
        ('custom', 'Custom'),
    )

    course = models.ForeignKey('course.Course', on_delete=models.CASCADE, related_name='grade_curves')
    assignment_name = models.CharField(max_length=200)

    # Curve settings
    curve_type = models.CharField(max_length=20, choices=CURVE_TYPE_CHOICES)
    adjustment_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        help_text="Multiplier for linear adjustment"
    )
    add_points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Points to add to all scores"
    )

    # Statistics before curve
    mean_before = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    median_before = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    std_dev_before = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Statistics after curve
    mean_after = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    median_after = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    std_dev_after = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Metadata
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.course} - {self.assignment_name} Curve"
