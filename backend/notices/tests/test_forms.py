"""Tests for notices app forms."""

from datetime import date, timedelta
from django.test import TestCase

from notices.forms import NoticeForm, NotifyGroupForm
from tests.helpers import TestDataMixin


class NoticeFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = NoticeForm(data={
            'title': 'Important Notice',
            'content': 'This is a notice.',
            'priority': 'normal',
            'is_active': True,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_title_too_short(self):
        form = NoticeForm(data={
            'title': 'Hi',
            'content': 'Content',
            'priority': 'normal',
        })
        self.assertFalse(form.is_valid())

    def test_expires_in_past(self):
        form = NoticeForm(data={
            'title': 'Past Notice',
            'content': 'This is content.',
            'priority': 'normal',
            'expires_at': (date.today() - timedelta(days=1)).isoformat(),
        })
        self.assertFalse(form.is_valid())

    def test_expires_in_future(self):
        form = NoticeForm(data={
            'title': 'Future Notice',
            'content': 'This is content.',
            'priority': 'normal',
            'expires_at': (date.today() + timedelta(days=7)).isoformat(),
            'is_active': True,
        })
        self.assertTrue(form.is_valid(), form.errors)


class NotifyGroupFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = NotifyGroupForm(data={
            'name': 'Test Group',
            'description': 'A test group',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        form = NotifyGroupForm(data={'description': 'No name'})
        self.assertFalse(form.is_valid())
