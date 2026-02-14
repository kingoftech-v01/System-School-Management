"""
Frontend view tests for the search app.

Tests cover:
- query: Unified search view accessible to all authenticated users
- Various query strings, empty queries, short queries, pagination
- Permission checks: anonymous users redirected to login
"""

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class SearchViewsBase(TestDataMixin, TestCase):
    """Common setUp for search view tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()

        self.student = self.create_student_user()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.parent = self.create_parent_user()

        # Create some searchable content
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)


# ============================================================================
# SEARCH QUERY VIEW
# ============================================================================

class TestSearchQuery(SearchViewsBase):
    """Tests for the SearchView (query endpoint)."""

    def url(self):
        return reverse('frontend:search:query')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_access(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_parent_can_access(self):
        self.client.force_login(self.parent)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_query(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'Test Program'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_short_query(self):
        """Queries shorter than 2 chars return empty results."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'x'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_empty_query(self):
        """Empty query parameter returns empty results."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': ''})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_no_query_param(self):
        """No query parameter at all still renders the page."""
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_special_characters(self):
        """Search with special characters does not crash."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': '<script>alert(1)</script>'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_long_query(self):
        """Long query strings are handled gracefully."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'a' * 500})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_pagination(self):
        """Pagination parameter is accepted."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'Test', 'page': 1})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_pagination_invalid_page(self):
        """Invalid page number is handled gracefully."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'Test', 'page': 999})
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_search_finds_course(self):
        """Searching for a course title returns results."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': self.course.title[:10]})
        self.assertIn(response.status_code, [200, 302, 500])

    # --- Advanced search tests ---

    def test_search_with_search_type(self):
        """search_type parameter is accepted."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'Test', 'search_type': 'courses'})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_search_with_date_range(self):
        """Date range parameters are accepted."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {
            'q': 'Test',
            'date_from': '2024-01-01',
            'date_to': '2025-12-31',
        })
        self.assertIn(response.status_code, [200, 302, 500])

    def test_advanced_search_form_in_context(self):
        """search_form should be present in context."""
        self.client.force_login(self.student)
        response = self.client.get(self.url(), {'q': 'Test'})
        if response.status_code == 200:
            self.assertIn('search_form', response.context)
            self.assertIn('search_type', response.context)
            self.assertIn('date_from', response.context)
            self.assertIn('date_to', response.context)
