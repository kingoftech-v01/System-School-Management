"""Tests for forums app forms."""

from django.test import TestCase

from forums.forms import ThreadForm, PostForm, ReportForm, SearchForm
from forums.models import ForumCategory
from tests.helpers import TestDataMixin


class ThreadFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        cat = ForumCategory.objects.create(name='General', is_active=True)
        form = ThreadForm(data={
            'category': cat.pk,
            'title': 'A valid title here',
            'content': 'Enough content for the validation to pass.',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_title_too_short(self):
        cat = ForumCategory.objects.create(name='Gen', is_active=True)
        form = ThreadForm(data={
            'category': cat.pk,
            'title': 'Hi',
            'content': 'Enough content for the validation to pass.',
        })
        self.assertFalse(form.is_valid())

    def test_content_too_short(self):
        cat = ForumCategory.objects.create(name='Gen2', is_active=True)
        form = ThreadForm(data={
            'category': cat.pk,
            'title': 'A valid title',
            'content': 'Short',
        })
        self.assertFalse(form.is_valid())

    def test_only_active_categories(self):
        ForumCategory.objects.create(name='Active', is_active=True)
        ForumCategory.objects.create(name='Inactive', is_active=False)
        form = ThreadForm()
        qs = form.fields['category'].queryset
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, 'Active')


class PostFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = PostForm(data={'content': 'This is a valid post content.'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_content_too_short(self):
        form = PostForm(data={'content': 'Short'})
        self.assertFalse(form.is_valid())


class ReportFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = ReportForm(data={
            'report_type': 'spam',
            'description': 'This post is definitely spam content.',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_description_too_short(self):
        form = ReportForm(data={
            'report_type': 'spam',
            'description': 'Bad',
        })
        self.assertFalse(form.is_valid())


class SearchFormTest(TestDataMixin, TestCase):
    def test_valid_search(self):
        form = SearchForm(data={'query': 'python'})
        self.assertTrue(form.is_valid(), form.errors)

    def test_query_too_short(self):
        form = SearchForm(data={'query': 'ab'})
        self.assertFalse(form.is_valid())
