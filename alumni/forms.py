from django import forms
from .models import Alumni, AlumniEvent

class AlumniForm(forms.ModelForm):
    class Meta:
        model = Alumni
        fields = ['graduation_year', 'current_occupation', 'current_employer', 'personal_email', 'phone', 'linkedin_url', 'willing_to_mentor']
        widgets = {
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'current_employer': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'willing_to_mentor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
