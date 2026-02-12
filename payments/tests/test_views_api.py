"""Tests for payments app API views."""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from tests.helpers import TestDataMixin
from payments.models import (
    FeeStructure, Invoice, PaymentPlan, Installment,
    Payment, PaymentVerification, Receipt,
)


class FeeStructureViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.direction_user = self.create_direction_user()
        self.client.force_authenticate(user=self.direction_user)
        self.program = self.create_program()
        self.fee = self.create_fee_structure(program=self.program)

    def test_list_fee_structures(self):
        resp = self.client.get('/api/v1/payments/fee-structures/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/payments/fee-structures/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_student_denied(self):
        student = self.create_student_user()
        self.client.force_authenticate(user=student)
        resp = self.client.get('/api/v1/payments/fee-structures/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class InvoiceViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.direction_user = self.create_direction_user()
        self.client.force_authenticate(user=self.direction_user)
        self.invoice = self.create_invoice(user=self.direction_user)

    def test_list_invoices(self):
        resp = self.client.get('/api/v1/payments/invoices/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_direction_sees_all_invoices(self):
        other_user = self.create_user(role='direction')
        self.create_invoice(user=other_user)
        resp = self.client.get('/api/v1/payments/invoices/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data['results']) if 'results' in resp.data else len(resp.data), 2)


class PaymentViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.direction_user = self.create_direction_user()
        self.client.force_authenticate(user=self.direction_user)
        self.invoice = self.create_invoice(user=self.direction_user)
        self.payment = self.create_payment(invoice=self.invoice)

    def test_list_payments(self):
        resp = self.client.get('/api/v1/payments/payments/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_payment(self):
        resp = self.client.get(f'/api/v1/payments/payments/{self.payment.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_denied(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/payments/payments/')
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class ReceiptViewSetTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = self.create_admin_user()
        self.client.force_authenticate(user=self.user)
        self.invoice = self.create_invoice(user=self.user)
        self.payment = self.create_payment(invoice=self.invoice)
        self.receipt = Receipt.objects.create(
            payment=self.payment, receipt_number='REC-API-001',
        )

    def test_list_receipts(self):
        resp = self.client.get('/api/v1/payments/receipts/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_readonly_no_post(self):
        resp = self.client.post('/api/v1/payments/receipts/', {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
