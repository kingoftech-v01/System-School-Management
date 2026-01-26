"""
Forums Forms - Django forms for forum management.

This module provides forms for:
- Creating and editing threads
- Creating and editing posts
- Reporting content
- Searching forums
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from ckeditor.widgets import CKEditorWidget

from .models import Thread, Post, Report, ForumCategory, Tag


class ThreadForm(forms.ModelForm):
    """Form for creating/editing threads."""

    class Meta:
        model = Thread
        fields = ['category', 'title', 'content', 'tags']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': CKEditorWidget(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active categories
        self.fields['category'].queryset = ForumCategory.objects.filter(is_active=True)
        # Tags are optional
        self.fields['tags'].required = False

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError(_('Title must be at least 5 characters long.'))
        return title

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise forms.ValidationError(_('Content must be at least 10 characters long.'))
        return content


class PostForm(forms.ModelForm):
    """Form for creating/editing posts."""

    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': CKEditorWidget(attrs={'class': 'form-control'}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise forms.ValidationError(_('Post content must be at least 10 characters long.'))
        return content


class ReportForm(forms.ModelForm):
    """Form for reporting inappropriate content."""

    class Meta:
        model = Report
        fields = ['report_type', 'description']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 10:
            raise forms.ValidationError(_('Please provide a detailed description (at least 10 characters).'))
        return description


class SearchForm(forms.Form):
    """Form for searching forums."""

    query = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search threads and posts...')
        }),
        label=_('Search'),
    )

    def clean_query(self):
        query = self.cleaned_data.get('query')
        if len(query) < 3:
            raise forms.ValidationError(_('Search query must be at least 3 characters long.'))
        return query
