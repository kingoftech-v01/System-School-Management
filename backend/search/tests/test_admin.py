"""Tests for search admin configuration."""

from django.test import TestCase

from tests.helpers import TestDataMixin


class SearchAdminTest(TestDataMixin, TestCase):
    """Test search admin configuration.

    The search admin.py is empty (no custom registrations)
    so we verify the module loads without errors.
    """

    def test_search_admin_module_loads(self):
        """Verify the search admin module can be imported."""
        import search.admin  # noqa: F401
        self.assertTrue(True)
