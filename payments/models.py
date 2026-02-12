from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from accounts.models import Student


class FeeStructure(models.Model):
    """Fee structures by program/level/year."""
    program = models.ForeignKey(
        'course.Program',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    level = models.CharField(
        max_length=25,
        choices=settings.LEVEL_CHOICES,
        help_text=_('Academic level (Bachelor, Master, etc.)')
    )
    academic_year = models.CharField(
        max_length=20,
        help_text=_('Academic year (e.g., 2024-2025)')
    )

    # Fee components
    tuition_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Tuition fee amount')
    )
    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('One-time registration fee')
    )
    library_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    lab_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    sports_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    other_fees = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Fee Structure')
        verbose_name_plural = _('Fee Structures')
        unique_together = [['program', 'level', 'academic_year']]
        ordering = ['-academic_year', 'program', 'level']
        indexes = [
            models.Index(fields=['program', 'level', 'academic_year']),
            models.Index(fields=['is_active', '-academic_year']),
        ]

    def __str__(self):
        return f"{self.program.title} - {self.level} - {self.academic_year}"

    def get_total_fee(self):
        """Calculate total fee."""
        return sum([
            self.tuition_fee,
            self.registration_fee,
            self.library_fee,
            self.lab_fee,
            self.sports_fee,
            self.other_fees
        ])


class Invoice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='invoices',
        help_text=_('Associated student for fee invoice')
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text=_('Associated fee structure')
    )

    total = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    payment_complete = models.BooleanField(default=False)
    invoice_code = models.CharField(max_length=200, blank=True, null=True)

    # NEW: Additional invoice fields
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Payment due date')
    )
    semester = models.ForeignKey(
        'core.Semester',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    description = models.TextField(
        blank=True,
        help_text=_('Invoice description')
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['payment_complete', 'due_date']),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_code} for {self.user}"

    def is_overdue(self):
        """Check if invoice is overdue."""
        if not self.due_date or self.payment_complete:
            return False
        return timezone.now().date() > self.due_date


class PaymentPlan(models.Model):
    """Installment payment plans."""
    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payment_plan'
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    number_of_installments = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Number of installment payments')
    )
    installment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Amount per installment')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Payment Plan')
        verbose_name_plural = _('Payment Plans')

    def __str__(self):
        return f"Payment plan for {self.invoice.invoice_code} ({self.number_of_installments} installments)"

    def get_paid_installments(self):
        """Get number of paid installments."""
        return self.installments.filter(paid=True).count()

    def get_remaining_installments(self):
        """Get number of remaining installments."""
        return self.number_of_installments - self.get_paid_installments()

    def get_remaining_amount(self):
        """Get remaining amount to be paid."""
        paid_amount = sum(
            inst.amount for inst in self.installments.filter(paid=True)
        )
        return self.total_amount - paid_amount


class Installment(models.Model):
    """Individual installment within a payment plan."""
    payment_plan = models.ForeignKey(
        PaymentPlan,
        on_delete=models.CASCADE,
        related_name='installments'
    )

    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = _('Installment')
        verbose_name_plural = _('Installments')
        ordering = ['installment_number']
        unique_together = [['payment_plan', 'installment_number']]

    def __str__(self):
        return f"Installment {self.installment_number} of {self.payment_plan}"

    def is_overdue(self):
        """Check if installment is overdue."""
        if self.paid:
            return False
        return timezone.now().date() > self.due_date


class Payment(models.Model):
    """Payment transaction records."""
    PAYMENT_GATEWAY_CHOICES = (
        ('stripe', _('Stripe')),
        ('braintree', _('Braintree')),
        ('bank_transfer', _('Bank Transfer')),
        ('cash', _('Cash')),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    installment = models.ForeignKey(
        Installment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text=_('Associated installment if part of payment plan')
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    payment_gateway = models.CharField(
        max_length=20,
        choices=PAYMENT_GATEWAY_CHOICES
    )
    transaction_id = models.CharField(
        max_length=200,
        unique=True,
        help_text=_('Payment gateway transaction ID')
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    payment_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['invoice', '-payment_date']),
            models.Index(fields=['status', '-payment_date']),
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} ({self.status})"


class PaymentVerification(models.Model):
    """Multi-step approval workflow for payments."""
    VERIFICATION_STATUS_CHOICES = (
        ('pending', _('Pending Verification')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
    )

    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='verification'
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending'
    )
    verification_notes = models.TextField(
        blank=True,
        help_text=_('Notes about the verification')
    )

    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Payment Verification')
        verbose_name_plural = _('Payment Verifications')
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification for {self.payment.transaction_id} ({self.verification_status})"

    def verify(self, user, notes=''):
        """Verify the payment atomically."""
        from django.db import transaction
        with transaction.atomic():
            self.verification_status = 'verified'
            self.verified_by = user
            self.verification_notes = notes
            self.verified_at = timezone.now()
            self.save()

            # Update payment status
            self.payment.status = 'completed'
            self.payment.save()

    def reject(self, user, notes=''):
        """Reject the payment atomically."""
        from django.db import transaction
        with transaction.atomic():
            self.verification_status = 'rejected'
            self.verified_by = user
            self.verification_notes = notes
            self.verified_at = timezone.now()
            self.save()

            # Update payment status
            self.payment.status = 'failed'
            self.payment.save()


class Receipt(models.Model):
    """Auto-generated PDF receipts."""
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='receipt'
    )

    receipt_number = models.CharField(
        max_length=100,
        unique=True,
        help_text=_('Unique receipt number')
    )
    pdf_file = models.FileField(
        upload_to='receipts/%Y/%m/%d/',
        blank=True,
        help_text=_('Generated PDF receipt')
    )

    generated_at = models.DateTimeField(auto_now_add=True)
    sent_to_email = models.BooleanField(
        default=False,
        help_text=_('Receipt sent to student email')
    )

    class Meta:
        verbose_name = _('Receipt')
        verbose_name_plural = _('Receipts')
        ordering = ['-generated_at']

    def __str__(self):
        return f"Receipt {self.receipt_number} for {self.payment.transaction_id}"
