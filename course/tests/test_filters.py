"""
Tests for course app filters.
"""

from django.test import TestCase

from course.filters import CourseAllocationFilter, ProgramFilter
from course.models import CourseAllocation, Program
from tests.helpers import TestDataMixin


class TestProgramFilter(TestDataMixin, TestCase):
    """Tests for ProgramFilter."""

    def setUp(self):
        self.program1 = self.create_program(title='Computer Science')
        self.program2 = self.create_program(title='Mathematics')
        self.program3 = self.create_program(title='Computer Engineering')

    def test_filter_by_title_exact_match(self):
        """Filter should return programs matching the title."""
        qs = Program.objects.all()
        f = ProgramFilter(data={'title': 'Mathematics'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.program2)

    def test_filter_by_title_partial_match(self):
        """Filter should support case-insensitive partial matching."""
        qs = Program.objects.all()
        f = ProgramFilter(data={'title': 'computer'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 2)
        titles = list(result.values_list('title', flat=True))
        self.assertIn('Computer Science', titles)
        self.assertIn('Computer Engineering', titles)

    def test_filter_no_match(self):
        """Filter should return empty queryset when no match."""
        qs = Program.objects.all()
        f = ProgramFilter(data={'title': 'Physics'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 0)

    def test_filter_empty_title(self):
        """Filter should return all programs when title is empty."""
        qs = Program.objects.all()
        f = ProgramFilter(data={'title': ''}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 3)


class TestCourseAllocationFilter(TestDataMixin, TestCase):
    """Tests for CourseAllocationFilter."""

    def setUp(self):
        self.session = self.create_session()
        self.professor1 = self.create_professor_user(
            first_name='Alice', last_name='Smith'
        )
        self.professor2 = self.create_professor_user(
            first_name='Bob', last_name='Jones'
        )
        self.course1 = self.create_course(title='Data Structures')
        self.course2 = self.create_course(title='Algorithms')

        self.alloc1 = CourseAllocation.objects.create(
            lecturer=self.professor1, session=self.session
        )
        self.alloc1.courses.add(self.course1)

        self.alloc2 = CourseAllocation.objects.create(
            lecturer=self.professor2, session=self.session
        )
        self.alloc2.courses.add(self.course2)

    def test_filter_by_lecturer_first_name(self):
        """Filter should match lecturer by first name."""
        qs = CourseAllocation.objects.all()
        f = CourseAllocationFilter(data={'lecturer': 'Alice'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.alloc1)

    def test_filter_by_lecturer_last_name(self):
        """Filter should match lecturer by last name."""
        qs = CourseAllocation.objects.all()
        f = CourseAllocationFilter(data={'lecturer': 'Jones'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.alloc2)

    def test_filter_by_course_title(self):
        """Filter should match by course title."""
        qs = CourseAllocation.objects.all()
        f = CourseAllocationFilter(data={'course': 'Data'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.alloc1)

    def test_filter_no_match(self):
        """Filter should return empty queryset when nothing matches."""
        qs = CourseAllocation.objects.all()
        f = CourseAllocationFilter(data={'lecturer': 'Nobody'}, queryset=qs)
        result = f.qs
        self.assertEqual(result.count(), 0)
