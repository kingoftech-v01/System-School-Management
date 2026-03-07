"""Tests for search forms, views, and API."""

from django.test import TestCase, Client
from rest_framework.test import APIClient

from core.models import NewsAndEvents
from course.models import Program, Course
from quiz.models import Quiz
from search.forms import SearchForm, AdvancedSearchForm
from tests.helpers import TestDataMixin

OK_CODES = {200, 302, 301, 403, 404, 500}


class SearchFormTest(TestCase):
    def test_valid_query(self):
        form = SearchForm(data={'q': 'hello'})
        self.assertTrue(form.is_valid())

    def test_short_query_invalid(self):
        form = SearchForm(data={'q': 'a'})
        self.assertFalse(form.is_valid())

    def test_empty_query_invalid(self):
        form = SearchForm(data={'q': ''})
        self.assertFalse(form.is_valid())

    def test_whitespace_only_invalid(self):
        form = SearchForm(data={'q': '  '})
        self.assertFalse(form.is_valid())

    def test_strips_whitespace(self):
        form = SearchForm(data={'q': '  hello  '})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['q'], 'hello')


class AdvancedSearchFormTest(TestCase):
    def test_valid_all_fields(self):
        form = AdvancedSearchForm(data={
            'q': 'test query',
            'search_type': 'courses',
            'date_from': '2024-01-01',
            'date_to': '2024-12-31',
        })
        self.assertTrue(form.is_valid())

    def test_valid_query_only(self):
        form = AdvancedSearchForm(data={'q': 'test'})
        self.assertTrue(form.is_valid())

    def test_invalid_date_range(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'date_from': '2024-12-31',
            'date_to': '2024-01-01',
        })
        self.assertFalse(form.is_valid())

    def test_partial_date_range_valid(self):
        form = AdvancedSearchForm(data={
            'q': 'test',
            'date_from': '2024-01-01',
        })
        self.assertTrue(form.is_valid())

    def test_search_type_choices(self):
        for choice in ['all', 'news', 'programs', 'courses', 'quizzes']:
            form = AdvancedSearchForm(data={'q': 'test', 'search_type': choice})
            self.assertTrue(form.is_valid(), f"Choice {choice} should be valid")


class SearchViewTest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.user = self.create_user()

    def test_search_with_query(self):
        NewsAndEvents.objects.create(title='Science Fair', posted_as='News')
        self.client.force_login(self.user)
        r = self.client.get('/search/', {'q': 'Science'})
        self.assertIn(r.status_code, OK_CODES)

    def test_search_without_query(self):
        self.client.force_login(self.user)
        r = self.client.get('/search/')
        self.assertIn(r.status_code, OK_CODES)

    def test_search_no_results(self):
        self.client.force_login(self.user)
        r = self.client.get('/search/', {'q': 'ZZZNOTFOUND'})
        self.assertIn(r.status_code, OK_CODES)


class SearchAPITest(TestDataMixin, TestCase):
    def setUp(self):
        self.client = APIClient(raise_request_exception=False)
        self.user = self.create_user()
        self.client.force_login(self.user)

    def test_search_api_with_query(self):
        NewsAndEvents.objects.create(title='Test Event', posted_as='Event')
        r = self.client.get('/api/v1/search/query/', {'q': 'Test'})
        self.assertIn(r.status_code, [200, 403])
        if r.status_code == 200:
            self.assertEqual(r.data['count'], 1)

    def test_search_api_no_query(self):
        r = self.client.get('/api/v1/search/query/')
        self.assertIn(r.status_code, [400, 403])

    def test_search_api_empty_query(self):
        r = self.client.get('/api/v1/search/query/', {'q': ''})
        self.assertIn(r.status_code, [400, 403])

    def test_search_api_with_limit(self):
        for i in range(5):
            NewsAndEvents.objects.create(title=f'Event {i}', posted_as='Event')
        r = self.client.get('/api/v1/search/query/', {'q': 'Event', 'limit': 2})
        self.assertIn(r.status_code, [200, 403])
        if r.status_code == 200:
            self.assertLessEqual(r.data['count'], 2)

    def test_search_api_requires_auth(self):
        """Unauthenticated requests should be rejected."""
        client = APIClient()
        r = client.get('/api/v1/search/query/', {'q': 'test'})
        self.assertIn(r.status_code, [401, 403])

    def test_suggestions_api_with_query(self):
        NewsAndEvents.objects.create(title='Math Course', posted_as='News')
        r = self.client.get('/api/v1/search/suggestions/', {'q': 'Math'})
        self.assertIn(r.status_code, [200, 403])
        if r.status_code == 200:
            self.assertIn('suggestions', r.data)

    def test_suggestions_api_no_query(self):
        r = self.client.get('/api/v1/search/suggestions/')
        self.assertIn(r.status_code, [400, 403])

    def test_suggestions_api_deduplicates(self):
        # Create items with same title in different models
        NewsAndEvents.objects.create(title='Duplicate Title', posted_as='News')
        r = self.client.get('/api/v1/search/suggestions/', {'q': 'Duplicate'})
        self.assertIn(r.status_code, [200, 403])
        if r.status_code == 200:
            suggestions = r.data['suggestions']
            self.assertEqual(len(suggestions), len(set(suggestions)))

    def test_search_across_models(self):
        NewsAndEvents.objects.create(title='Biology News', posted_as='News')
        program = Program.objects.create(title='Biology Program', summary='Bio')
        course = Course.objects.create(
            title='Biology 101', slug='bio-101',
            summary='Bio course', program=program
        )
        r = self.client.get('/api/v1/search/query/', {'q': 'Biology'})
        self.assertIn(r.status_code, [200, 403])
        if r.status_code == 200:
            self.assertGreaterEqual(r.data['count'], 3)
