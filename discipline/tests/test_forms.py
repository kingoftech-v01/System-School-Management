"""Tests for discipline app forms."""

from datetime import date
from django.test import TestCase

from discipline.forms import DisciplinaryActionForm
from tests.helpers import TestDataMixin


class DisciplinaryActionFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        student = self.create_user(role='student')
        form = DisciplinaryActionForm(data={
            'student': student.pk,
            'incident_type': 'Tardiness',
            'description': 'Repeated tardiness to class',
            'action_taken': 'Verbal warning',
            'severity': 'minor',
            'incident_date': date.today().isoformat(),
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required(self):
        form = DisciplinaryActionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('student', form.errors)
        self.assertIn('incident_type', form.errors)

    def test_all_severities(self):
        student = self.create_user(role='student')
        for sev in ['minor', 'moderate', 'serious', 'critical']:
            form = DisciplinaryActionForm(data={
                'student': student.pk,
                'incident_type': 'Test',
                'description': 'Desc',
                'action_taken': 'Action',
                'severity': sev,
                'incident_date': date.today().isoformat(),
            })
            self.assertTrue(form.is_valid(), f'{sev}: {form.errors}')
