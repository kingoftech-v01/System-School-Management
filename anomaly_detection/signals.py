import logging

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# ============================================================================
# LOGIN ANOMALY DETECTION
# ============================================================================

@receiver(user_logged_in)
def check_login_anomalies(sender, request, user, **kwargs):
    """Run login anomaly detectors on successful login."""
    try:
        from anomaly_detection.detectors.login import (
            UnusualLoginTimeDetector,
            DeviceChangeDetector,
        )
        ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
        UnusualLoginTimeDetector().check(user)
        DeviceChangeDetector().check(user, current_user_agent=ua)
    except Exception:
        logger.exception(
            "Error in login anomaly detection for user %s",
            getattr(user, 'pk', '?')
        )


@receiver(user_login_failed)
def check_failed_login_anomalies(sender, credentials, request, **kwargs):
    """Run brute force detection on failed logins."""
    try:
        from anomaly_detection.detectors.login import BruteForceDetector
        ip = request.META.get('REMOTE_ADDR', '') if request else None
        BruteForceDetector().check(user=None, ip_address=ip)
    except Exception:
        logger.exception("Error in failed login anomaly detection")


# ============================================================================
# ANOMALY TYPE CACHE INVALIDATION
# ============================================================================

@receiver(post_save, sender='anomaly_detection.AnomalyType')
def clear_anomaly_type_cache(sender, instance, **kwargs):
    """Clear cached AnomalyType when updated (fixes 5-min stale cache issue)."""
    try:
        from django.core.cache import cache
        cache.delete(f'anomaly_type_{instance.code}')
    except Exception:
        logger.exception("Error clearing anomaly type cache for %s", instance.code)


# ============================================================================
# GRADE ANOMALY DETECTION
# ============================================================================

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
