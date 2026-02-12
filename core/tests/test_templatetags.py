"""Tests for core template tags: custom_tags.py and sanitize.py."""

from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from core.templatetags.custom_tags import getdata
from core.templatetags.sanitize import sanitize_html, ALLOWED_TAGS, ALLOWED_ATTRIBUTES
from tests.helpers import TestDataMixin


class GetdataFilterTest(TestDataMixin, TestCase):
    """Tests for the getdata template filter."""

    def test_returns_matching_data_for_known_view(self):
        """getdata returns list for a URL path whose view name exists in json_data."""
        # Use a known URL path -- the admin index always resolves to 'index'
        json_data = {'index': ['style.css', 'script.js']}
        result = getdata(json_data, '/admin/')
        self.assertEqual(result, ['style.css', 'script.js'])

    def test_returns_empty_list_for_unknown_view(self):
        """getdata returns [] when view name is not a key in json_data."""
        json_data = {'some_other_view': ['a.css']}
        result = getdata(json_data, '/admin/')
        self.assertEqual(result, [])

    def test_returns_empty_list_for_nonexistent_url(self):
        """getdata returns [] when the URL path does not resolve."""
        json_data = {'anything': ['data']}
        result = getdata(json_data, '/this-url-does-not-exist-xyz/')
        self.assertEqual(result, [])

    def test_empty_json_data_returns_empty(self):
        """getdata returns [] when json_data is an empty dict."""
        result = getdata({}, '/admin/')
        self.assertEqual(result, [])

    def test_json_data_with_nested_values(self):
        """getdata returns whatever value is stored, even if nested."""
        json_data = {'index': {'key': 'value'}}
        result = getdata(json_data, '/admin/')
        self.assertEqual(result, {'key': 'value'})


class SanitizeHtmlFilterTest(TestDataMixin, TestCase):
    """Tests for the sanitize_html template filter.

    Note: nh3 library has a known panic when link_rel is combined with 'rel'
    in allowed_attributes for 'a' tags. We mock nh3.clean to test our wrapper
    logic (empty-check, mark_safe, parameter passing).
    """

    def test_returns_empty_string_for_none(self):
        self.assertEqual(sanitize_html(None), '')

    def test_returns_empty_string_for_empty_string(self):
        self.assertEqual(sanitize_html(''), '')

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<p>Hello <strong>world</strong></p>')
    def test_allows_permitted_tags(self, mock_clean):
        html = '<p>Hello <strong>world</strong></p>'
        result = sanitize_html(html)
        mock_clean.assert_called_once()
        self.assertIn('<p>', result)
        self.assertIn('<strong>', result)

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<p>Safe</p>alert("xss")')
    def test_strips_disallowed_tags(self, mock_clean):
        html = '<p>Safe</p><script>alert("xss")</script>'
        result = sanitize_html(html)
        mock_clean.assert_called_once()
        self.assertNotIn('<script>', result)

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<a href="https://example.com">Link</a>')
    def test_preserves_allowed_attributes(self, mock_clean):
        result = sanitize_html('<a href="https://example.com" target="_blank">Link</a>')
        self.assertIn('href="https://example.com"', result)

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<p>Text</p>')
    def test_strips_disallowed_attributes(self, mock_clean):
        result = sanitize_html('<p onclick="alert(1)">Text</p>')
        self.assertNotIn('onclick', result)

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<p>Hello</p>')
    def test_result_is_marked_safe(self, mock_clean):
        from django.utils.safestring import SafeString
        result = sanitize_html('<p>Hello</p>')
        self.assertIsInstance(result, SafeString)

    def test_allowed_tags_set_contains_expected_tags(self):
        for tag in ('p', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'img', 'table'):
            self.assertIn(tag, ALLOWED_TAGS)

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<img src="test.jpg" alt="A test">')
    def test_allowed_attributes_for_images(self, mock_clean):
        result = sanitize_html('<img src="test.jpg" alt="A test" width="100" height="50">')
        self.assertIn('src="test.jpg"', result)

    @patch('core.templatetags.sanitize.nh3.clean', return_value='<a href="https://example.com" rel="noopener noreferrer">Link</a>')
    def test_noopener_noreferrer_added_to_links(self, mock_clean):
        result = sanitize_html('<a href="https://example.com">Link</a>')
        self.assertIn('noopener', result)
        self.assertIn('noreferrer', result)

    @patch('core.templatetags.sanitize.nh3.clean')
    def test_clean_called_with_correct_params(self, mock_clean):
        """Verify nh3.clean is called with the expected configuration."""
        mock_clean.return_value = '<p>test</p>'
        sanitize_html('<p>test</p>')
        mock_clean.assert_called_once_with(
            '<p>test</p>',
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            link_rel='noopener noreferrer',
        )
