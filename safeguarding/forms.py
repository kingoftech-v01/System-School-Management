from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Incident, VisitorLog, StudentCaseNote


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'incident_type', 'title', 'description', 'severity',
            'incident_date', 'incident_time', 'location',
            'students_involved', 'staff_involved',
            'external_parties', 'witnesses',
            'actions_taken', 'follow_up_needed', 'follow_up_date',
            'follow_up_notes', 'disciplinary_action', 'status',
        ]
        widgets = {
            'incident_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'incident_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'students_involved': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'staff_involved': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'external_parties': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'witnesses': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'actions_taken': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'follow_up_needed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'follow_up_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'disciplinary_action': forms.Select(attrs={'class': 'form-control'}),
        }


class VisitorLogForm(forms.ModelForm):
    class Meta:
        model = VisitorLog
        fields = [
            'visitor_name', 'visitor_type', 'organization',
            'badge_number', 'id_verified', 'phone',
            'purpose', 'time_in',
            'host_staff', 'students_involved',
            'notes', 'approved_by',
        ]
        widgets = {
            'visitor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'visitor_type': forms.Select(attrs={'class': 'form-control'}),
            'organization': forms.TextInput(attrs={'class': 'form-control'}),
            'badge_number': forms.TextInput(attrs={'class': 'form-control'}),
            'id_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'time_in': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'host_staff': forms.Select(attrs={'class': 'form-control'}),
            'students_involved': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'approved_by': forms.Select(attrs={'class': 'form-control'}),
        }


class VisitorCheckoutForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 'rows': 2,
            'placeholder': _('Exit notes...'),
        })
    )


class StudentCaseNoteForm(forms.ModelForm):
    class Meta:
        model = StudentCaseNote
        fields = [
            'student', 'category', 'confidentiality',
            'title', 'content',
            'follow_up_date', 'related_incident',
        ]
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'confidentiality': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'related_incident': forms.Select(attrs={'class': 'form-control'}),
        }
