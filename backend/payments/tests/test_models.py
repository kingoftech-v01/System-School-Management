"""Tests for payments app models."""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone

from payments.models import (
    FeeStructure, Invoice, PaymentPlan, Installment,
    Payment, PaymentVerification, Receipt,
)
from tests.helpers import TestDataMixin


class FeeStructureModelTest(TestDataMixin, TestCase):
    def _create_fee_structure(self, **overrides):
        program = overrides.pop('program', None) or self.create_program()
        defaults = {
            'program': program,
            'level': 'Bachelor',
            'academic_year': '2024-2025',
            'tuition_fee': Decimal('5000.00'),
        }
        defaults.update(overrides)
        return FeeStructure.objects.create(**defaults)

    def test_create(self):
        fee = self._create_fee_structure()
        self.assertIsNotNone(fee.pk)

    def test_str(self):
        fee = self._create_fee_structure()
        result = str(fee)
        self.assertIn('2024-2025', result)

    def test_default_is_active(self):
        fee = self._create_fee_structure()
        self.assertTrue(fee.is_active)

    def test_get_total_fee(self):
        fee = self._create_fee_structure(
            tuition_fee=Decimal('5000.00'),
            registration_fee=Decimal('100.00'),
            library_fee=Decimal('50.00'),
            lab_fee=Decimal('200.00'),
            sports_fee=Decimal('30.00'),
            other_fees=Decimal('20.00'),
        )
        expected = Decimal('5400.00')
        self.assertEqual(fee.get_total_fee(), expected)

    def test_get_total_fee_defaults(self):
        fee = self._create_fee_structure(tuition_fee=Decimal('1000.00'))
        self.assertEqual(fee.get_total_fee(), Decimal('1000.00'))

    def test_unique_together(self):
        program = self.create_program()
        self._create_fee_structure(program=program, level='Bachelor', academic_year='2024-2025')
        with self.assertRaises(Exception):
            self._create_fee_structure(program=program, level='Bachelor', academic_year='2024-2025')


