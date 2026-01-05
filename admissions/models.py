"""
Admissions app models for student admission workflow.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class AdmissionSession(models.Model):
    """Admission session/year."""
    name = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class AdmissionStudent(models.Model):
    """Admission application."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('counseling', 'Counseling'),
        ('payment_pending', 'Payment Pending'),
        ('admitted', 'Admitted'),
        ('rejected', 'Rejected'),
    )

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    session = models.ForeignKey(AdmissionSession, on_delete=models.CASCADE, related_name='applications')

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    nationality = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    # Guardian Information
    guardian_name = models.CharField(max_length=200)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(blank=True)

    # Academic Information
    program = models.ForeignKey('course.Program', on_delete=models.SET_NULL, null=True, blank=True)
    previous_school = models.CharField(max_length=200)
    previous_grade = models.CharField(max_length=50)
    exam_scores = models.JSONField(default=dict, blank=True, help_text="Previous exam scores")

    # Application Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications'
    )
    counselor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='counseled_applications'
    )

    # Payment & Admission
    application_fee_paid = models.BooleanField(default=False)
    admitted = models.BooleanField(default=False)
    admission_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Document Upload
    transcript = models.FileField(
        upload_to='admissions/transcripts/%Y/%m/%d/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    birth_certificate = models.FileField(
        upload_to='admissions/certificates/%Y/%m/%d/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['session', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class CounselingComment(models.Model):
    """Counseling feedback."""
    application = models.ForeignKey(
        AdmissionStudent,
        on_delete=models.CASCADE,
        related_name='counseling_comments'
    )
    counselor = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    is_recommendation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.counselor} on {self.application}"


class AdmissionPayment(models.Model):
    """Track admission payment."""
    application = models.OneToOneField(
        AdmissionStudent,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=50,
        choices=(
            ('stripe', 'Stripe'),
            ('braintree', 'Braintree'),
            ('bank_transfer', 'Bank Transfer'),
            ('cash', 'Cash'),
        ),
        default='stripe'
    )
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_admission_payments'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at']

    def __str__(self):
        return f"Payment for {self.application} - ${self.amount}"
