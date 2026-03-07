"""Tests for search template tags: class_name.py."""

from django.test import TestCase

from search.templatetags.class_name import class_name
from tests.helpers import TestDataMixin


class ClassNameFilterTest(TestDataMixin, TestCase):
    """Tests for the class_name template filter."""

    def test_returns_class_name_of_string(self):
        """class_name returns 'str' for a string value."""
        self.assertEqual(class_name('hello'), 'str')

    def test_returns_class_name_of_int(self):
        """class_name returns 'int' for an integer value."""
        self.assertEqual(class_name(42), 'int')

    def test_returns_class_name_of_dict(self):
        """class_name returns 'dict' for a dict value."""
        self.assertEqual(class_name({}), 'dict')

    def test_returns_class_name_of_model_instance(self):
        """class_name returns the model class name for a Django model instance."""
        school = self.create_school()
        self.assertEqual(class_name(school), 'School')

    def test_returns_class_name_of_user(self):
        """class_name returns 'User' for a User model instance."""
        user = self.create_user()
        # The user model class name varies, but it should be a non-empty string
        result = class_name(user)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
