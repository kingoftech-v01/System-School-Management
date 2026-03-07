"""Tests for core app models."""

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import School, Domain, Session, Semester, NewsAndEvents, ActivityLog
from tests.helpers import TestDataMixin


class SchoolModelTest(TestDataMixin, TestCase):
    def test_create_school(self):
        school = self.create_school()
        self.assertIsNotNone(school.pk)
        self.assertTrue(school.name.startswith('Test School'))

    def test_str(self):
        school = self.create_school(name='My School')
        self.assertEqual(str(school), 'My School')

    def test_is_subscription_valid_active(self):
        school = self.create_school(
            is_active=True,
            subscription_end=date.today() + timedelta(days=30),
        )
        self.assertTrue(school.is_subscription_valid())

    def test_is_subscription_valid_expired(self):
        school = self.create_school(
            is_active=True,
            subscription_end=date.today() - timedelta(days=1),
        )
        self.assertFalse(school.is_subscription_valid())

    def test_is_subscription_valid_inactive(self):
        school = self.create_school(
            is_active=False,
            subscription_end=date.today() + timedelta(days=30),
        )
        self.assertFalse(school.is_subscription_valid())

    def test_unique_name(self):
        self.create_school(name='Unique School', slug='unique-1', license_key='UK-1')
        with self.assertRaises(Exception):
            self.create_school(name='Unique School', slug='unique-2', license_key='UK-2')

    def test_unique_license_key(self):
        self.create_school(license_key='LK-001')
        with self.assertRaises(Exception):
            self.create_school(license_key='LK-001')

    def test_default_values(self):
        school = self.create_school()
        self.assertTrue(school.is_active)
        self.assertEqual(school.max_students, 500)
        self.assertEqual(school.max_staff, 50)
        self.assertEqual(school.subscription_type, 'monthly')
        self.assertEqual(school.primary_color, '#007bff')

    def test_ordering(self):
        self.create_school(name='Zebra School')
        self.create_school(name='Alpha School')
        schools = list(School.objects.values_list('name', flat=True))
        self.assertEqual(schools, sorted(schools))


class DomainModelTest(TestDataMixin, TestCase):
    def test_create_domain(self):
        school = self.create_school()
        domain = Domain.objects.create(
            domain='test.example.com',
            school=school,
            is_primary=True,
        )
        self.assertIsNotNone(domain.pk)

    def test_str(self):
        school = self.create_school()
        domain = Domain.objects.create(
            domain='my.domain.com',
            school=school,
        )
        self.assertEqual(str(domain), 'my.domain.com')

    def test_unique_domain(self):
        school = self.create_school()
        Domain.objects.create(domain='unique.com', school=school)
        with self.assertRaises(Exception):
            Domain.objects.create(domain='unique.com', school=school)


class SessionModelTest(TestDataMixin, TestCase):
    def test_create_session(self):
        session = self.create_session()
        self.assertIsNotNone(session.pk)

    def test_str(self):
        session = Session.objects.create(session='2024/2025')
        self.assertEqual(str(session), '2024/2025')

    def test_is_current_session(self):
        session = self.create_session(is_current_session=True)
        self.assertTrue(session.is_current_session)

    def test_unique_session(self):
        Session.objects.create(session='2024/2025')
        with self.assertRaises(Exception):
            Session.objects.create(session='2024/2025')


class SemesterModelTest(TestDataMixin, TestCase):
    def test_create_semester(self):
        semester = self.create_semester()
        self.assertIsNotNone(semester.pk)

    def test_str(self):
        session = self.create_session()
        semester = Semester.objects.create(semester='First', session=session)
        self.assertEqual(str(semester), 'First')

    def test_fk_to_session(self):
        session = self.create_session()
        semester = Semester.objects.create(semester='Second', session=session)
        self.assertEqual(semester.session, session)

    def test_is_current_semester(self):
        semester = self.create_semester(is_current_semester=True)
        self.assertTrue(semester.is_current_semester)


class NewsAndEventsModelTest(TestDataMixin, TestCase):
    def test_create_news(self):
        item = NewsAndEvents.objects.create(
            title='Test News', summary='A summary', posted_as='News'
        )
        self.assertIsNotNone(item.pk)

    def test_create_event(self):
        item = NewsAndEvents.objects.create(
            title='Test Event', summary='An event', posted_as='Event'
        )
        self.assertEqual(item.posted_as, 'Event')

    def test_str(self):
        item = NewsAndEvents.objects.create(
            title='Breaking News', posted_as='News'
        )
        self.assertEqual(str(item), 'Breaking News')

    def test_manager_search(self):
        NewsAndEvents.objects.create(title='Python Workshop', posted_as='Event')
        NewsAndEvents.objects.create(title='Math Seminar', posted_as='News')
        results = NewsAndEvents.objects.search('python')
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().title, 'Python Workshop')

    def test_manager_search_by_summary(self):
        NewsAndEvents.objects.create(
            title='Event 1', summary='Django conference', posted_as='Event'
        )
        results = NewsAndEvents.objects.search('django')
        self.assertEqual(results.count(), 1)

    def test_manager_get_by_id(self):
        item = NewsAndEvents.objects.create(title='Item', posted_as='News')
        found = NewsAndEvents.objects.get_by_id(item.pk)
        self.assertEqual(found, item)

    def test_manager_get_by_id_not_found(self):
        result = NewsAndEvents.objects.get_by_id(99999)
        self.assertIsNone(result)


class ActivityLogModelTest(TestDataMixin, TestCase):
    def test_create_log(self):
        log = ActivityLog.objects.create(message='Test action')
        self.assertIsNotNone(log.pk)

    def test_str(self):
        log = ActivityLog.objects.create(message='Something happened')
        self.assertIn('Something happened', str(log))

    def test_auto_created_at(self):
        log = ActivityLog.objects.create(message='Timestamped')
        self.assertIsNotNone(log.created_at)
