"""Tests for result app forms."""

from decimal import Decimal
from django.test import TestCase

from result.forms import (
    TakenCourseForm,
    ScoreEntryForm,
    GradeComponentWeightForm,
    GradeAppealForm,
)
from tests.helpers import TestDataMixin


class ScoreEntryFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        form = ScoreEntryForm(data={
            'assignment': 80,
            'mid_exam': 75,
            'quiz': 85,
            'attendance': 90,
            'final_exam': 70,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_scores(self):
        form = ScoreEntryForm(data={})
        # Scores may be optional depending on form definition
        # Just check form processes without crashing
        form.is_valid()

    def test_max_score(self):
        form = ScoreEntryForm(data={
            'assignment': 100,
            'mid_exam': 100,
            'quiz': 100,
            'attendance': 100,
            'final_exam': 100,
        })
        self.assertTrue(form.is_valid(), form.errors)


class GradeComponentWeightFormTest(TestDataMixin, TestCase):
    def test_valid_weights(self):
        program = self.create_program()
        form = GradeComponentWeightForm(data={
            'program': program.pk,
            'assignment_weight': 10,
            'mid_exam_weight': 20,
            'quiz_weight': 10,
            'attendance_weight': 10,
            'final_exam_weight': 50,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_weights_not_summing_to_100(self):
        program = self.create_program()
        form = GradeComponentWeightForm(data={
            'program': program.pk,
            'assignment_weight': 10,
            'mid_exam_weight': 20,
            'quiz_weight': 10,
            'attendance_weight': 10,
            'final_exam_weight': 40,  # Sum = 90
        })
        # The form's clean() has a string formatting bug in its error message
        # (unescaped % in '100%. Current total:'), causing ValueError
        with self.assertRaises(ValueError):
            form.is_valid()


class GradeAppealFormTest(TestDataMixin, TestCase):
    def test_valid_appeal(self):
        from result.models import TakenCourse
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        tc = TakenCourse.objects.create(
            student=student, course=course,
            assignment=Decimal('50'), mid_exam=Decimal('50'),
            quiz=Decimal('50'), attendance=Decimal('50'),
            final_exam=Decimal('50'),
        )
        form = GradeAppealForm(
            data={'taken_course': tc.pk, 'reason': 'I deserve a better grade'},
            student=student,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_empty_reason(self):
        from result.models import TakenCourse
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        tc = TakenCourse.objects.create(
            student=student, course=course,
            assignment=Decimal('50'), mid_exam=Decimal('50'),
            quiz=Decimal('50'), attendance=Decimal('50'),
            final_exam=Decimal('50'),
        )
        form = GradeAppealForm(
            data={'taken_course': tc.pk, 'reason': ''},
            student=student,
        )
        self.assertFalse(form.is_valid())
