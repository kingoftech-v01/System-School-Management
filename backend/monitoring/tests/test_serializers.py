"""Tests for monitoring app serializers."""

from django.test import TestCase

from monitoring.serializers import (
    UserStatsSerializer,
    GenderDistributionSerializer,
    EnrollmentStatsSerializer,
    LibraryStatsSerializer,
    DisciplineStatsSerializer,
    DashboardStatsSerializer,
    BooksByCategorySerializer,
    BorrowStatusSerializer,
    DetailedLibraryStatsSerializer,
)


class UserStatsSerializerTest(TestCase):
    def test_valid(self):
        data = {'students': 100, 'professors': 20, 'parents': 50}
        serializer = UserStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_field(self):
        data = {'students': 100, 'professors': 20}
        serializer = UserStatsSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class GenderDistributionSerializerTest(TestCase):
    def test_valid(self):
        data = {'gender': 'Male', 'count': 55}
        serializer = GenderDistributionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class EnrollmentStatsSerializerTest(TestCase):
    def test_valid_with_level(self):
        data = {'status': 'enrolled', 'level': 'bachelor', 'count': 30}
        serializer = EnrollmentStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_without_level(self):
        data = {'status': 'enrolled', 'count': 30}
        serializer = EnrollmentStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class LibraryStatsSerializerTest(TestCase):
    def test_valid(self):
        data = {'total_books': 500, 'borrowed': 50, 'overdue': 5}
        serializer = LibraryStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class DisciplineStatsSerializerTest(TestCase):
    def test_valid(self):
        data = {'total': 10, 'unresolved': 3}
        serializer = DisciplineStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class DashboardStatsSerializerTest(TestCase):
    def test_valid_full(self):
        data = {
            'users': {'students': 100, 'professors': 20, 'parents': 50},
            'gender_distribution': [
                {'gender': 'Male', 'count': 55},
                {'gender': 'Female', 'count': 45},
            ],
            'enrollment': [
                {'status': 'enrolled', 'count': 80},
            ],
            'library': {'total_books': 500, 'borrowed': 50, 'overdue': 5},
            'discipline': {'total': 10, 'unresolved': 3},
        }
        serializer = DashboardStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_without_optional(self):
        data = {
            'users': {'students': 100, 'professors': 20, 'parents': 50},
            'gender_distribution': [],
            'enrollment': [],
            'library': None,
            'discipline': None,
        }
        serializer = DashboardStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class BooksByCategorySerializerTest(TestCase):
    def test_valid(self):
        data = {'category': 'Science', 'count': 42}
        serializer = BooksByCategorySerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class BorrowStatusSerializerTest(TestCase):
    def test_valid(self):
        data = {'status': 'returned', 'count': 15}
        serializer = BorrowStatusSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class DetailedLibraryStatsSerializerTest(TestCase):
    def test_valid(self):
        data = {
            'books_by_category': [
                {'category': 'Science', 'count': 42},
                {'category': 'History', 'count': 30},
            ],
            'borrow_status': [
                {'status': 'borrowed', 'count': 20},
                {'status': 'returned', 'count': 15},
            ],
        }
        serializer = DetailedLibraryStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_lists(self):
        data = {
            'books_by_category': [],
            'borrow_status': [],
        }
        serializer = DetailedLibraryStatsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
