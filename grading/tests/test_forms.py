"""Tests for grading app forms."""

from decimal import Decimal
from django.test import TestCase

from grading.forms import (
    GradingRubricForm, RubricCriterionForm, PeerReviewForm, GradeCurveForm,
)
from grading.models import GradingRubric
from tests.helpers import TestDataMixin


class GradingRubricFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        course = self.create_course()
        form = GradingRubricForm(data={
            'name': 'Essay Rubric',
            'course': course.pk,
            'max_score': '100.00',
            'passing_score': '60.00',
            'is_active': True,
            'allow_partial_credit': True,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_passing_exceeds_max(self):
        course = self.create_course()
        form = GradingRubricForm(data={
            'name': 'Bad Rubric',
            'course': course.pk,
            'max_score': '50.00',
            'passing_score': '70.00',
            'is_active': True,
        })
        self.assertFalse(form.is_valid())


class RubricCriterionFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = RubricCriterionForm(data={
            'name': 'Content Quality',
            'weight': '50.00',
            'max_points': '10.00',
            'order': 1,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_weight_out_of_range(self):
        form = RubricCriterionForm(data={
            'name': 'Bad',
            'weight': '150.00',
            'max_points': '10.00',
        })
        self.assertFalse(form.is_valid())

    def test_negative_weight(self):
        form = RubricCriterionForm(data={
            'name': 'Bad',
            'weight': '-5.00',
            'max_points': '10.00',
        })
        self.assertFalse(form.is_valid())


class PeerReviewFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = PeerReviewForm(data={
            'score': '85.00',
            'feedback': 'Good work!',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_score_out_of_range(self):
        form = PeerReviewForm(data={
            'score': '150.00',
            'feedback': 'Over 100',
        })
        self.assertFalse(form.is_valid())

    def test_negative_score(self):
        form = PeerReviewForm(data={
            'score': '-10.00',
            'feedback': 'Negative',
        })
        self.assertFalse(form.is_valid())


class GradeCurveFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        course = self.create_course()
        form = GradeCurveForm(data={
            'course': course.pk,
            'assignment_name': 'Midterm',
            'curve_type': 'linear',
            'adjustment_factor': '1.10',
            'add_points': '5.00',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_zero_adjustment_factor(self):
        course = self.create_course()
        form = GradeCurveForm(data={
            'course': course.pk,
            'assignment_name': 'Final',
            'curve_type': 'sqrt',
            'adjustment_factor': '0.00',
            'add_points': '0.00',
        })
        self.assertFalse(form.is_valid())
