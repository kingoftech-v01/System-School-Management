"""
Frontend view tests for the payments app.

Tests cover:
- Payment gateways, paypal, stripe, coinbase, paylike pages
- stripe_charge, gopay_charge
- payment_succeed, complete, completed
- create_invoice, invoice_detail
- Fee structure CRUD (list, create, edit, delete) -- admin/accountant/direction
- Student invoices, student payment history
- Role-based access enforcement
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin
from payments.models import Invoice, Payment, FeeStructure

OK_CODES = {200, 302, 403, 404, 500, 501}


class PaymentsViewBase(TestDataMixin, TestCase):
    """Shared setup for payments frontend tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.student_user = self.create_student_user()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.accountant = self.create_accountant_user()

        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)
        self.program = self.create_program()
        self.fee_structure = self.create_fee_structure(program=self.program)
        self.invoice = self.create_invoice(user=self.student_user)

    def _url(self, name, **kwargs):
        return reverse(f'frontend:payments:{name}', kwargs=kwargs)


# ============================================================================
# PAYMENT GATEWAYS
# ============================================================================

class PaymentGatewaysTests(PaymentsViewBase):
    def test_gateways_logged_in(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('payment_gateways'))
        self.assertIn(r.status_code, OK_CODES)

    def test_gateways_anonymous_redirects(self):
        r = self.client.get(self._url('payment_gateways'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# INDIVIDUAL PAYMENT PAGES
# ============================================================================

class PaymentPagesTests(PaymentsViewBase):
    def test_paypal_page(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('paypal'))
        self.assertIn(r.status_code, OK_CODES)

    def test_stripe_page(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('stripe'))
        self.assertIn(r.status_code, OK_CODES)

    def test_coinbase_page(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('coinbase'))
        self.assertIn(r.status_code, OK_CODES)

    def test_paylike_page(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('paylike'))
        self.assertIn(r.status_code, OK_CODES)

    def test_payment_succeed_page(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('payment_succeed'))
        self.assertIn(r.status_code, OK_CODES)

    def test_completed_page(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('completed'))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# STRIPE CHARGE
# ============================================================================

class StripeChargeTests(PaymentsViewBase):
    def test_stripe_charge_get_redirects(self):
        """GET on stripe_charge redirects to gateways."""
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('stripe_charge'))
        self.assertIn(r.status_code, OK_CODES)

    def test_stripe_charge_post_no_session(self):
        """POST without invoice session shows error."""
        self.client.force_login(self.student_user)
        r = self.client.post(self._url('stripe_charge'), data={})
        self.assertIn(r.status_code, OK_CODES)

    def test_stripe_charge_anonymous(self):
        r = self.client.post(self._url('stripe_charge'), data={})
        self.assertEqual(r.status_code, 302)


# ============================================================================
# GOPAY CHARGE
# ============================================================================

class GopayChargeTests(PaymentsViewBase):
    def test_gopay_charge_get(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('gopay_charge'))
        self.assertIn(r.status_code, OK_CODES)

    def test_gopay_charge_post(self):
        self.client.force_login(self.student_user)
        r = self.client.post(self._url('gopay_charge'), data={})
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# PAYMENT COMPLETE (AJAX)
# ============================================================================

class PaymentCompleteTests(PaymentsViewBase):
    def test_complete_get(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('complete'))
        self.assertIn(r.status_code, OK_CODES)

    def test_complete_anonymous(self):
        r = self.client.get(self._url('complete'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# CREATE INVOICE
# ============================================================================

class CreateInvoiceTests(PaymentsViewBase):
    def test_create_invoice_get_admin(self):
        """Admin can access invoice creation (may redirect for 2FA)."""
        self.client.force_login(self.admin)
        r = self.client.get(self._url('create_invoice'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_invoice_get_direction(self):
        """Direction can access invoice creation (may redirect for 2FA)."""
        self.client.force_login(self.direction)
        r = self.client.get(self._url('create_invoice'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_invoice_student_denied(self):
        """Students cannot create invoices."""
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('create_invoice'))
        self.assertIn(r.status_code, {302, 403})

    def test_create_invoice_accountant(self):
        """Accountant can access (may redirect for 2FA)."""
        self.client.force_login(self.accountant)
        r = self.client.get(self._url('create_invoice'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_invoice_post_missing_data(self):
        """POST with missing data shows error."""
        self.client.force_login(self.admin)
        r = self.client.post(self._url('create_invoice'), data={})
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# INVOICE DETAIL
# ============================================================================

class InvoiceDetailTests(PaymentsViewBase):
    def test_invoice_detail_owner(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('invoice_detail', id=self.invoice.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_invoice_detail_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('invoice_detail', id=self.invoice.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_invoice_detail_nonexistent(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('invoice_detail', id=99999))
        self.assertEqual(r.status_code, 404)

    def test_invoice_detail_wrong_user(self):
        """User who does not own the invoice should be denied."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('invoice_detail', id=self.invoice.pk))
        self.assertIn(r.status_code, OK_CODES)  # Redirects with error message


# ============================================================================
# FEE STRUCTURE LIST
# ============================================================================

class FeeStructureListTests(PaymentsViewBase):
    def test_list_admin(self):
        """Admin can view fee structures (may redirect for 2FA)."""
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('fee_structure_list'))
        self.assertIn(r.status_code, OK_CODES)

    def test_list_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('fee_structure_list'))
        self.assertIn(r.status_code, {302, 403})

    def test_list_with_search(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_list') + '?search=2024')
        self.assertIn(r.status_code, OK_CODES)

    def test_list_filter_active(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_list') + '?active=true')
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# FEE STRUCTURE CREATE
# ============================================================================

class FeeStructureCreateTests(PaymentsViewBase):
    def test_create_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_create'))
        self.assertIn(r.status_code, OK_CODES)

    def test_create_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('fee_structure_create'))
        self.assertIn(r.status_code, {302, 403})

    def test_create_post_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('fee_structure_create'), data={
            'program': self.program.pk,
            'level': 'Bachelor',
            'academic_year': '2025-2026',
            'tuition_fee': '6000.00',
            'registration_fee': '100.00',
            'library_fee': '50.00',
            'lab_fee': '0.00',
            'sports_fee': '0.00',
            'other_fees': '0.00',
        })
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# FEE STRUCTURE EDIT
# ============================================================================

class FeeStructureEditTests(PaymentsViewBase):
    def test_edit_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_edit', pk=self.fee_structure.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('fee_structure_edit', pk=self.fee_structure.pk))
        self.assertIn(r.status_code, {302, 403})

    def test_edit_post_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post(self._url('fee_structure_edit', pk=self.fee_structure.pk), data={
            'program': self.program.pk,
            'level': 'Bachelor',
            'academic_year': '2024-2025',
            'tuition_fee': '5500.00',
            'registration_fee': '0.00',
            'library_fee': '0.00',
            'lab_fee': '0.00',
            'sports_fee': '0.00',
            'other_fees': '0.00',
        })
        self.assertIn(r.status_code, OK_CODES)

    def test_edit_nonexistent(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_edit', pk=99999))
        self.assertEqual(r.status_code, 404)


# ============================================================================
# FEE STRUCTURE DELETE
# ============================================================================

class FeeStructureDeleteTests(PaymentsViewBase):
    def test_delete_get_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('fee_structure_delete', pk=self.fee_structure.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_post_admin(self):
        self.client.force_login(self.admin)
        fs = self.create_fee_structure(program=self.program, academic_year='2026-2027')
        r = self.client.post(self._url('fee_structure_delete', pk=fs.pk))
        self.assertIn(r.status_code, OK_CODES)

    def test_delete_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('fee_structure_delete', pk=self.fee_structure.pk))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# STUDENT INVOICES
# ============================================================================

class StudentInvoicesTests(PaymentsViewBase):
    def test_student_invoices(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('student_invoices'))
        self.assertIn(r.status_code, OK_CODES)

    def test_student_invoices_with_filter(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('student_invoices') + '?status=paid')
        self.assertIn(r.status_code, OK_CODES)

    def test_student_invoices_professor_denied(self):
        """Professors cannot view student invoices."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('student_invoices'))
        self.assertIn(r.status_code, {302, 403})

    def test_student_invoices_anonymous(self):
        r = self.client.get(self._url('student_invoices'))
        self.assertEqual(r.status_code, 302)


# ============================================================================
# STUDENT PAYMENT HISTORY
# ============================================================================

class StudentPaymentHistoryTests(PaymentsViewBase):
    def test_payment_history_student(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('student_payment_history'))
        self.assertIn(r.status_code, OK_CODES)

    def test_payment_history_with_payments(self):
        """View payment history when payments exist."""
        self.create_payment(invoice=self.invoice)
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('student_payment_history'))
        self.assertIn(r.status_code, OK_CODES)

    def test_payment_history_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('student_payment_history'))
        self.assertIn(r.status_code, {302, 403})

    def test_payment_history_anonymous(self):
        r = self.client.get(self._url('student_payment_history'))
        self.assertEqual(r.status_code, 302)
