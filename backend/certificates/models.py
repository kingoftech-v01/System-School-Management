"""
Certificate Generation app models.
PDF certificate generation with digital signatures and verification.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import hashlib
import uuid

User = get_user_model()


class CertificateTemplate(models.Model):
    """Certificate design templates."""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    # Template design
    template_file = models.FileField(
        upload_to='certificates/templates/%Y/%m/',
        help_text="HTML/PDF template file"
    )
    background_image = models.ImageField(
        upload_to='certificates/backgrounds/',
        blank=True,
        help_text="Background image for certificate"
    )

    # Certificate content placeholders
    title_text = models.CharField(max_length=200, default="Certificate of Completion")
    body_template = models.TextField(
        help_text="Template with placeholders: {student_name}, {course_name}, {date}, {grade}"
    )

    # Signature fields
    signature_1_name = models.CharField(max_length=100, blank=True, help_text="e.g., Dean")
    signature_1_title = models.CharField(max_length=100, blank=True)
    signature_1_image = models.ImageField(upload_to='certificates/signatures/', blank=True)

    signature_2_name = models.CharField(max_length=100, blank=True, help_text="e.g., Director")
    signature_2_title = models.CharField(max_length=100, blank=True)
    signature_2_image = models.ImageField(upload_to='certificates/signatures/', blank=True)

    # Settings
    orientation = models.CharField(
        max_length=20,
        choices=(('landscape', 'Landscape'), ('portrait', 'Portrait')),
        default='landscape'
    )
    page_size = models.CharField(
        max_length=20,
        choices=(('A4', 'A4'), ('Letter', 'Letter')),
        default='A4'
    )

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Certificate(models.Model):
    """Issued certificates."""
    STATUS_CHOICES = (
        ('pending', 'Pending Generation'),
        ('generated', 'Generated'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked'),
    )

    # Student and course information
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='certificates'
    )

    # Certificate details
    certificate_number = models.CharField(max_length=100, unique=True, blank=True)
    issue_date = models.DateField(default=timezone.now)
    completion_date = models.DateField(null=True, blank=True)

    # Academic information
    grade = models.CharField(max_length=10, blank=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    credits = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Certificate file
    pdf_file = models.FileField(
        upload_to='certificates/issued/%Y/%m/',
        blank=True,
        help_text="Generated PDF certificate"
    )

    # Digital signature and verification
    hash_signature = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of certificate content"
    )
    blockchain_hash = models.CharField(max_length=66, blank=True, help_text="Blockchain transaction hash")
    qr_code = models.ImageField(upload_to='certificates/qr_codes/', blank=True)
    verification_url = models.URLField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Issuance
    issued_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates'
    )

    # Revocation
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_certificates'
    )
    revocation_reason = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['student', '-issue_date']),
            models.Index(fields=['course', '-issue_date']),
            models.Index(fields=['certificate_number']),
            models.Index(fields=['status', '-created_at']),
        ]
        unique_together = ['student', 'course']

    def __str__(self):
        return f"Certificate {self.certificate_number} - {self.student}"

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = self.generate_certificate_number()
        if not self.hash_signature and self.pdf_file:
            self.hash_signature = self.calculate_hash()
        super().save(*args, **kwargs)

    def generate_certificate_number(self):
        """Generate unique certificate number."""
        year = self.issue_date.year
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"CERT-{year}-{unique_id}"

    def calculate_hash(self):
        """Calculate SHA-256 hash of certificate data."""
        data = f"{self.certificate_number}{self.student.id}{self.course.id}{self.issue_date}"
        return hashlib.sha256(data.encode()).hexdigest()

    def revoke(self, user, reason):
        """Revoke certificate."""
        self.is_revoked = True
        self.status = 'revoked'
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.revocation_reason = reason
        self.save()


class CertificateVerification(models.Model):
    """Certificate verification attempts."""
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.CASCADE,
        related_name='verifications'
    )

    # Verification details
    verified_at = models.DateTimeField(auto_now_add=True)
    verification_method = models.CharField(
        max_length=50,
        choices=(
            ('qr_code', 'QR Code Scan'),
            ('number', 'Certificate Number'),
            ('hash', 'Hash Verification'),
            ('blockchain', 'Blockchain Verification'),
        )
    )

    # Requester information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    verified_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificate_verifications'
    )

    # Result
    is_valid = models.BooleanField()
    verification_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-verified_at']
        indexes = [
            models.Index(fields=['certificate', '-verified_at']),
            models.Index(fields=['-verified_at']),
        ]

    def __str__(self):
        return f"Verification of {self.certificate.certificate_number} at {self.verified_at}"


class BatchCertificateGeneration(models.Model):
    """Batch certificate generation tracking."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='batch_generations'
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True
    )

    # Batch criteria
    min_grade = models.CharField(max_length=10, blank=True, help_text="Minimum grade requirement")
    min_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    # Progress tracking
    total_students = models.PositiveIntegerField(default=0)
    processed_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_log = models.TextField(blank=True)

    # Metadata
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='initiated_batch_generations'
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Batch generation for {self.course} - {self.get_status_display()}"
