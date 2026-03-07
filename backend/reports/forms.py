from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import Student
from attendance.models import Group


class ExportReasonForm(forms.Form):
    """Required reason before exporting sensitive student records."""
    reason = forms.CharField(
        label=_('Reason for export'),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _(
                'e.g. Police request ref #12345, custody hearing, '
                'transfer documentation...'
            ),
        }),
        help_text=_(
            'This reason will be recorded in the export audit log.'
        ),
    )


class AttendanceReportFilterForm(forms.Form):
    """Filters for attendance report export."""
    FORMAT_CHOICES = (
        ('pdf', _('PDF')),
        ('csv', _('CSV')),
        ('xlsx', _('Excel')),
    )

    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        label=_('Student'),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label=_('Class / Group'),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    date_from = forms.DateField(
        required=False,
        label=_('From date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
        }),
    )
    date_to = forms.DateField(
        required=False,
        label=_('To date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
        }),
    )
    export_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='pdf',
        label=_('Export format'),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('student') and not cleaned.get('group'):
            raise forms.ValidationError(
                _('Please select either a student or a class/group.')
            )
        return cleaned


class DisciplineHistoryFilterForm(forms.Form):
    """Filters for discipline history export."""
    date_from = forms.DateField(
        required=False,
        label=_('From date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
        }),
    )
    date_to = forms.DateField(
        required=False,
        label=_('To date'),
        widget=forms.DateInput(attrs={
            'class': 'form-control', 'type': 'date',
        }),
    )


class GradesExportFilterForm(forms.Form):
    """Filters for grades export."""
    FORMAT_CHOICES = (
        ('csv', _('CSV')),
        ('xlsx', _('Excel')),
    )

    export_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='csv',
        label=_('Export format'),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
