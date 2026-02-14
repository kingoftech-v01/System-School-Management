from django import forms
from .models import AdmissionStudent, AdmissionSession, CounselingComment


class AdmissionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdmissionStudent
        fields = [
            'session', 'first_name', 'middle_name', 'last_name',
            'email', 'phone', 'gender', 'date_of_birth', 'nationality',
            'street_address', 'city', 'province', 'country', 'postal_code',
            'guardian_first_name', 'guardian_middle_name', 'guardian_last_name',
            'guardian_phone', 'guardian_email',
        ]
        widgets = {
            'session': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Middle name (optional)'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nationality'}),
            'street_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'province': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province / State'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal code (optional)'}),
            'guardian_first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian first name'}),
            'guardian_middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian middle name (optional)'}),
            'guardian_last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian last name'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class CounselingCommentForm(forms.ModelForm):
    class Meta:
        model = CounselingComment
        fields = ['comment', 'is_recommendation']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_recommendation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdmissionStatusForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter application email',
        })
    )
