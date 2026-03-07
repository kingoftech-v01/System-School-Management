"""
Notices Forms - Django forms for notice creation and management.

This module provides forms for:
- Creating and editing notices
- Validating notice input

All forms use Django's form validation.
"""

from django import forms
from .models import Notice, NotifyGroup


# ============================================================================
# NOTICE FORMS
# ============================================================================

class NoticeForm(forms.ModelForm):
    """
    Form for creating and editing notices.

    Fields:
    - title: Notice title
    - content: Rich text content
    - priority: Priority level
    - notify_groups: Groups to notify
    - expires_at: Optional expiration date
    - is_active: Active status
    """

    class Meta:
        model = Notice
        fields = [
            'title',
            'content',
            'priority',
            'notify_groups',
            'expires_at',
            'is_active',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter notice title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notify_groups': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'expires_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        """Validate title length and content."""
        title = self.cleaned_data.get('title', '').strip()

        if len(title) < 5:
            raise forms.ValidationError('Notice title must be at least 5 characters long.')

        return title

    def clean_expires_at(self):
        """Ensure expiry date is in the future."""
        expires_at = self.cleaned_data.get('expires_at')

        if expires_at:
            from django.utils import timezone
            if expires_at < timezone.now().date():
                raise forms.ValidationError('Expiry date must be in the future.')

        return expires_at


class NotifyGroupForm(forms.ModelForm):
    """Form for creating and editing notify groups."""

    class Meta:
        model = NotifyGroup
        fields = ['name', 'description', 'users']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Group name...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'users': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
