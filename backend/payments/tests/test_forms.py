"""Tests for payments app forms."""

from decimal import Decimal
from django.test import TestCase

from payments.forms import InvoiceForm, FeeStructureForm, PaymentForm, PaymentPlanForm
from tests.helpers import TestDataMixin


class InvoiceFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        form = InvoiceForm(data={
            'student': student.pk,
            'amount': 1000,
            'description': 'Tuition payment',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_form(self):
        form = InvoiceForm(data={})
        form.is_valid()


class FeeStructureFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        program = self.create_program()
        form = FeeStructureForm(data={
            'program': program.pk,
            'level': 'bachelor',  # lowercase per LEVEL_CHOICES
            'academic_year': '2024-2025',
            'tuition_fee': '5000.00',
            'registration_fee': '100.00',
            'library_fee': '50.00',
            'lab_fee': '200.00',
            'sports_fee': '30.00',
            'other_fees': '20.00',
            'is_active': True,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_tuition(self):
        program = self.create_program()
        form = FeeStructureForm(data={
            'program': program.pk,
            'level': 'bachelor',
            'academic_year': '2024-2025',
        })
        self.assertFalse(form.is_valid())


class PaymentPlanFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        invoice = self.create_invoice()
        form = PaymentPlanForm(data={
            'invoice': invoice.pk,
            'total_amount': '3000.00',
            'number_of_installments': 3,
            'installment_amount': '1000.00',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_mismatched_amounts(self):
        invoice = self.create_invoice()
        form = PaymentPlanForm(data={
            'invoice': invoice.pk,
            'total_amount': '3000.00',
            'number_of_installments': 3,
            'installment_amount': '500.00',  # 500 * 3 = 1500, not 3000
        })
        self.assertFalse(form.is_valid())
