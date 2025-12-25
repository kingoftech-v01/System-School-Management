from django import forms
from .models import DisciplinaryAction


class DisciplinaryActionForm(forms.ModelForm):
    class Meta:
        model = DisciplinaryAction
        fields = ['student', 'incident_type', 'description', 'action_taken',
                  'severity', 'incident_date', 'resolution_date', 'is_resolved']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'incident_type': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'action_taken': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'incident_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'resolution_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