class InvoiceModelTest(TestDataMixin, TestCase):
    def test_create(self):
        invoice = self.create_invoice()
        self.assertIsNotNone(invoice.pk)

    def test_str(self):
        invoice = self.create_invoice(invoice_code='INV-001')
        self.assertIn('INV-001', str(invoice))

    def test_default_payment_not_complete(self):
        invoice = self.create_invoice()
        self.assertFalse(invoice.payment_complete)

    def test_is_overdue_no_due_date(self):
        invoice = self.create_invoice(due_date=None)
        self.assertFalse(invoice.is_overdue())

    def test_is_overdue_paid(self):
        invoice = self.create_invoice(
            due_date=date.today() - timedelta(days=1),
            payment_complete=True,
        )
        self.assertFalse(invoice.is_overdue())

    def test_is_overdue_past_due(self):
        invoice = self.create_invoice(
            due_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(invoice.is_overdue())

    def test_is_not_overdue_future_due(self):
        invoice = self.create_invoice(
            due_date=date.today() + timedelta(days=30),
        )
        self.assertFalse(invoice.is_overdue())


class PaymentPlanModelTest(TestDataMixin, TestCase):
    def _create_plan(self):
        invoice = self.create_invoice()
        plan = PaymentPlan.objects.create(
            invoice=invoice,
            total_amount=Decimal('3000.00'),
            number_of_installments=3,
            installment_amount=Decimal('1000.00'),
        )
        for i in range(1, 4):
            Installment.objects.create(
                payment_plan=plan,
                installment_number=i,
                amount=Decimal('1000.00'),
                due_date=date.today() + timedelta(days=30 * i),
            )
        return plan

    def test_create(self):
        plan = self._create_plan()
        self.assertIsNotNone(plan.pk)

    def test_str(self):
        plan = self._create_plan()
        self.assertIn('3 installments', str(plan))

    def test_get_paid_installments_none_paid(self):
        plan = self._create_plan()
        self.assertEqual(plan.get_paid_installments(), 0)

    def test_get_paid_installments_one_paid(self):
        plan = self._create_plan()
        inst = plan.installments.first()
        inst.paid = True
        inst.save()
        self.assertEqual(plan.get_paid_installments(), 1)

    def test_get_remaining_installments(self):
        plan = self._create_plan()
        self.assertEqual(plan.get_remaining_installments(), 3)

    def test_get_remaining_amount(self):
        plan = self._create_plan()
        self.assertEqual(plan.get_remaining_amount(), Decimal('3000.00'))

    def test_get_remaining_amount_after_payment(self):
        plan = self._create_plan()
        inst = plan.installments.first()
        inst.paid = True
        inst.save()
        self.assertEqual(plan.get_remaining_amount(), Decimal('2000.00'))


class InstallmentModelTest(TestDataMixin, TestCase):
    def _create_installment(self, **overrides):
        invoice = self.create_invoice()
        plan = PaymentPlan.objects.create(
            invoice=invoice,
            total_amount=Decimal('1000.00'),
            number_of_installments=1,
            installment_amount=Decimal('1000.00'),
        )
        defaults = {
            'payment_plan': plan,
            'installment_number': 1,
            'amount': Decimal('1000.00'),
            'due_date': date.today() + timedelta(days=30),
        }
        defaults.update(overrides)
        return Installment.objects.create(**defaults)

    def test_create(self):
        inst = self._create_installment()
        self.assertIsNotNone(inst.pk)

    def test_str(self):
        inst = self._create_installment()
        self.assertIn('Installment 1', str(inst))

    def test_default_not_paid(self):
        inst = self._create_installment()
        self.assertFalse(inst.paid)

    def test_is_overdue_unpaid_past(self):
        inst = self._create_installment(
            due_date=date.today() - timedelta(days=1),
        )
        self.assertTrue(inst.is_overdue())

    def test_is_overdue_paid(self):
        inst = self._create_installment(
            due_date=date.today() - timedelta(days=1),
            paid=True,
        )
        self.assertFalse(inst.is_overdue())

    def test_is_not_overdue_future(self):
        inst = self._create_installment(
            due_date=date.today() + timedelta(days=30),
        )
        self.assertFalse(inst.is_overdue())


class PaymentModelTest(TestDataMixin, TestCase):
    def _create_payment(self, **overrides):
        invoice = overrides.pop('invoice', None) or self.create_invoice()
        from tests.helpers import _next_counter
        n = _next_counter()
        defaults = {
            'invoice': invoice,
            'amount': Decimal('1000.00'),
            'payment_gateway': 'stripe',
            'transaction_id': f'txn_{n:06d}',
            'status': 'pending',
        }
        defaults.update(overrides)
        return Payment.objects.create(**defaults)

    def test_create(self):
        payment = self._create_payment()
        self.assertIsNotNone(payment.pk)

    def test_str(self):
        payment = self._create_payment(transaction_id='txn_test')
        self.assertIn('txn_test', str(payment))
        self.assertIn('pending', str(payment))

    def test_default_status_pending(self):
        payment = self._create_payment()
        self.assertEqual(payment.status, 'pending')

    def test_unique_transaction_id(self):
        self._create_payment(transaction_id='txn_dup')
        with self.assertRaises(Exception):
            self._create_payment(transaction_id='txn_dup')


class PaymentVerificationModelTest(TestDataMixin, TestCase):
    def _create_verification(self):
        invoice = self.create_invoice()
        from tests.helpers import _next_counter
        n = _next_counter()
        payment = Payment.objects.create(
            invoice=invoice, amount=Decimal('500.00'),
            payment_gateway='cash', transaction_id=f'txn_ver_{n}',
        )
        return PaymentVerification.objects.create(payment=payment)

    def test_create(self):
        ver = self._create_verification()
        self.assertIsNotNone(ver.pk)

    def test_default_pending(self):
        ver = self._create_verification()
        self.assertEqual(ver.verification_status, 'pending')

    def test_verify(self):
        ver = self._create_verification()
        admin = self.create_admin_user()
        ver.verify(admin, notes='Looks good')
        ver.refresh_from_db()
        self.assertEqual(ver.verification_status, 'verified')
        self.assertEqual(ver.verified_by, admin)
        self.assertIsNotNone(ver.verified_at)
        ver.payment.refresh_from_db()
        self.assertEqual(ver.payment.status, 'completed')

    def test_reject(self):
        ver = self._create_verification()
        admin = self.create_admin_user()
        ver.reject(admin, notes='Suspicious')
        ver.refresh_from_db()
        self.assertEqual(ver.verification_status, 'rejected')
        ver.payment.refresh_from_db()
        self.assertEqual(ver.payment.status, 'failed')

    def test_str(self):
        ver = self._create_verification()
        self.assertIn('pending', str(ver))


class ReceiptModelTest(TestDataMixin, TestCase):
    def test_create(self):
        invoice = self.create_invoice()
        from tests.helpers import _next_counter
        n = _next_counter()
        payment = Payment.objects.create(
            invoice=invoice, amount=Decimal('500.00'),
            payment_gateway='stripe', transaction_id=f'txn_rcpt_{n}',
        )
        receipt = Receipt.objects.create(
            payment=payment, receipt_number=f'REC-{n:06d}',
        )
        self.assertIsNotNone(receipt.pk)

    def test_str(self):
        invoice = self.create_invoice()
        from tests.helpers import _next_counter
        n = _next_counter()
        payment = Payment.objects.create(
            invoice=invoice, amount=Decimal('500.00'),
            payment_gateway='stripe', transaction_id=f'txn_rcpt_str_{n}',
        )
        receipt = Receipt.objects.create(
            payment=payment, receipt_number=f'REC-STR-{n:06d}',
        )
        self.assertIn(f'REC-STR-{n:06d}', str(receipt))
