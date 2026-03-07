"""Tests for School_System/celery.py - Celery app configuration."""

from django.test import TestCase

from School_System.celery import app
from tests.helpers import TestDataMixin


class CeleryAppCreationTest(TestDataMixin, TestCase):
    """Tests for Celery app initialization."""

    def test_celery_app_name(self):
        """The Celery app is named 'School_System'."""
        self.assertEqual(app.main, 'School_System')

    def test_celery_app_is_celery_instance(self):
        """The app is an instance of Celery."""
        from celery import Celery
        self.assertIsInstance(app, Celery)

    def test_config_from_object_uses_django_settings(self):
        """Celery is configured from Django settings with CELERY namespace."""
        self.assertEqual(app.namespace, 'CELERY')


class CeleryBeatScheduleTest(TestDataMixin, TestCase):
    """Tests for Celery Beat schedule configuration."""

    def test_beat_schedule_is_not_empty(self):
        """beat_schedule contains scheduled tasks."""
        self.assertTrue(len(app.conf.beat_schedule) > 0)

    def test_cleanup_inactive_parents_task_exists(self):
        """cleanup-inactive-parents is in the beat schedule."""
        self.assertIn('cleanup-inactive-parents', app.conf.beat_schedule)

    def test_each_task_has_task_and_schedule_keys(self):
        """Every beat schedule entry has 'task' and 'schedule' keys."""
        for name, config in app.conf.beat_schedule.items():
            self.assertIn('task', config, f"'{name}' missing 'task' key")
            self.assertIn('schedule', config, f"'{name}' missing 'schedule' key")

    def test_task_names_are_dotted_paths(self):
        """All task names follow the 'app.tasks.function' convention."""
        for name, config in app.conf.beat_schedule.items():
            task_name = config['task']
            parts = task_name.split('.')
            self.assertGreaterEqual(
                len(parts), 2,
                f"Task '{task_name}' in '{name}' should be a dotted path",
            )

    def test_expected_task_count(self):
        """The beat schedule contains at least 1 scheduled task."""
        self.assertGreaterEqual(len(app.conf.beat_schedule), 1)

    def test_schedules_use_crontab(self):
        """All schedule entries use crontab schedules."""
        from celery.schedules import crontab
        for name, config in app.conf.beat_schedule.items():
            self.assertIsInstance(
                config['schedule'], crontab,
                f"'{name}' should use a crontab schedule",
            )
