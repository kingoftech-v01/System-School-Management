"""Tests for course app forms."""

from django.test import TestCase

from course.forms import (
    ProgramForm, CourseAddForm, CourseAllocationForm,
    EditCourseAllocationForm,
)
from course.models import Program, Course
from tests.helpers import TestDataMixin


class ProgramFormTest(TestDataMixin, TestCase):
    def test_valid(self):
        form = ProgramForm(data={'title': 'CS', 'summary': 'Computer Science'})
        self.assertTrue(form.is_valid())

    def test_invalid_no_title(self):
        form = ProgramForm(data={'title': '', 'summary': 'No title'})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_save(self):
        form = ProgramForm(data={'title': 'New Program', 'summary': 'Desc'})
        self.assertTrue(form.is_valid())
        program = form.save()
        self.assertEqual(program.title, 'New Program')


class CourseAddFormTest(TestDataMixin, TestCase):
    def test_valid(self):
        program = self.create_program()
        form = CourseAddForm(data={
            'title': 'Algorithms',
            'code': 'ALG101',
            'credit': 3,
            'summary': 'Algo course',
            'program': program.pk,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_no_code(self):
        program = self.create_program()
        form = CourseAddForm(data={
            'title': 'Algorithms',
            'code': '',
            'credit': 3,
            'program': program.pk,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        })
        self.assertFalse(form.is_valid())

    def test_invalid_no_title(self):
        form = CourseAddForm(data={'title': ''})
        self.assertFalse(form.is_valid())

    def test_save(self):
        program = self.create_program()
        form = CourseAddForm(data={
            'title': 'Data Structures',
            'code': 'DS101',
            'credit': 4,
            'program': program.pk,
            'level': 'bachelor',
            'year': 1,
            'semester': 'fall',
        })
        self.assertTrue(form.is_valid(), form.errors)
        course = form.save()
        self.assertEqual(course.title, 'Data Structures')


class CourseAllocationFormTest(TestDataMixin, TestCase):
    def test_valid(self):
        lecturer = self.create_professor_user()
        course = self.create_course()
        form = CourseAllocationForm(data={
            'lecturer': lecturer.pk,
            'courses': [course.pk],
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_no_lecturer(self):
        course = self.create_course()
        form = CourseAllocationForm(data={
            'courses': [course.pk],
        })
        self.assertFalse(form.is_valid())

    def test_multiple_courses(self):
        lecturer = self.create_professor_user()
        course1 = self.create_course()
        course2 = self.create_course()
        form = CourseAllocationForm(data={
            'lecturer': lecturer.pk,
            'courses': [course1.pk, course2.pk],
        })
        self.assertTrue(form.is_valid(), form.errors)


class EditCourseAllocationFormTest(TestDataMixin, TestCase):
    def test_valid(self):
        lecturer = self.create_professor_user()
        course = self.create_course()
        form = EditCourseAllocationForm(data={
            'lecturer': lecturer.pk,
            'courses': [course.pk],
        })
        self.assertTrue(form.is_valid(), form.errors)
