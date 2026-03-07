"""
Payments API Views - REST API endpoints for payments and invoices.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import FeeStructure, Invoice, PaymentPlan, Installment, Payment, PaymentVerification, Receipt
from .serializers import (
    FeeStructureSerializer, InvoiceSerializer, PaymentPlanSerializer,
    InstallmentSerializer, PaymentSerializer, PaymentVerificationSerializer, ReceiptSerializer
)
from accounts.permissions import IsDirectionUser, IsAccountantOrDirectionUser, IsStudentOrParent


class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrDirectionUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['program', 'level', 'academic_year', 'is_active']
    ordering = ['-academic_year']


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated, IsStudentOrParent | IsAccountantOrDirectionUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'payment_complete', 'semester']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Invoice.objects.all()
        # Accountants and direction can see all invoices
        if getattr(user, 'role', '') in ('accountant', 'direction', 'admin'):
            return Invoice.objects.all()
        if getattr(user, 'is_parent', False):
            from accounts.models import Parent
            student_ids = Parent.objects.filter(user=user).values_list('student__student_id', flat=True)
            return Invoice.objects.filter(user_id__in=student_ids)
        return Invoice.objects.filter(user=user)


class PaymentPlanViewSet(viewsets.ModelViewSet):
    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrDirectionUser]


class InstallmentViewSet(viewsets.ModelViewSet):
    queryset = Installment.objects.all()
    serializer_class = InstallmentSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrDirectionUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_plan', 'paid']
    ordering = ['installment_number']


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrDirectionUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['invoice', 'status', 'payment_gateway']
    ordering = ['-payment_date']


class PaymentVerificationViewSet(viewsets.ModelViewSet):
    queryset = PaymentVerification.objects.all()
    serializer_class = PaymentVerificationSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrDirectionUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['verification_status']
    ordering = ['-created_at']


class ReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Receipt.objects.all()
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-generated_at']
