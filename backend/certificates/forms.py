"""
Certificates Forms - Django forms for certificate management.

This module provides forms for:
- Creating and editing certificate templates
- Issuing certificates
- Public certificate verification
- Batch certificate generation
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import CertificateTemplate, Certificate, BatchCertificateGeneration
from course.models import Course
from accounts.models import Student


class CertificateTemplateForm(forms.ModelForm):
    """Form for creating/editing certificate templates."""

    class Meta:
        model = CertificateTemplate
        fields = ['name', 'description', 'template_file', 'background_image',
                  'title_text', 'body_template', 'signature_1_name', 'signature_1_title',
                  'signature_1_image', 'signature_2_name', 'signature_2_title',
                  'signature_2_image', 'orientation', 'page_size', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template_file': forms.FileInput(attrs={'class': 'form-control'}),
            'background_image': forms.FileInput(attrs={'class': 'form-control'}),
            'title_text': forms.TextInput(attrs={'class': 'form-control'}),
            'body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'signature_1_name': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_1_title': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_1_image': forms.FileInput(attrs={'class': 'form-control'}),
            'signature_2_name': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_2_title': forms.TextInput(attrs={'class': 'form-control'}),
            'signature_2_image': forms.FileInput(attrs={'class': 'form-control'}),
            'orientation': forms.Select(attrs={'class': 'form-select'}),
            'page_size': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CertificateForm(forms.ModelForm):
    """Form for issuing certificates."""

    class Meta:
        model = Certificate
        fields = ['student', 'course', 'template', 'completion_date', 'grade', 'gpa', 'credits']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        course = cleaned_data.get('course')

        # Check if certificate already exists for this student-course combination
        if student and course:
            if Certificate.objects.filter(student=student, course=course).exists():
                raise forms.ValidationError(
                    _('A certificate already exists for this student and course.')
                )

        return cleaned_data


class CertificateVerificationForm(forms.Form):
    """Form for public certificate verification."""

    certificate_number = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter certificate number (e.g., CERT-2024-ABC12345)')
        }),
        label=_('Certificate Number'),
        help_text=_('Enter the certificate number exactly as shown on the certificate')
    )

    def clean_certificate_number(self):
        cert_number = self.cleaned_data.get('certificate_number')
        # Normalize certificate number (remove spaces, convert to uppercase)
        cert_number = cert_number.strip().upper()
        return cert_number


class BatchCertificateGenerationForm(forms.ModelForm):
    """Form for creating batch certificate generation jobs."""

    class Meta:
        model = BatchCertificateGeneration
        fields = ['course', 'template', 'min_grade', 'min_gpa']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'template': forms.Select(attrs={'class': 'form-select'}),
            'min_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'min_gpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        template = cleaned_data.get('template')

        if template and not template.is_active:
            raise forms.ValidationError(
                _('Cannot use inactive template for batch generation.')
            )

        return cleaned_data
