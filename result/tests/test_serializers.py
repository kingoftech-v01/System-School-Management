"""Tests for result app serializers."""

from decimal import Decimal
from django.test import TestCase

from result.models import TakenCourse, Result, GradeComponentWeight
from result.serializers import (
    TakenCourseSerializer,
    ResultSerializer,
    GradeComponentWeightSerializer,
)
from tests.helpers import TestDataMixin


class TakenCourseSerializerTest(TestDataMixin, TestCase):
    def test_serializes_taken_course(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        tc = TakenCourse.objects.create(
            student=student, course=course,
            assignment=Decimal('80'), mid_exam=Decimal('75'),
            quiz=Decimal('85'), attendance=Decimal('90'),
            final_exam=Decimal('70'),
        )
        serializer = TakenCourseSerializer(tc)
        data = serializer.data
        self.assertIn('total_score', data)
        self.assertIn('letter_grade', data)
        self.assertIn('pass_status', data)

    def test_includes_student_info(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        tc = TakenCourse.objects.create(
            student=student, course=course,
            assignment=Decimal('80'), mid_exam=Decimal('75'),
            quiz=Decimal('85'), attendance=Decimal('90'),
            final_exam=Decimal('70'),
        )
        serializer = TakenCourseSerializer(tc)
        data = serializer.data
        self.assertIn('student_name', data)


class ResultSerializerTest(TestDataMixin, TestCase):
    def test_serializes_result(self):
        user = self.create_student_user()
        student = self.create_student_profile(user)
        result = Result.objects.create(
            student=student,
            gpa=3.5,
            cgpa=3.4,
            semester='First',
            level='Bachelor',
        )
        serializer = ResultSerializer(result)
        data = serializer.data
        self.assertIn('gpa', data)
        self.assertIn('cgpa', data)


class GradeComponentWeightSerializerTest(TestDataMixin, TestCase):
    def test_serializes_weights(self):
        program = self.create_program()
        weight = GradeComponentWeight.objects.create(
            program=program,
            assignment_weight=Decimal('10'),
            mid_exam_weight=Decimal('20'),
            quiz_weight=Decimal('10'),
            attendance_weight=Decimal('10'),
            final_exam_weight=Decimal('50'),
        )
        serializer = GradeComponentWeightSerializer(weight)
        data = serializer.data
        self.assertIn('total_weight', data)

    def test_invalid_weights_sum(self):
        program = self.create_program()
        serializer = GradeComponentWeightSerializer(data={
            'program': program.pk,
            'assignment_weight': 10,
            'mid_exam_weight': 20,
            'quiz_weight': 10,
            'attendance_weight': 10,
            'final_exam_weight': 40,
        })
        self.assertFalse(serializer.is_valid())
