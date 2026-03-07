"""
Analytics Forms - Django forms for analytics management.

This module provides forms for:
- Date range filtering
- Learning outcome management
- At-risk student intervention tracking
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta

from .models import LearningOutcome, AtRiskStudent
from course.models import Course


class DateRangeFilterForm(forms.Form):
    """Form for filtering data by date range."""

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Start Date'),
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('End Date'),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_('Start date must be before end date.'))

            # Limit range to 365 days
            if (end_date - start_date).days > 365:
                raise forms.ValidationError(_('Date range cannot exceed 365 days.'))

        return cleaned_data


class LearningOutcomeForm(forms.ModelForm):
    """Form for creating/editing learning outcomes."""

    class Meta:
        model = LearningOutcome
        fields = ['course', 'outcome_name', 'description', 'assessment_method', 'target_percentage', 'is_active']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'outcome_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assessment_method': forms.Select(attrs={'class': 'form-select'}),
            'target_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_target_percentage(self):
        target = self.cleaned_data.get('target_percentage')
        if target < 0 or target > 100:
            raise forms.ValidationError(_('Target percentage must be between 0 and 100.'))
        return target


class AtRiskInterventionForm(forms.ModelForm):
    """Form for recording interventions for at-risk students."""

    class Meta:
        model = AtRiskStudent
        fields = ['intervention_notes', 'intervention_needed']
        widgets = {
            'intervention_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'intervention_needed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_intervention_notes(self):
        notes = self.cleaned_data.get('intervention_notes')
        if notes and len(notes) < 10:
            raise forms.ValidationError(_('Please provide detailed intervention notes (at least 10 characters).'))
        return notes
