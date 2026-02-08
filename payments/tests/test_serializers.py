"""Tests for payments app serializers."""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase

from payments.serializers import (
    FeeStructureSerializer,
    InvoiceSerializer,
    PaymentPlanSerializer,
    InstallmentSerializer,
    PaymentSerializer,
    PaymentVerificationSerializer,
    ReceiptSerializer,
)
from payments.models import (
    FeeStructure, Invoice, PaymentPlan, Installment,
    Payment, PaymentVerification, Receipt,
)
from tests.helpers import TestDataMixin, _next_counter


class FeeStructureSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        program = self.create_program()
        fee = FeeStructure.objects.create(
            program=program, level='Bachelor',
            academic_year='2024-2025', tuition_fee=Decimal('5000.00'),
        )
        serializer = FeeStructureSerializer(fee)
        data = serializer.data
        self.assertIn('total_fee', data)
        self.assertIn('program_name', data)


class InvoiceSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        invoice = self.create_invoice()
        serializer = InvoiceSerializer(invoice)
        data = serializer.data
        self.assertIn('is_overdue', data)

    def test_is_overdue_field(self):
        invoice = self.create_invoice(
            due_date=date.today() - timedelta(days=1),
        )
        serializer = InvoiceSerializer(invoice)
        self.assertTrue(serializer.data['is_overdue'])


class PaymentPlanSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        invoice = self.create_invoice()
        plan = PaymentPlan.objects.create(
            invoice=invoice,
            total_amount=Decimal('1000.00'),
            number_of_installments=2,
            installment_amount=Decimal('500.00'),
        )
        serializer = PaymentPlanSerializer(plan)
        data = serializer.data
        self.assertIn('remaining_installments', data)
        self.assertIn('remaining_amount', data)


class InstallmentSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        invoice = self.create_invoice()
        plan = PaymentPlan.objects.create(
            invoice=invoice,
            total_amount=Decimal('1000.00'),
            number_of_installments=1,
            installment_amount=Decimal('1000.00'),
        )
        inst = Installment.objects.create(
            payment_plan=plan, installment_number=1,
            amount=Decimal('1000.00'),
            due_date=date.today() + timedelta(days=30),
        )
        serializer = InstallmentSerializer(inst)
        self.assertIn('is_overdue', serializer.data)


class PaymentSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        invoice = self.create_invoice()
        n = _next_counter()
        payment = Payment.objects.create(
            invoice=invoice, amount=Decimal('500.00'),
            payment_gateway='stripe', transaction_id=f'txn_ser_{n}',
        )
        serializer = PaymentSerializer(payment)
        data = serializer.data
        self.assertIn('status', data)


class PaymentVerificationSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        invoice = self.create_invoice()
        n = _next_counter()
        payment = Payment.objects.create(
            invoice=invoice, amount=Decimal('500.00'),
            payment_gateway='cash', transaction_id=f'txn_vser_{n}',
        )
        ver = PaymentVerification.objects.create(payment=payment)
        serializer = PaymentVerificationSerializer(ver)
        self.assertIn('verification_status', serializer.data)


class ReceiptSerializerTest(TestDataMixin, TestCase):
    def test_serializes(self):
        invoice = self.create_invoice()
        n = _next_counter()
        payment = Payment.objects.create(
            invoice=invoice, amount=Decimal('500.00'),
            payment_gateway='stripe', transaction_id=f'txn_rser_{n}',
        )
        receipt = Receipt.objects.create(
            payment=payment, receipt_number=f'REC-SER-{n}',
        )
        serializer = ReceiptSerializer(receipt)
        self.assertIn('receipt_number', serializer.data)
