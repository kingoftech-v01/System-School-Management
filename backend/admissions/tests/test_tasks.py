"""Tests for admissions app Celery tasks."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from admissions.models import AdmissionSession, AdmissionStudent
from admissions.tasks import auto_archive_old_applications
from tests.helpers import TestDataMixin


class AutoArchiveOldApplicationsTest(TestDataMixin, TestCase):
    def test_counts_old_applications(self):
        session = AdmissionSession.objects.create(
            name='2023 Session',
            start_date=timezone.now().date() - timedelta(days=365),
            end_date=timezone.now().date() - timedelta(days=30),
            is_active=False,
        )
        AdmissionStudent.objects.create(
            session=session,
            first_name='John',
            last_name='Doe',
            email='john@test.com',
            phone='1234567890',
            date_of_birth='2000-01-01',
            status='pending',
        )
        result = auto_archive_old_applications()
        self.assertIn('1', result)

    def test_active_session_excluded(self):
        session = AdmissionSession.objects.create(
            name='Current Session',
            start_date=timezone.now().date() - timedelta(days=30),
            end_date=timezone.now().date() + timedelta(days=30),
            is_active=True,
        )
        AdmissionStudent.objects.create(
            session=session,
            first_name='Jane',
            last_name='Doe',
            email='jane@test.com',
            phone='1234567890',
            date_of_birth='2000-01-01',
            status='pending',
        )
        result = auto_archive_old_applications()
        self.assertIn('0', result)
