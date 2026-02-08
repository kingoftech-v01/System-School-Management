"""Extended core model tests for uncovered branches."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import (
    School, Domain, NewsAndEvents, Session, Semester, ActivityLog,
)
from tests.helpers import TestDataMixin


class SchoolModelTest(TestDataMixin, TestCase):
    def test_str(self):
        school = self.create_school()
        self.assertEqual(str(school), school.name)

    def test_subscription_valid(self):
        school = self.create_school()
        self.assertTrue(school.is_subscription_valid())

    def test_subscription_expired(self):
        school = self.create_school()
        school.subscription_end = timezone.now().date() - timedelta(days=1)
        school.save()
        self.assertFalse(school.is_subscription_valid())

    def test_subscription_inactive(self):
        school = self.create_school()
        school.is_active = False
        school.save()
        self.assertFalse(school.is_subscription_valid())


class DomainModelTest(TestDataMixin, TestCase):
    def test_str(self):
        school = self.create_school()
        domain = Domain.objects.create(
            domain='test.school.com',
            school=school,
            is_primary=True,
        )
        self.assertEqual(str(domain), 'test.school.com')

    def test_multiple_domains(self):
        school = self.create_school()
        d1 = Domain.objects.create(domain='main.school.com', school=school, is_primary=True)
        d2 = Domain.objects.create(domain='alt.school.com', school=school, is_primary=False)
        self.assertEqual(school.domains.count(), 2)


class NewsAndEventsModelTest(TestCase):
    def test_str(self):
        news = NewsAndEvents.objects.create(title='Spring Gala', posted_as='Event')
        self.assertEqual(str(news), 'Spring Gala')

    def test_search(self):
        NewsAndEvents.objects.create(title='Math Competition', posted_as='News')
        qs = NewsAndEvents.objects.search('Math')
        self.assertEqual(qs.count(), 1)

    def test_search_by_summary(self):
        NewsAndEvents.objects.create(
            title='Event', summary='Annual science fair', posted_as='Event'
        )
        qs = NewsAndEvents.objects.search('science')
        self.assertEqual(qs.count(), 1)

    def test_search_by_posted_as(self):
        NewsAndEvents.objects.create(title='Title', posted_as='News')
        qs = NewsAndEvents.objects.search('News')
        self.assertEqual(qs.count(), 1)

    def test_search_no_results(self):
        NewsAndEvents.objects.create(title='Something', posted_as='News')
        qs = NewsAndEvents.objects.search('ZZZZZ')
        self.assertEqual(qs.count(), 0)

    def test_get_by_id(self):
        news = NewsAndEvents.objects.create(title='Test', posted_as='News')
        result = NewsAndEvents.objects.get_by_id(news.id)
        self.assertEqual(result, news)

    def test_get_by_id_not_found(self):
        result = NewsAndEvents.objects.get_by_id(99999)
        self.assertIsNone(result)

    def test_all(self):
        NewsAndEvents.objects.create(title='One', posted_as='News')
        NewsAndEvents.objects.create(title='Two', posted_as='Event')
        self.assertEqual(NewsAndEvents.objects.all().count(), 2)


class SessionModelTest(TestCase):
    def test_str(self):
        session = Session.objects.create(session='2024/2025')
        self.assertEqual(str(session), '2024/2025')

    def test_is_current_session(self):
        session = Session.objects.create(session='2024/2025', is_current_session=True)
        self.assertTrue(session.is_current_session)


class SemesterModelTest(TestCase):
    def test_str(self):
        session = Session.objects.create(session='2024/2025')
        semester = Semester.objects.create(semester='First', session=session)
        self.assertEqual(str(semester), 'First')

    def test_is_current_semester(self):
        session = Session.objects.create(session='2024/2025')
        semester = Semester.objects.create(
            semester='First', session=session, is_current_semester=True
        )
        self.assertTrue(semester.is_current_semester)


class ActivityLogTest(TestCase):
    def test_str(self):
        log = ActivityLog.objects.create(message='User logged in')
        self.assertIn('User logged in', str(log))

    def test_created_at_set(self):
        log = ActivityLog.objects.create(message='Test')
        self.assertIsNotNone(log.created_at)
