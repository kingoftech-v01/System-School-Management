"""Tests for core utility functions."""

from unittest.mock import patch, MagicMock

from django.test import TestCase

from core.utils import random_string_generator, unique_slug_generator
from tests.helpers import TestDataMixin


class RandomStringGeneratorTest(TestCase):
    def test_default_length(self):
        result = random_string_generator()
        self.assertEqual(len(result), 10)

    def test_custom_length(self):
        result = random_string_generator(size=20)
        self.assertEqual(len(result), 20)

    def test_only_lowercase_and_digits(self):
        result = random_string_generator(size=100)
        for char in result:
            self.assertTrue(char.isalnum() and (char.islower() or char.isdigit()))

    def test_uniqueness(self):
        results = {random_string_generator() for _ in range(50)}
        self.assertGreater(len(results), 40)


class UniqueSlugGeneratorTest(TestDataMixin, TestCase):
    def _make_instance(self, title='Hello World'):
        """Create a mock instance using Course (which has a slug field)."""
        from course.models import Course
        mock_instance = MagicMock()
        mock_instance.title = title
        mock_instance.__class__ = Course
        return mock_instance

    def test_basic_slug(self):
        slug = unique_slug_generator(self._make_instance('Hello World'))
        self.assertEqual(slug, 'hello-world')

    def test_slug_with_special_chars(self):
        slug = unique_slug_generator(self._make_instance('Test & Special (Chars)!'))
        self.assertNotIn('&', slug)
        self.assertNotIn('!', slug)

    def test_custom_new_slug(self):
        slug = unique_slug_generator(self._make_instance(), new_slug='custom-slug')
        self.assertEqual(slug, 'custom-slug')

    def test_duplicate_slug_gets_suffix(self):
        from course.models import Course
        program = self.create_program()
        Course.objects.create(
            title='Test Course', code='DUP001', credit=3,
            program=program, level='bachelor', year=1,
            semester='fall', slug='test-course',
        )
        slug = unique_slug_generator(self._make_instance('Test Course'))
        self.assertNotEqual(slug, 'test-course')
        self.assertTrue(slug.startswith('test-course-'))


class SendEmailTest(TestCase):
    @patch('core.utils.send_mail')
    def test_send_email(self, mock_send):
        from core.utils import send_email
        user = MagicMock()
        user.email = 'test@example.com'
        send_email(user, 'Subject', 'Message')
        mock_send.assert_called_once()

    @patch('core.utils.send_mail')
    @patch('core.utils.render_to_string', return_value='<p>Test</p>')
    def test_send_html_email(self, mock_render, mock_send):
        from core.utils import send_html_email
        send_html_email(
            'Subject',
            ['test@example.com'],
            'emails/test.html',
            {'key': 'value'},
        )
        mock_render.assert_called_once_with('emails/test.html', {'key': 'value'})
        mock_send.assert_called_once()
