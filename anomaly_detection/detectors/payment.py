import logging
from decimal import Decimal

from .base import BaseDetector

logger = logging.getLogger(__name__)


class PaymentAmountMismatchDetector(BaseDetector):
    """Detect payments where amount doesn't match the invoice amount."""

    anomaly_code = 'payment_amount_mismatch'

    def check(self, payment):
        invoice = payment.invoice
        if not invoice or not invoice.amount:
            return

        if payment.amount != invoice.amount:
            self.create_alert(
                title=f"Payment amount mismatch: paid {payment.amount} vs invoice {invoice.amount} "
                      f"(Invoice {invoice.invoice_code})",
                details={
                    'payment_id': payment.pk,
                    'transaction_id': payment.transaction_id,
                    'payment_amount': str(payment.amount),
                    'invoice_amount': str(invoice.amount),
                    'invoice_code': invoice.invoice_code,
                    'difference': str(payment.amount - invoice.amount),
                    'gateway': payment.payment_gateway,
                },
                user=invoice.user,
                related_obj=payment,
            )


class DoublePaymentDetector(BaseDetector):
    """Detect multiple completed payments for the same invoice."""

    anomaly_code = 'payment_double'

    def check(self, payment):
        from payments.models import Payment

        invoice = payment.invoice

        completed_count = Payment.objects.filter(
            invoice=invoice,
            status='completed',
        ).count()

        if completed_count > 1:
            self.create_alert(
                title=f"Double payment detected: {completed_count} completed payments "
                      f"for invoice {invoice.invoice_code}",
                details={
                    'invoice_code': invoice.invoice_code,
                    'completed_payment_count': completed_count,
                    'latest_payment_id': payment.pk,
                    'latest_transaction_id': payment.transaction_id,
                    'invoice_amount': str(invoice.amount) if invoice.amount else '0',
                },
                user=invoice.user,
                related_obj=payment,
            )


class PaymentStatusReversalDetector(BaseDetector):
    """Detect suspicious payment status reversals (completed -> failed/pending)."""

    anomaly_code = 'payment_status_reversal'

    # Valid forward transitions
    VALID_TRANSITIONS = {
        'pending': {'processing', 'completed', 'failed'},
        'processing': {'completed', 'failed'},
        'completed': {'refunded'},
        'failed': {'pending', 'processing'},
        'refunded': set(),
    }

    def check(self, payment):
        """Called on pre_save - instance has new values, DB has old."""
        from payments.models import Payment

        if not payment.pk:
            return

        try:
            old_payment = Payment.objects.get(pk=payment.pk)
        except Payment.DoesNotExist:
            return

        old_status = old_payment.status
        new_status = payment.status

        if old_status == new_status:
            return

        valid_next = self.VALID_TRANSITIONS.get(old_status, set())
        if new_status not in valid_next:
            self.create_alert(
                title=f"Suspicious payment status reversal: {old_status} -> {new_status} "
                      f"(Transaction {payment.transaction_id})",
                details={
                    'payment_id': payment.pk,
                    'transaction_id': payment.transaction_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'invoice_code': payment.invoice.invoice_code if payment.invoice else '',
                    'amount': str(payment.amount),
                },
                user=payment.invoice.user if payment.invoice else None,
                related_obj=payment,
            )


class InvoiceFeeStructureMismatchDetector(BaseDetector):
    """Detect invoices where amount doesn't match the fee structure total."""

    anomaly_code = 'payment_fee_mismatch'

    def check(self, invoice):
        if not invoice.fee_structure or not invoice.amount:
            return

        expected = invoice.fee_structure.get_total_fee()
        if invoice.amount != expected:
            self.create_alert(
                title=f"Invoice/fee structure mismatch: invoice {invoice.amount} vs "
                      f"structure {expected} (Invoice {invoice.invoice_code})",
                details={
                    'invoice_code': invoice.invoice_code,
                    'invoice_amount': str(invoice.amount),
                    'fee_structure_total': str(expected),
                    'fee_structure': str(invoice.fee_structure),
                    'difference': str(invoice.amount - expected),
                },
                user=invoice.user,
                related_obj=invoice,
            )
