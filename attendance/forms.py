"""
Attendance Forms - Django forms for attendance management.

This module provides forms for:
- Taking attendance
- Managing students, groups, and subjects
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Attendance, AttendanceReport, Student, Group, Subject


class AttendanceForm(forms.ModelForm):
    """Form for creating an attendance session."""

    class Meta:
        model = Attendance
        fields = ['subject', 'group', 'date']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.lecturer = kwargs.pop('lecturer', None)
        super().__init__(*args, **kwargs)


class AttendanceReportForm(forms.ModelForm):
    """Form for marking individual student attendance."""

    class Meta:
        model = AttendanceReport
        fields = ['student', 'status']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class StudentForm(forms.ModelForm):
    """Form for creating/editing students."""

    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'group']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
        }


class GroupForm(forms.ModelForm):
    """Form for creating/editing groups."""

    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SubjectForm(forms.ModelForm):
    """Form for creating/editing subjects."""

    class Meta:
        model = Subject
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
        }
