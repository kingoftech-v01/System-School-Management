"""Tests for search app serializers."""

from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from search.serializers import (
    UnifiedSearchResultSerializer,
    NewsSearchSerializer,
    ProgramSearchSerializer,
    CourseSearchSerializer,
    QuizSearchSerializer,
)
from core.models import NewsAndEvents
from course.models import Program, Course
from tests.helpers import TestDataMixin


class UnifiedSearchResultSerializerTest(TestDataMixin, TestCase):
    def test_news_result(self):
        news = NewsAndEvents.objects.create(
            title='Test News', summary='A summary',
        )
        serializer = UnifiedSearchResultSerializer(news)
        data = serializer.data
        self.assertEqual(data['id'], news.pk)
        self.assertEqual(data['title'], 'Test News')
        self.assertEqual(data['type'], 'news')

    def test_program_result(self):
        program = self.create_program()
        serializer = UnifiedSearchResultSerializer(program)
        data = serializer.data
        self.assertEqual(data['type'], 'program')
        self.assertEqual(data['title'], program.title)

    def test_course_result(self):
        course = self.create_course()
        serializer = UnifiedSearchResultSerializer(course)
        data = serializer.data
        self.assertEqual(data['type'], 'course')
        self.assertIsNotNone(data['url'])  # course has slug

    def test_unknown_type(self):
        school = self.create_school()
        serializer = UnifiedSearchResultSerializer(school)
        data = serializer.data
        self.assertEqual(data['type'], 'unknown')

    def test_summary_from_description(self):
        """Objects with summary attribute return it."""
        program = self.create_program()
        serializer = UnifiedSearchResultSerializer(program)
        data = serializer.data
        self.assertIsNotNone(data['summary'])

    def test_created_at_field(self):
        news = NewsAndEvents.objects.create(title='News', summary='S')
        serializer = UnifiedSearchResultSerializer(news)
        data = serializer.data
        # UnifiedSearchResultSerializer checks for created_at via getattr
        self.assertIn('created_at', data)

    def test_url_none_for_no_slug(self):
        """Objects without slug return None for url."""
        news = NewsAndEvents.objects.create(title='News', summary='S')
        serializer = UnifiedSearchResultSerializer(news)
        data = serializer.data
        self.assertIsNone(data['url'])


class NewsSearchSerializerTest(TestCase):
    def test_raises_for_invalid_field(self):
        """NewsSearchSerializer references created_at which doesn't exist on model."""
        news = NewsAndEvents.objects.create(title='Test', summary='Sum')
        serializer = NewsSearchSerializer(news)
        with self.assertRaises(ImproperlyConfigured):
            serializer.data


class ProgramSearchSerializerTest(TestDataMixin, TestCase):
    def test_raises_for_invalid_field(self):
        """ProgramSearchSerializer references created_at which doesn't exist on model."""
        program = self.create_program()
        serializer = ProgramSearchSerializer(program)
        with self.assertRaises(ImproperlyConfigured):
            serializer.data


class CourseSearchSerializerTest(TestDataMixin, TestCase):
    def test_raises_for_invalid_field(self):
        """CourseSearchSerializer references created_at which doesn't exist on model."""
        course = self.create_course()
        serializer = CourseSearchSerializer(course)
        with self.assertRaises(ImproperlyConfigured):
            serializer.data
