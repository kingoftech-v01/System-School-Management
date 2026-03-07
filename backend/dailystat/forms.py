"""
Daily Stats Forms - Django forms for filtering statistics.

This module provides forms for:
- Date selection and filtering
- Date range selection for trends
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta


class DailyStatFilterForm(forms.Form):
    """
    Form for filtering daily statistics by date or date range.
    """
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Select Date'),
        help_text=_('View statistics for a specific date')
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Start Date'),
        help_text=_('Start of date range for trends')
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('End Date'),
        help_text=_('End of date range for trends')
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_('Start date must be before end date.'))

            # Limit range to 90 days
            if (end_date - start_date).days > 90:
                raise forms.ValidationError(_('Date range cannot exceed 90 days.'))

        return cleaned_data
