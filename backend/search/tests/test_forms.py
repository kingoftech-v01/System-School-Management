"""Tests for search app forms."""

from datetime import date, timedelta
from django.test import TestCase

from search.forms import SearchForm, AdvancedSearchForm


class SearchFormTest(TestCase):
    def test_valid_query(self):
        form = SearchForm(data={'q': 'python'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_query_too_short(self):
        form = SearchForm(data={'q': 'a'})
        self.assertFalse(form.is_valid())
        self.assertIn('q', form.errors)

    def test_query_stripped(self):
        form = SearchForm(data={'q': '  hello  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['q'], 'hello')

    def test_empty_query(self):
        form = SearchForm(data={'q': ''})
        self.assertFalse(form.is_valid())

    def test_whitespace_only_query(self):
        form = SearchForm(data={'q': '   '})
        self.assertFalse(form.is_valid())

    def test_missing_query(self):
        form = SearchForm(data={})
        self.assertFalse(form.is_valid())


class AdvancedSearchFormTest(TestCase):
    def test_valid_minimal(self):
        form = AdvancedSearchForm(data={'q': 'test'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_with_all_fields(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'search_type': 'courses',
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_all_search_types(self):
        for st in ['all', 'news', 'programs', 'courses', 'quizzes']:
            form = AdvancedSearchForm(data={'q': 'test', 'search_type': st})
            self.assertTrue(form.is_valid(), f'{st}: {form.errors}')

    def test_invalid_search_type(self):
        form = AdvancedSearchForm(data={'q': 'test', 'search_type': 'invalid'})
        self.assertFalse(form.is_valid())

    def test_date_range_valid(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'date_from': '2024-01-01',
            'date_to': '2024-06-01',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_range_invalid(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'date_from': '2024-12-01',
            'date_to': '2024-01-01',
        })
        self.assertFalse(form.is_valid())

    def test_date_from_only(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'date_from': '2024-01-01',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_date_to_only(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'date_to': '2024-12-31',
        })
        self.assertTrue(form.is_valid(), form.errors)
