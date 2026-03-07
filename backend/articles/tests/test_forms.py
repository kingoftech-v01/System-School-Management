"""Tests for articles app forms."""

from django.test import TestCase

from tests.helpers import TestDataMixin
from articles.forms import ArticleForm, CommentForm, NewsletterForm


class ArticleFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'title': 'Test Article',
            'summary': 'A brief summary',
            'content': 'Full article content here.',
            'status': 'draft',
        }
        form = ArticleForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = ArticleForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('content', form.errors)

    def test_meta_fields(self):
        form = ArticleForm()
        self.assertIn('title', form.fields)
        self.assertIn('summary', form.fields)
        self.assertIn('content', form.fields)
        self.assertIn('status', form.fields)


class CommentFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {'content': 'This is a great article!'}
        form = CommentForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_content_invalid(self):
        form = CommentForm(data={'content': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


class NewsletterFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {'email': 'subscriber@test.com', 'frequency': 'weekly'}
        form = NewsletterForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email(self):
        data = {'email': 'bad-email', 'frequency': 'weekly'}
        form = NewsletterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_frequency(self):
        data = {'email': 'test@test.com', 'frequency': 'hourly'}
        form = NewsletterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('frequency', form.errors)

    def test_default_frequency(self):
        form = NewsletterForm()
        self.assertEqual(form.fields['frequency'].initial, 'weekly')
