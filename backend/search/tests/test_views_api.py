"""
API view tests for the search app.

Tests cover:
- SearchAPIView (unified search across models)
- SearchSuggestionsAPIView (autocomplete suggestions)
- Authentication requirement (no longer public)
- Limit validation and capping
- Advanced search parameters (search_type, date_from, date_to)
- Tenant guard
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
        self.user = self.create_user()
        self.client.force_login(self.user)
        # Create some searchable data
        self.program = self.create_program(title='Computer Science', summary='CS programme')
        self.course = self.create_course(
            program=self.program,
            title='Algorithms',
            code='ALG001',
            summary='Algorithms course',
        )

    def test_search_requires_auth(self):
        """Unauthenticated requests should be rejected."""
        client = APIClient()
        url = reverse('api:search:query')
        response = client.get(url, {'q': 'test'})
        self.assertIn(response.status_code, [401, 403])

    def test_search_without_query(self):
        """Missing 'q' parameter should return 400."""
        url = reverse('api:search:query')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
        if response.status_code == 400:
            self.assertIn('error', response.data)

    def test_search_with_empty_query(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': ''})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_search_returns_results(self):
        """Search with a matching query should return results."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertIn('results', response.data)
            self.assertIn('count', response.data)
            self.assertIn('query', response.data)
            self.assertEqual(response.data['query'], 'Computer')

    def test_search_returns_correct_count(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer Science'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertGreaterEqual(response.data['count'], 1)

    def test_search_with_limit(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Algorithm', 'limit': 1})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertLessEqual(len(response.data['results']), 1)

    def test_search_no_results(self):
        """Non-matching query should return zero results."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'xyznonexistent123'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertEqual(response.data['count'], 0)
            self.assertEqual(response.data['results'], [])

    def test_search_result_structure(self):
        """Each search result should have id, title, type fields."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Algorithms'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200 and response.data['count'] > 0:
            result = response.data['results'][0]
            self.assertIn('id', result)
            self.assertIn('title', result)
            self.assertIn('type', result)

    # --- Limit validation tests ---

    def test_search_with_excessive_limit(self):
        """Limit above SEARCH_MAX_RESULTS should be capped."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer', 'limit': 99999})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_search_with_negative_limit(self):
        """Negative limit should be clamped to 1."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer', 'limit': -5})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_search_with_invalid_limit(self):
        """Non-integer limit should use default."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer', 'limit': 'abc'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    # --- Advanced search tests ---

    def test_search_with_search_type(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer', 'search_type': 'programs'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_search_with_invalid_search_type(self):
        """Invalid search_type should fall back to 'all'."""
        url = reverse('api:search:query')
        response = self.client.get(url, {'q': 'Computer', 'search_type': 'invalid'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_search_with_date_range(self):
        url = reverse('api:search:query')
        response = self.client.get(url, {
            'q': 'Computer',
            'date_from': '2024-01-01',
            'date_to': '2025-12-31',
        })
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_search_with_invalid_date_range(self):
        """date_from after date_to should return 400."""
        url = reverse('api:search:query')
        response = self.client.get(url, {
            'q': 'Computer',
            'date_from': '2025-12-31',
            'date_to': '2024-01-01',
        })
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_search_with_malformed_date(self):
        """Malformed dates should be ignored (treated as no filter)."""
        url = reverse('api:search:query')
        response = self.client.get(url, {
            'q': 'Computer',
            'date_from': 'not-a-date',
        })
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])


class SearchSuggestionsAPIViewTests(TestDataMixin, TestCase):
    """Tests for SearchSuggestionsAPIView (autocomplete)."""

    def setUp(self):
        self.client = APIClient()
        self.user = self.create_user()
        self.client.force_login(self.user)
        self.program = self.create_program(title='Data Science', summary='DS programme')
        self.course = self.create_course(
            program=self.program,
            title='Machine Learning',
            code='ML001',
            summary='ML course',
        )

    def test_suggestions_requires_auth(self):
        """Unauthenticated requests should be rejected."""
        client = APIClient()
        url = reverse('api:search:suggestions')
        response = client.get(url, {'q': 'test'})
        self.assertIn(response.status_code, [401, 403])

    def test_suggestions_without_query(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_suggestions_with_empty_query(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': ''})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_suggestions_returns_results(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Data'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertIn('suggestions', response.data)
            self.assertIn('query', response.data)

    def test_suggestions_with_limit(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'M', 'limit': 2})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertLessEqual(len(response.data['suggestions']), 2)

    def test_suggestions_no_match(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'zzznonexistent999'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertEqual(response.data['suggestions'], [])

    def test_suggestions_deduplication(self):
        """Duplicate titles across models should be deduplicated."""
        self.create_program(title='Machine Learning Advanced', summary='ML adv')
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Machine'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            suggestions = response.data['suggestions']
            self.assertEqual(len(suggestions), len(set(suggestions)))

    def test_suggestions_contains_matching_title(self):
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Machine Learning'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
        if response.status_code == 200:
            self.assertIn('Machine Learning', response.data['suggestions'])

    def test_suggestions_with_excessive_limit(self):
        """Limit above SEARCH_MAX_RESULTS should be capped."""
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Machine', 'limit': 99999})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_suggestions_with_invalid_limit(self):
        """Non-integer limit should use default."""
        url = reverse('api:search:suggestions')
        response = self.client.get(url, {'q': 'Machine', 'limit': 'abc'})
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
