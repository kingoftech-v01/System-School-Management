"""
Monitoring Forms - Django forms for filtering and exporting statistics.

This module provides forms for:
- Date range filtering for statistics
- Export format selection
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class DashboardFilterForm(forms.Form):
    """
    Form for filtering dashboard statistics by date range.
    """
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('From Date')
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('To Date')
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_('From date must be before to date.'))

        return cleaned_data


class ExportFormatForm(forms.Form):
    """
    Form for selecting export format.
    """
    FORMAT_CHOICES = (
        ('csv', 'CSV'),
        ('xlsx', 'Excel (XLSX)'),
        ('json', 'JSON'),
        ('pdf', 'PDF Report'),
    )

    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Export Format')
    )
    include_charts = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Include Charts')
    )
