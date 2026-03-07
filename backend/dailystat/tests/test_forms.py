"""Tests for dailystat app forms."""

from datetime import date, timedelta
from django.test import TestCase

from dailystat.forms import DailyStatFilterForm


class DailyStatFilterFormTest(TestCase):
    def test_valid_empty(self):
        form = DailyStatFilterForm(data={})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_single_date(self):
        form = DailyStatFilterForm(data={'date': '2024-06-15'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_date_range(self):
        form = DailyStatFilterForm(data={
            'start_date': '2024-01-01',
            'end_date': '2024-03-01',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_range_start_after_end(self):
        form = DailyStatFilterForm(data={
            'start_date': '2024-12-01',
            'end_date': '2024-01-01',
        })
        self.assertFalse(form.is_valid())

    def test_range_exceeds_90_days(self):
        start = date(2024, 1, 1)
        end = start + timedelta(days=91)
        form = DailyStatFilterForm(data={
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
        })
        self.assertFalse(form.is_valid())

    def test_range_exactly_90_days(self):
        start = date(2024, 1, 1)
        end = start + timedelta(days=90)
        form = DailyStatFilterForm(data={
            'start_date': start.isoformat(),
            'end_date': end.isoformat(),
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_start_date_only(self):
        form = DailyStatFilterForm(data={'start_date': '2024-01-01'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_end_date_only(self):
        form = DailyStatFilterForm(data={'end_date': '2024-12-31'})
        self.assertTrue(form.is_valid(), form.errors)
