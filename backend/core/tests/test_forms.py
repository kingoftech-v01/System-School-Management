"""Tests for core app forms."""

from django.test import TestCase

from core.forms import SessionForm, SemesterForm, NewsAndEventsForm
from core.models import Session, Semester
from tests.helpers import TestDataMixin


class SessionFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = SessionForm(data={
            'session': '2025/2026',
            'is_current_session': True,
            'next_session_begins': '2025-09-01',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_empty_session(self):
        form = SessionForm(data={'session': '', 'next_session_begins': '2025-09-01'})
        self.assertFalse(form.is_valid())
        self.assertIn('session', form.errors)

    def test_invalid_no_date(self):
        form = SessionForm(data={'session': '2025/2026'})
        self.assertFalse(form.is_valid())
        self.assertIn('next_session_begins', form.errors)

    def test_save(self):
        form = SessionForm(data={
            'session': '2025/2026',
            'is_current_session': False,
            'next_session_begins': '2025-09-01',
        })
        self.assertTrue(form.is_valid(), form.errors)
        session = form.save()
        self.assertEqual(session.session, '2025/2026')

    def test_edit_existing(self):
        session = Session.objects.create(session='2024/2025-edit')
        form = SessionForm(data={
            'session': '2024/2025-updated',
            'is_current_session': True,
            'next_session_begins': '2025-09-01',
        }, instance=session)
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated.pk, session.pk)


class SemesterFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        session = self.create_session()
        form = SemesterForm(data={
            'semester': 'First',
            'is_current_semester': True,
            'session': session.pk,
            'next_semester_begins': '2025-01-15',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_empty(self):
        form = SemesterForm(data={})
        self.assertFalse(form.is_valid())

    def test_save(self):
        session = self.create_session()
        form = SemesterForm(data={
            'semester': 'Second',
            'is_current_semester': False,
            'session': session.pk,
            'next_semester_begins': '2025-06-01',
        })
        self.assertTrue(form.is_valid(), form.errors)
        semester = form.save()
        self.assertEqual(semester.semester, 'Second')

    def test_session_fk(self):
        session = self.create_session()
        form = SemesterForm(data={
            'semester': 'Third',
            'is_current_semester': False,
            'session': session.pk,
            'next_semester_begins': '2025-09-01',
        })
        self.assertTrue(form.is_valid(), form.errors)
        semester = form.save()
        self.assertEqual(semester.session, session)


class NewsAndEventsFormTest(TestDataMixin, TestCase):
    def test_valid_news(self):
        form = NewsAndEventsForm(data={
            'title': 'Test News',
            'summary': 'A news summary',
            'posted_as': 'News',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_event(self):
        form = NewsAndEventsForm(data={
            'title': 'Test Event',
            'summary': 'An event summary',
            'posted_as': 'Event',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_no_title(self):
        form = NewsAndEventsForm(data={
            'title': '',
            'posted_as': 'News',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_save(self):
        form = NewsAndEventsForm(data={
            'title': 'Saved News',
            'posted_as': 'News',
        })
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.title, 'Saved News')
