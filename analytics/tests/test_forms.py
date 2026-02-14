"""Tests for analytics app forms."""

from datetime import date, timedelta
from django.test import TestCase

from tests.helpers import TestDataMixin
from analytics.forms import DateRangeFilterForm, LearningOutcomeForm, AtRiskInterventionForm
from analytics.models import LearningOutcome, AtRiskStudent


class DateRangeFilterFormTest(TestDataMixin, TestCase):
    def test_valid_date_range(self):
        data = {
            'start_date': '2024-01-01',
            'end_date': '2024-06-01',
        }
        form = DateRangeFilterForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_both_fields_optional(self):
        form = DateRangeFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_start_only(self):
        form = DateRangeFilterForm(data={'start_date': '2024-01-01'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_end_only(self):
        form = DateRangeFilterForm(data={'end_date': '2024-06-01'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_start_after_end_invalid(self):
        data = {
            'start_date': '2024-06-01',
            'end_date': '2024-01-01',
        }
        form = DateRangeFilterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_range_exceeds_365_days(self):
        data = {
            'start_date': '2023-01-01',
            'end_date': '2024-12-31',
        }
        form = DateRangeFilterForm(data=data)
        self.assertFalse(form.is_valid())

    def test_exactly_365_days_valid(self):
        start = date(2024, 1, 1)
        end = start + timedelta(days=365)
        data = {
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
        }
        form = DateRangeFilterForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class LearningOutcomeFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.course = self.create_course()

    def test_valid_form(self):
        data = {
            'course': self.course.pk,
            'outcome_name': 'Understand OOP',
            'description': 'Student understands object-oriented programming.',
            'assessment_method': 'quiz',
            'target_percentage': '70.00',
            'is_active': True,
        }
        form = LearningOutcomeForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_target_below_zero_invalid(self):
        data = {
            'course': self.course.pk,
            'outcome_name': 'Test',
            'assessment_method': 'exam',
            'target_percentage': '-5',
            'is_active': True,
        }
        form = LearningOutcomeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('target_percentage', form.errors)

    def test_target_above_100_invalid(self):
        data = {
            'course': self.course.pk,
            'outcome_name': 'Test',
            'assessment_method': 'exam',
            'target_percentage': '150',
            'is_active': True,
        }
        form = LearningOutcomeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('target_percentage', form.errors)

    def test_missing_required_fields(self):
        form = LearningOutcomeForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('course', form.errors)
        self.assertIn('outcome_name', form.errors)
        self.assertIn('assessment_method', form.errors)


class AtRiskInterventionFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'intervention_notes': 'Called the student and discussed their performance. Set up tutoring sessions.',
            'intervention_needed': True,
        }
        form = AtRiskInterventionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_short_notes_invalid(self):
        data = {
            'intervention_notes': 'short',
            'intervention_needed': True,
        }
        form = AtRiskInterventionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('intervention_notes', form.errors)

    def test_empty_notes_valid(self):
        """Empty notes should be valid since notes field is not required."""
        data = {
            'intervention_notes': '',
            'intervention_needed': False,
        }
        form = AtRiskInterventionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_exactly_ten_char_notes_valid(self):
        data = {
            'intervention_notes': 'Exactly 10',
            'intervention_needed': True,
        }
        form = AtRiskInterventionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
