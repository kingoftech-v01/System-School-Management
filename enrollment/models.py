"""
Enrollment models for student registration and re-enrollment.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class RegistrationForm(models.Model):
    """Model for student registration/enrollment applications."""

    STATUS_CHOICES = (
        ('pending', _('Pending Review')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('enrolled', _('Enrolled')),
    )

    ENROLLMENT_TYPE_CHOICES = (
        ('new', _('New Student')),
        ('transfer', _('Transfer Student')),
        ('re_enrollment', _('Re-enrollment')),
    )

    # Tenant relationship
    tenant = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        related_name='registration_forms'
    )

    # Basic Information
    student_name = models.CharField(max_length=200, verbose_name=_('Student Full Name'))
    date_of_birth = models.DateField(verbose_name=_('Date of Birth'))
    gender = models.CharField(max_length=1, choices=(('M', _('Male')), ('F', _('Female'))))
    nationality = models.CharField(max_length=100, default='', verbose_name=_('Nationality'))

    # Contact Information
    email = models.EmailField(verbose_name=_('Email Address'))
    phone = models.CharField(max_length=20, verbose_name=_('Phone Number'))
    address = models.TextField(verbose_name=_('Residential Address'))

    # Parent/Guardian Information
    parent_name = models.CharField(max_length=200, verbose_name=_('Parent/Guardian Name'))
    parent_email = models.EmailField(verbose_name=_('Parent Email'))
    parent_phone = models.CharField(max_length=20, verbose_name=_('Parent Phone'))
    parent_relationship = models.CharField(
        max_length=50,
        default='father',
        verbose_name=_('Relationship')
    )

    # Academic Information
    filiere = models.ForeignKey(
        'filieres.Filiere',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Program/Filiere'),
        related_name='registrations'
    )
    academic_year = models.CharField(max_length=20, verbose_name=_('Academic Year'))
    level = models.CharField(
        max_length=25,
        choices=(
            ('Bachelor', _('Bachelor Degree')),
            ('Master', _('Master Degree')),
        ),
        default='Bachelor'
    )
    previous_school = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Previous School')
    )

    # Enrollment Details
    enrollment_type = models.CharField(
        max_length=20,
        choices=ENROLLMENT_TYPE_CHOICES,
        default='new'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Review Information
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_registrations',
        verbose_name=_('Reviewed By')
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, verbose_name=_('Review Notes'))
    rejection_reason = models.TextField(blank=True, verbose_name=_('Rejection Reason'))

    # Additional Information
    special_needs = models.TextField(blank=True, verbose_name=_('Special Needs/Requirements'))
    medical_information = models.TextField(blank=True, verbose_name=_('Medical Information'))

    # Created User (if approved and enrolled)
    enrolled_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration_form',
        verbose_name=_('Enrolled User Account')
    )

    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = _('Registration Form')
        verbose_name_plural = _('Registration Forms')
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['academic_year', 'filiere']),
            models.Index(fields=['submitted_at']),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        """Override save to set reviewed_at when status changes."""
        if self.pk:
            old_instance = RegistrationForm.objects.get(pk=self.pk)
            if old_instance.status != self.status and self.status in ['approved', 'rejected']:
                self.reviewed_at = timezone.now()
        super().save(*args, **kwargs)

    def can_enroll(self):
        """Check if registration is ready to be enrolled."""
        return self.status == 'approved' and not self.enrolled_user

    def get_completion_percentage(self):
        """Calculate form completion percentage."""
        required_fields = [
            self.student_name, self.date_of_birth, self.gender,
            self.email, self.phone, self.address,
            self.parent_name, self.parent_email, self.parent_phone,
            self.filiere, self.academic_year
        ]
        filled = sum(1 for field in required_fields if field)
        return int((filled / len(required_fields)) * 100)


class EnrollmentDocument(models.Model):
    """Model for documents uploaded with enrollment application."""

    DOCUMENT_TYPE_CHOICES = (
        ('birth_certificate', _('Birth Certificate')),
        ('photo', _('Student Photo')),
        ('transcript', _('Academic Transcript')),
        ('transfer_letter', _('Transfer Letter')),
        ('medical_certificate', _('Medical Certificate')),
        ('id_card', _('ID Card/Passport')),
        ('parent_id', _('Parent ID')),
        ('other', _('Other Document')),
    )

    registration = models.ForeignKey(
        RegistrationForm,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name=_('Document Type')
    )
    file = models.FileField(
        upload_to='enrollment_docs/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
            )
        ],
        verbose_name=_('Document File')
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Description')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False, verbose_name=_('Verified'))
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_documents'
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _('Enrollment Document')
        verbose_name_plural = _('Enrollment Documents')

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.registration.student_name}"

    def get_file_size(self):
        """Get file size in MB."""
        if self.file:
            return round(self.file.size / (1024 * 1024), 2)
        return 0


class EnrollmentStatusHistory(models.Model):
    """Track status changes for enrollment applications."""

    registration = models.ForeignKey(
        RegistrationForm,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']
        verbose_name = _('Enrollment Status History')
        verbose_name_plural = _('Enrollment Status Histories')

    def __str__(self):
        return f"{self.registration.student_name}: {self.old_status} → {self.new_status}"
