"""
Forms for filieres management.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import Filiere, FiliereSubject, FiliereRequirement


class FiliereForm(forms.ModelForm):
    """Form for creating/editing filieres."""

    class Meta:
        model = Filiere
        fields = [
            'name',
            'code',
            'description',
            'level',
            'duration_years',
            'capacity',
            'coordinator',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Computer Science')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., CS'),
                'maxlength': 20
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Brief description of the program...')
            }),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'duration_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Leave empty for unlimited')
            }),
            'coordinator': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)

        # Filter coordinator by tenant and role
        if tenant:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['coordinator'].queryset = User.objects.filter(
                tenant=tenant,
                role__in=['professor', 'direction']
            )

    def clean_code(self):
        """Ensure code is uppercase and unique within tenant."""
        code = self.cleaned_data.get('code', '').upper()

        # Check uniqueness within tenant (excluding current instance)
        if self.instance and self.instance.pk:
            if Filiere.objects.filter(
                tenant=self.instance.tenant,
                code=code
            ).exclude(pk=self.instance.pk).exists():
                raise ValidationError(_('A program with this code already exists.'))

        return code


class FiliereSubjectForm(forms.ModelForm):
    """Form for adding subjects to a filiere."""

    class Meta:
        model = FiliereSubject
        fields = [
            'subject',
            'coefficient',
            'is_mandatory',
            'year',
            'semester',
            'credits',
            'hours_per_week'
        ]
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.1',
                'max': '10'
            }),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'credits': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 20
            }),
            'hours_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 40
            }),
        }

    def __init__(self, *args, **kwargs):
        filiere = kwargs.pop('filiere', None)
        super().__init__(*args, **kwargs)

        # Filter subjects by tenant
        if filiere:
            from course.models import Course
            self.fields['subject'].queryset = Course.objects.filter(
                program__in=filiere.tenant.programs.all() if hasattr(filiere.tenant, 'programs') else Course.objects.none()
            )


class FiliereRequirementForm(forms.ModelForm):
    """Form for adding requirements to a filiere."""

    class Meta:
        model = FiliereRequirement
        fields = [
            'requirement_type',
            'description',
            'is_mandatory',
            'order'
        ]
        widgets = {
            'requirement_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Describe the requirement...')
            }),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }


class FiliereSearchForm(forms.Form):
    """Form for searching and filtering filieres."""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by name or code...')
        })
    )
    level = forms.ChoiceField(
        required=False,
        choices=[('', _('All Levels'))] + list(Filiere._meta.get_field('level').choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All')),
            ('true', _('Active Only')),
            ('false', _('Inactive Only'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    has_capacity = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All')),
            ('true', _('Available Spots')),
            ('false', _('Full'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
