"""
API view tests for the search app.

Tests cover:
- SearchAPIView (unified search across models)
- SearchSuggestionsAPIView (autocomplete suggestions)
- Missing query parameter validation
- Result structure
- Public access (AllowAny)
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tests.helpers import TestDataMixin


class SearchAPIViewTests(TestDataMixin, TestCase):
    """Tests for the unified SearchAPIView."""

    def setUp(self):
        self.client = APIClient()
        # Create some searchable data
        self.program = self.create_program(title='Computer Science', summary='CS programme')
        self.course = self.create_course(
            program=self.program,
            title='Algorithms',
            code='ALG001',
            summary='Algorithms course',
        )

    def test_search_without_query(self):
        """Missing 'q' parameter should return 400."""
        url = reverse('api:search:query')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_search_with_empty_query(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_returns_results(self):
        """Search with a matching query should return results."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('query', response.data)
        self.assertEqual(response.data['query'], 'Computer')

    def test_search_returns_correct_count(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer Science'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_search_with_limit(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Algorithm', 'limit': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 1)

    def test_search_no_results(self):
        """Non-matching query should return zero results."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'xyznonexistent123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    def test_search_result_structure(self):
        """Each search result should have id, title, type fields."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Algorithms'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if response.data['count'] > 0:
            result = response.data['results'][0]
            self.assertIn('id', result)
            self.assertIn('title', result)
            self.assertIn('type', result)

    def test_search_is_public(self):
        """Search endpoint uses AllowAny -- no auth needed."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SearchSuggestionsAPIViewTests(TestDataMixin, TestCase):
    """Tests for SearchSuggestionsAPIView (autocomplete)."""

    def setUp(self):
        self.client = APIClient()
        self.program = self.create_program(title='Data Science', summary='DS programme')
        self.course = self.create_course(
            program=self.program,
            title='Machine Learning',
            code='ML001',
            summary='ML course',
        )

    def test_suggestions_without_query(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suggestions_with_empty_query(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_suggestions_returns_results(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Data'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertIn('query', response.data)

    def test_suggestions_with_limit(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'M', 'limit': 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['suggestions']), 2)

    def test_suggestions_no_match(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'zzznonexistent999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['suggestions'], [])

    def test_suggestions_deduplication(self):
        """Duplicate titles across models should be deduplicated."""
        self.create_program(title='Machine Learning Advanced', summary='ML adv')
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Machine'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All suggestions should be unique
        suggestions = response.data['suggestions']
        self.assertEqual(len(suggestions), len(set(suggestions)))

    def test_suggestions_is_public(self):
        """Suggestions endpoint uses AllowAny -- no auth needed."""
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_suggestions_contains_matching_title(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Machine Learning'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Machine Learning', response.data['suggestions'])
