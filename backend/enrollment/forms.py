"""
Forms for student enrollment and registration.
"""

import os

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import RegistrationForm, EnrollmentDocument


class RegistrationFormStep1(forms.ModelForm):
    """Step 1: Student Basic Information."""

    class Meta:
        model = RegistrationForm
        fields = [
            'student_first_name',
            'student_middle_name',
            'student_last_name',
            'date_of_birth',
            'gender',
            'nationality',
            'email',
            'phone',
            'street_address',
            'city',
            'province',
            'country',
            'postal_code',
        ]
        widgets = {
            'student_first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('First name')
            }),
            'student_middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Middle name (optional)')
            }),
            'student_last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Last name')
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter nationality')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'student@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'street_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Street address')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City')
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Province / State')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Country')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal code (optional)')
            }),
        }

    def clean_date_of_birth(self):
        """Validate date of birth (must be at least 5 years old)."""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 5:
                raise ValidationError(_('Student must be at least 5 years old.'))
            if age > 100:
                raise ValidationError(_('Please enter a valid date of birth.'))
        return dob

    def clean_email(self):
        """Validate email uniqueness within tenant."""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email already registered
            if RegistrationForm.objects.filter(
                email=email,
                status__in=['approved', 'enrolled']
            ).exists():
                raise ValidationError(_('This email is already registered.'))
        return email


class RegistrationFormStep2(forms.ModelForm):
    """Step 2: Parent/Guardian Information."""

    class Meta:
        model = RegistrationForm
        fields = [
            'parent_first_name',
            'parent_middle_name',
            'parent_last_name',
            'parent_email',
            'parent_phone',
            'parent_relationship'
        ]
        widgets = {
            'parent_first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Parent first name')
            }),
            'parent_middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Parent middle name (optional)')
            }),
            'parent_last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Parent last name')
            }),
            'parent_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'parent@example.com'
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
            'parent_relationship': forms.Select(attrs={
                'class': 'form-control'
            }, choices=[
                ('father', _('Father')),
                ('mother', _('Mother')),
                ('guardian', _('Legal Guardian')),
                ('other', _('Other')),
            ]),
        }


class RegistrationFormStep3(forms.ModelForm):
    """Step 3: Academic Information."""

    class Meta:
        model = RegistrationForm
        fields = [
            'enrollment_type',
            'filiere',
            'academic_year',
            'level',
            'previous_school'
        ]
        widgets = {
            'enrollment_type': forms.Select(attrs={'class': 'form-control'}),
            'filiere': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '2024-2025'
            }),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Leave blank if new student')
            }),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        # Filter filiere by tenant
        if tenant:
            from filieres.models import Filiere
            self.fields['filiere'].queryset = Filiere.objects.filter(tenant=tenant)


class RegistrationFormStep4(forms.ModelForm):
    """Step 4: Additional Information."""

    class Meta:
        model = RegistrationForm
        fields = [
            'special_needs',
            'medical_information'
        ]
        widgets = {
            'special_needs': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Any special needs or accommodations required (optional)')
            }),
            'medical_information': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Any medical conditions we should be aware of (optional)')
            }),
        }


class RegistrationEditForm(forms.ModelForm):
    """Form for editing a registration (Direction only)."""

    class Meta:
        model = RegistrationForm
        fields = [
            'student_first_name', 'student_middle_name', 'student_last_name',
            'date_of_birth', 'gender', 'nationality',
            'email', 'phone',
            'street_address', 'city', 'province', 'country', 'postal_code',
            'parent_first_name', 'parent_middle_name', 'parent_last_name',
            'parent_email', 'parent_phone', 'parent_relationship',
            'enrollment_type', 'filiere', 'academic_year', 'level', 'previous_school',
            'special_needs', 'medical_information',
            'status', 'review_notes', 'rejection_reason',
        ]
        widgets = {
            'student_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'student_middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'student_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_relationship': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('father', _('Father')),
                ('mother', _('Mother')),
                ('guardian', _('Legal Guardian')),
                ('other', _('Other')),
            ]),
            'enrollment_type': forms.Select(attrs={'class': 'form-control'}),
            'filiere': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'previous_school': forms.TextInput(attrs={'class': 'form-control'}),
            'special_needs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_information': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'review_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            from filieres.models import Filiere
            self.fields['filiere'].queryset = Filiere.objects.filter(tenant=tenant)


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading enrollment documents."""

    class Meta:
        model = EnrollmentDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Brief description (optional)')
            }),
        }

    ALLOWED_CONTENT_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']

    def clean_file(self):
        """Validate file size (max 10MB) and file type."""
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise ValidationError(_('File size must not exceed 10 MB.'))

            # Validate file extension
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    _('Unsupported file type "%(ext)s". Allowed: PDF, JPG, PNG, DOC, DOCX.'),
                    params={'ext': ext},
                )

            # Validate content type
            if hasattr(file, 'content_type') and file.content_type not in self.ALLOWED_CONTENT_TYPES:
                raise ValidationError(
                    _('Invalid file content type. Please upload a PDF, image, or Word document.')
                )
        return file


class RegistrationReviewForm(forms.ModelForm):
    """Form for reviewing and approving/rejecting registrations (Direction only)."""

    class Meta:
        model = RegistrationForm
        fields = ['status', 'review_notes', 'rejection_reason']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'review_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Internal review notes')
            }),
            'rejection_reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Reason for rejection (will be sent to applicant)')
            }),
        }

    def clean(self):
        """Validate that rejection reason is provided when rejecting."""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rejection_reason = cleaned_data.get('rejection_reason')

        if status == 'rejected' and not rejection_reason:
            raise ValidationError({
                'rejection_reason': _('Rejection reason is required when rejecting a registration.')
            })

        return cleaned_data


class DocumentVerificationForm(forms.ModelForm):
    """Form for verifying uploaded documents."""

    class Meta:
        model = EnrollmentDocument
        fields = ['is_verified']
        widgets = {
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EnrollmentSearchForm(forms.Form):
    """Form for searching/filtering enrollment applications."""

    student_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by student name')
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by email')
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', _('All Statuses'))] + list(RegistrationForm.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    enrollment_type = forms.ChoiceField(
        required=False,
        choices=[('', _('All Types'))] + list(RegistrationForm.ENROLLMENT_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    academic_year = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '2024-2025'
        })
    )
    filiere = forms.ModelChoiceField(
        required=False,
        queryset=None,  # Will be set in __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        # Set filiere queryset based on tenant
        if tenant:
            try:
                from filieres.models import Filiere
                self.fields['filiere'].queryset = Filiere.objects.filter(tenant=tenant)
                self.fields['filiere'].empty_label = _('All Programs')
            except:
                self.fields['filiere'].queryset = None
