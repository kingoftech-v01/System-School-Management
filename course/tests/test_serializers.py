"""Tests for course app serializers."""

from django.test import TestCase

from course.models import Program, Course, CourseAllocation
from course.serializers import (
    ProgramSerializer, CourseSerializer, CourseAllocationSerializer,
)
from tests.helpers import TestDataMixin


class ProgramSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        program = self.create_program()
        data = ProgramSerializer(program).data
        self.assertEqual(data['title'], program.title)
        self.assertIn('id', data)

    def test_deserialization_valid(self):
        serializer = ProgramSerializer(data={
            'title': 'New Program',
            'summary': 'A summary',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_deserialization_invalid(self):
        serializer = ProgramSerializer(data={'title': ''})
        self.assertFalse(serializer.is_valid())


class CourseSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        course = self.create_course()
        data = CourseSerializer(course).data
        self.assertEqual(data['title'], course.title)
        self.assertEqual(data['code'], course.code)

    def test_deserialization_valid(self):
        program = self.create_program()
        serializer = CourseSerializer(data={
            'title': 'New Course',
            'code': 'NC001',
            'credit': 3,
            'program': program.pk,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)


class CourseAllocationSerializerTest(TestDataMixin, TestCase):
    def test_serialization(self):
        lecturer = self.create_professor_user()
        alloc = CourseAllocation.objects.create(lecturer=lecturer)
        course = self.create_course()
        alloc.courses.add(course)
        data = CourseAllocationSerializer(alloc).data
        self.assertIn('lecturer', data)
        self.assertIn('courses', data)
