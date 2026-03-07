"""
Payments Serializers - DRF serializers for payments and invoices API.
"""

from rest_framework import serializers
from .models import FeeStructure, Invoice, PaymentPlan, Installment, Payment, PaymentVerification, Receipt


class FeeStructureSerializer(serializers.ModelSerializer):
    program_name = serializers.CharField(source='program.title', read_only=True)
    total_fee = serializers.SerializerMethodField()

    class Meta:
        model = FeeStructure
        fields = '__all__'

    def get_total_fee(self, obj):
        return obj.get_total_fee()


class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True, allow_null=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = '__all__'

    def get_is_overdue(self, obj):
        return obj.is_overdue()


class PaymentPlanSerializer(serializers.ModelSerializer):
    remaining_installments = serializers.SerializerMethodField()
    remaining_amount = serializers.SerializerMethodField()

    class Meta:
        model = PaymentPlan
        fields = '__all__'

    def get_remaining_installments(self, obj):
        return obj.get_remaining_installments()

    def get_remaining_amount(self, obj):
        return obj.get_remaining_amount()


class InstallmentSerializer(serializers.ModelSerializer):
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Installment
        fields = '__all__'

    def get_is_overdue(self, obj):
        return obj.is_overdue()


class PaymentSerializer(serializers.ModelSerializer):
    invoice_code = serializers.CharField(source='invoice.invoice_code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class PaymentVerificationSerializer(serializers.ModelSerializer):
    payment_transaction_id = serializers.CharField(source='payment.transaction_id', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True, allow_null=True)

    class Meta:
        model = PaymentVerification
        fields = '__all__'


class ReceiptSerializer(serializers.ModelSerializer):
    payment_amount = serializers.DecimalField(source='payment.amount', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Receipt
        fields = '__all__'
