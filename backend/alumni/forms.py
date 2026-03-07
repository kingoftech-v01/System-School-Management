from django import forms
from .models import Alumni, AlumniEvent, AlumniDonation, AlumniAchievement


class AlumniForm(forms.ModelForm):
    class Meta:
        model = Alumni
        fields = [
            'graduation_year', 'current_occupation', 'current_employer',
            'industry', 'job_title', 'personal_email', 'phone',
            'linkedin_url', 'city', 'country', 'willing_to_mentor',
        ]
        widgets = {
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'current_occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'current_employer': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'willing_to_mentor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AlumniEventForm(forms.ModelForm):
    class Meta:
        model = AlumniEvent
        fields = [
            'title', 'description', 'event_type', 'event_date', 'end_date',
            'location', 'venue_details', 'max_attendees',
            'registration_deadline', 'registration_fee',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'event_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'venue_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'max_attendees': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DonationForm(forms.ModelForm):
    class Meta:
        model = AlumniDonation
        fields = ['amount', 'purpose', 'purpose_details', 'is_anonymous']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'purpose': forms.Select(attrs={'class': 'form-select'}),
            'purpose_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AlumniAchievementForm(forms.ModelForm):
    class Meta:
        model = AlumniAchievement
        fields = [
            'achievement_type', 'title', 'description',
            'achievement_date', 'image', 'url',
        ]
        widgets = {
            'achievement_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'achievement_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
        }
