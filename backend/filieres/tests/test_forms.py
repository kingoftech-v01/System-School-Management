"""Tests for filieres app forms."""

from django.test import TestCase

from filieres.forms import FiliereForm, FiliereSubjectForm, FiliereRequirementForm, FiliereSearchForm
from tests.helpers import TestDataMixin


class FiliereFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = FiliereForm(data={
            'name': 'Computer Science',
            'code': 'cs',
            'level': 'Bachelor',
            'duration_years': 3,
            'is_active': True,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_code_uppercased(self):
        form = FiliereForm(data={
            'name': 'Computer Science',
            'code': 'cs',
            'level': 'Bachelor',
            'duration_years': 3,
        })
        form.is_valid()
        self.assertEqual(form.cleaned_data['code'], 'CS')

    def test_missing_name(self):
        form = FiliereForm(data={
            'code': 'CS',
            'level': 'Bachelor',
            'duration_years': 3,
        })
        self.assertFalse(form.is_valid())

    def test_missing_code(self):
        form = FiliereForm(data={
            'name': 'Computer Science',
            'level': 'Bachelor',
            'duration_years': 3,
        })
        self.assertFalse(form.is_valid())


class FiliereSubjectFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        course = self.create_course()
        form = FiliereSubjectForm(data={
            'subject': course.pk,
            'coefficient': '2.0',
            'is_mandatory': True,
            'year': 1,
            'semester': 1,
            'credits': 3,
            'hours_per_week': 4,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_subject(self):
        form = FiliereSubjectForm(data={
            'coefficient': '2.0',
            'year': 1,
            'semester': 1,
        })
        self.assertFalse(form.is_valid())


class FiliereRequirementFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = FiliereRequirementForm(data={
            'requirement_type': 'academic',
            'description': 'Must have GPA 3.0',
            'is_mandatory': True,
            'order': 1,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_description(self):
        form = FiliereRequirementForm(data={
            'requirement_type': 'academic',
        })
        self.assertFalse(form.is_valid())


class FiliereSearchFormTest(TestCase):
    def test_empty_search_valid(self):
        form = FiliereSearchForm(data={})
        self.assertTrue(form.is_valid())

    def test_search_with_keyword(self):
        form = FiliereSearchForm(data={'search': 'Computer'})
        self.assertTrue(form.is_valid())

    def test_search_with_level(self):
        form = FiliereSearchForm(data={'level': 'Bachelor'})
        self.assertTrue(form.is_valid())
