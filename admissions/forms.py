from django import forms
from .models import AdmissionStudent, AdmissionSession, CounselingComment


class AdmissionApplicationForm(forms.ModelForm):
    class Meta:
        model = AdmissionStudent
        fields = ['session', 'first_name', 'last_name', 'email', 'phone', 'gender', 'date_of_birth', 'address']
        widgets = {
            'session': forms.Select(attrs={'class': 'form-select'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
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
