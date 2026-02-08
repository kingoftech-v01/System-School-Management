"""Tests for monitoring app forms."""

from django.test import TestCase

from monitoring.forms import DashboardFilterForm, ExportFormatForm


class DashboardFilterFormTest(TestCase):
    def test_valid_empty(self):
        form = DashboardFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_date_range(self):
        form = DashboardFilterForm(data={
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_date_range(self):
        form = DashboardFilterForm(data={
            'date_from': '2024-12-31',
            'date_to': '2024-01-01',
        })
        self.assertFalse(form.is_valid())

    def test_date_from_only(self):
        form = DashboardFilterForm(data={'date_from': '2024-01-01'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_to_only(self):
        form = DashboardFilterForm(data={'date_to': '2024-12-31'})
        self.assertTrue(form.is_valid(), form.errors)


class ExportFormatFormTest(TestCase):
    def test_valid_csv(self):
        form = ExportFormatForm(data={'format': 'csv'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_all_formats(self):
        for fmt in ['csv', 'xlsx', 'json', 'pdf']:
            form = ExportFormatForm(data={'format': fmt})
            self.assertTrue(form.is_valid(), f'{fmt}: {form.errors}')

    def test_invalid_format(self):
        form = ExportFormatForm(data={'format': 'html'})
        self.assertFalse(form.is_valid())

    def test_include_charts_default(self):
        form = ExportFormatForm(data={'format': 'csv'})
        self.assertTrue(form.is_valid())
        # include_charts is not required, defaults handled by widget
        self.assertFalse(form.cleaned_data['include_charts'])

    def test_include_charts_true(self):
        form = ExportFormatForm(data={'format': 'pdf', 'include_charts': True})
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['include_charts'])

    def test_missing_format(self):
        form = ExportFormatForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('format', form.errors)
