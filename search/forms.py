"""
Search Forms - Django forms for search functionality.

This module provides forms for:
- Basic search form with query input
- Advanced search form with filters

All forms use Django's form validation and rendering.
"""

from django import forms


# ============================================================================
# SEARCH FORMS
# ============================================================================

class SearchForm(forms.Form):
    """
    Basic search form.

    Fields:
    - q: Search query string
    """

    q = forms.CharField(
        label='Search',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for courses, programs, news, quizzes...',
            'autocomplete': 'off'
        })
    )

    def clean_q(self):
        """Validate and clean search query."""
        query = self.cleaned_data.get('q', '').strip()

        if len(query) < 2:
            raise forms.ValidationError('Search query must be at least 2 characters long.')

        return query


class AdvancedSearchForm(forms.Form):
    """
    Advanced search form with filters.

    Fields:
    - q: Search query string
    - search_type: Type of content to search (all, news, programs, courses, quizzes)
    - date_from: Filter results from this date
    - date_to: Filter results until this date
    """

    SEARCH_TYPE_CHOICES = [
        ('all', 'All Content'),
        ('news', 'News & Events'),
        ('programs', 'Programs'),
        ('courses', 'Courses'),
        ('quizzes', 'Quizzes'),
    ]

    q = forms.CharField(
        label='Search Query',
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search terms...'
        })
    )

    search_type = forms.ChoiceField(
        label='Search In',
        choices=SEARCH_TYPE_CHOICES,
        required=False,
        initial='all',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date_from = forms.DateField(
        label='From Date',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    date_to = forms.DateField(
        label='To Date',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Start date must be before end date.')

        return cleaned_data
