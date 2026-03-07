"""
Payments Forms - Django forms for payment and invoice management.

This module provides forms for:
- Creating and editing invoices
- Payment processing
- Fee structure management
"""

from django import forms
from .models import Invoice, FeeStructure, Payment, PaymentPlan


class InvoiceForm(forms.ModelForm):
    """
    Form for creating and editing invoices.
    """
    class Meta:
        model = Invoice
        fields = ['student', 'fee_structure', 'amount', 'due_date', 'semester', 'description']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'fee_structure': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FeeStructureForm(forms.ModelForm):
    """
    Form for creating and editing fee structures.
    """
    class Meta:
        model = FeeStructure
        fields = [
            'program', 'level', 'academic_year', 'tuition_fee', 'registration_fee',
            'library_fee', 'lab_fee', 'sports_fee', 'other_fees', 'is_active'
        ]
        widgets = {
            'program': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-2025'}),
            'tuition_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'library_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'lab_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sports_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'other_fees': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentForm(forms.ModelForm):
    """
    Form for recording payments.
    """
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_gateway', 'transaction_id']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_gateway': forms.Select(attrs={'class': 'form-select'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PaymentPlanForm(forms.ModelForm):
    """
    Form for creating payment plans.
    """
    class Meta:
        model = PaymentPlan
        fields = ['invoice', 'total_amount', 'number_of_installments', 'installment_amount']
        widgets = {
            'invoice': forms.Select(attrs={'class': 'form-select'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'number_of_installments': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'installment_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_amount = cleaned_data.get('total_amount')
        number_of_installments = cleaned_data.get('number_of_installments')
        installment_amount = cleaned_data.get('installment_amount')

        if total_amount and number_of_installments and installment_amount:
            expected_total = installment_amount * number_of_installments
            if abs(expected_total - total_amount) > 0.01:  # Allow small floating point differences
                raise forms.ValidationError(
                    f'Total amount should equal installment amount × number of installments '
                    f'({installment_amount} × {number_of_installments} = {expected_total})'
                )

        return cleaned_data
