import logging

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='result.TakenCourse')
def check_grade_anomalies(sender, instance, **kwargs):
    """Run grade anomaly detection after a TakenCourse is saved."""
    from decimal import Decimal

    if instance.total == Decimal('0.00'):
        return

    try:
        from anomaly_detection.detectors.grade import (
            GradeJumpDetector,
            GradeAbnormallyHighDetector,
        )
        GradeJumpDetector().check(instance)
        GradeAbnormallyHighDetector().check(instance)
    except Exception:
        logger.exception("Error in grade anomaly detection for TakenCourse %s", instance.pk)


@receiver(post_save, sender='result.GradeHistory')
def check_grade_history_anomalies(sender, instance, created, **kwargs):
    """Run unauthorized grade change detection on new GradeHistory entries."""
    if not created:
        return

    try:
        from anomaly_detection.detectors.grade import GradeUnauthorizedChangeDetector
        GradeUnauthorizedChangeDetector().check(instance)
    except Exception:
        logger.exception("Error in grade history anomaly detection for GradeHistory %s", instance.pk)


@receiver(post_save, sender='payments.Payment')
def check_payment_anomalies(sender, instance, created, **kwargs):
    """Run payment anomaly detection after a Payment is saved."""
    try:
        from anomaly_detection.detectors.payment import (
            PaymentAmountMismatchDetector,
            DoublePaymentDetector,
        )
        PaymentAmountMismatchDetector().check(instance)
        if created:
            DoublePaymentDetector().check(instance)
    except Exception:
        logger.exception("Error in payment anomaly detection for Payment %s", instance.pk)


@receiver(pre_save, sender='payments.Payment')
def check_payment_status_reversal(sender, instance, **kwargs):
    """Check for suspicious payment status reversals before save."""
    if not instance.pk:
        return

    try:
        from anomaly_detection.detectors.payment import PaymentStatusReversalDetector
        PaymentStatusReversalDetector().check(instance)
    except Exception:
        logger.exception("Error in payment status reversal detection for Payment %s", instance.pk)


@receiver(post_save, sender='payments.Invoice')
def check_invoice_anomalies(sender, instance, created, **kwargs):
    """Check for invoice/fee structure mismatches."""
    if not created:
        return

    try:
        from anomaly_detection.detectors.payment import InvoiceFeeStructureMismatchDetector
        InvoiceFeeStructureMismatchDetector().check(instance)
    except Exception:
        logger.exception("Error in invoice anomaly detection for Invoice %s", instance.pk)


@receiver(post_save, sender='enrollment.RegistrationForm')
def check_enrollment_anomalies(sender, instance, created, **kwargs):
    """Run enrollment anomaly detection after a RegistrationForm is saved."""
    try:
        from anomaly_detection.detectors.enrollment import (
            DuplicateEnrollmentDetector,
            InvalidStatusTransitionDetector,
            UnauthorizedApprovalDetector,
        )
        if created:
            DuplicateEnrollmentDetector().check(instance)
        else:
            InvalidStatusTransitionDetector().check(instance)
            UnauthorizedApprovalDetector().check(instance)
    except Exception:
        logger.exception("Error in enrollment anomaly detection for RegistrationForm %s", instance.pk)
