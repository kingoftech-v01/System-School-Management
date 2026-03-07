"""
Models for academic programs (filieres) and their associated subjects.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Filiere(models.Model):
    """
    Academic track/program (e.g., Computer Science, Business Administration).
    Each filiere has specific subjects with coefficients.
    """

    # Tenant relationship
    tenant = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        related_name='filieres',
        verbose_name=_('School')
    )

    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name=_('Program Name')
    )
    code = models.CharField(
        max_length=20,
        verbose_name=_('Program Code'),
        help_text=_('Unique code for this program (e.g., CS, BA, ENG)')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )

    # Program Details
    level = models.CharField(
        max_length=25,
        choices=(
            ('Bachelor', _('Bachelor Degree')),
            ('Master', _('Master Degree')),
        ),
        default='Bachelor',
        verbose_name=_('Level')
    )
    duration_years = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_('Duration (Years)')
    )
    capacity = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Maximum Students'),
        help_text=_('Maximum number of students allowed in this program')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Inactive programs cannot accept new enrollments')
    )

    # Director/Coordinator
    coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role__in': ['professor', 'direction']},
        related_name='coordinated_filieres',
        verbose_name=_('Program Coordinator')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('Filiere/Program')
        verbose_name_plural = _('Filieres/Programs')
        unique_together = [['tenant', 'code']]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_total_subjects(self):
        """Get total number of subjects in this filiere."""
        return self.subjects.count()

    def get_enrolled_students_count(self):
        """Get number of students currently enrolled."""
        try:
            from enrollment.models import RegistrationForm
            return RegistrationForm.objects.filter(
                filiere=self,
                status='enrolled'
            ).count()
        except:
            return 0

    def is_full(self):
        """Check if filiere has reached capacity."""
        if not self.capacity:
            return False
        return self.get_enrolled_students_count() >= self.capacity


class FiliereSubject(models.Model):
    """
    Subjects associated with a filiere, including their coefficients.
    Each subject has a specific weight in the overall grading.
    """

    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='subjects',
        verbose_name=_('Filiere')
    )
    subject = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        verbose_name=_('Subject/Course')
    )

    # Subject details for this filiere
    coefficient = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('10'))],
        verbose_name=_('Coefficient'),
        help_text=_('Weight of this subject in final grade calculation')
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('Is Mandatory'),
        help_text=_('Whether this subject is required or elective')
    )
    year = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name=_('Academic Year'),
        help_text=_('Which year of the program this subject belongs to')
    )
    semester = models.IntegerField(
        choices=(
            (1, _('Semester 1')),
            (2, _('Semester 2')),
            (3, _('Semester 3')),
            (4, _('Semester 4')),
        ),
        default=1,
        verbose_name=_('Semester')
    )

    # Additional info
    credits = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name=_('Credits/ECTS'),
        help_text=_('Number of academic credits for this subject')
    )
    hours_per_week = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(40)],
        verbose_name=_('Hours per Week')
    )

    class Meta:
        ordering = ['year', 'semester', 'subject__title']
        verbose_name = _('Filiere Subject')
        verbose_name_plural = _('Filiere Subjects')
        unique_together = [['filiere', 'subject', 'year', 'semester']]
        indexes = [
            models.Index(fields=['filiere', 'year', 'semester']),
            models.Index(fields=['is_mandatory']),
        ]

    def __str__(self):
        return f"{self.filiere.code} - {self.subject.title} (Year {self.year}, Sem {self.semester})"

    def get_total_hours(self):
        """Calculate total hours for the semester (assuming 15 weeks)."""
        return self.hours_per_week * 15


class FiliereRequirement(models.Model):
    """
    Admission requirements or prerequisites for a filiere.
    """

    filiere = models.ForeignKey(
        Filiere,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name=_('Filiere')
    )
    requirement_type = models.CharField(
        max_length=50,
        choices=(
            ('academic', _('Academic Qualification')),
            ('language', _('Language Proficiency')),
            ('exam', _('Entrance Exam')),
            ('document', _('Required Document')),
            ('other', _('Other')),
        ),
        verbose_name=_('Requirement Type')
    )
    description = models.TextField(verbose_name=_('Description'))
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name=_('Is Mandatory')
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_('Display Order')
    )

    class Meta:
        ordering = ['order', 'requirement_type']
        verbose_name = _('Filiere Requirement')
        verbose_name_plural = _('Filiere Requirements')

    def __str__(self):
        return f"{self.filiere.code} - {self.get_requirement_type_display()}"
