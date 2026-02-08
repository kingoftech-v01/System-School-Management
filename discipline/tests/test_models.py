"""Tests for discipline app models."""

from datetime import date, timedelta
from django.test import TestCase

from discipline.models import DisciplinaryAction
from tests.helpers import TestDataMixin


class DisciplinaryActionTest(TestDataMixin, TestCase):
    def _create_action(self, **kwargs):
        tenant = kwargs.pop('tenant', None) or self.create_school()
        student = kwargs.pop('student', None) or self.create_user(role='student')
        reporter = kwargs.pop('reported_by', None) or self.create_user(role='direction')
        defaults = {
            'tenant': tenant,
            'student': student,
            'reported_by': reporter,
            'incident_type': 'Cheating',
            'description': 'Caught cheating on exam',
            'action_taken': 'Written warning issued',
            'severity': 'moderate',
            'incident_date': date.today(),
        }
        defaults.update(kwargs)
        return DisciplinaryAction.objects.create(**defaults)

    def test_create_and_str(self):
        action = self._create_action()
        self.assertIn('Cheating', str(action))
        self.assertIn('moderate', str(action))

    def test_defaults(self):
        action = self._create_action()
        self.assertFalse(action.is_resolved)
        self.assertIsNone(action.resolution_date)

    def test_severity_choices(self):
        for sev in ['minor', 'moderate', 'serious', 'critical']:
            action = self._create_action(severity=sev)
            self.assertEqual(action.severity, sev)

    def test_resolved_with_date(self):
        action = self._create_action(
            is_resolved=True,
            resolution_date=date.today(),
        )
        self.assertTrue(action.is_resolved)
        self.assertIsNotNone(action.resolution_date)

    def test_updated_by(self):
        updater = self.create_user(role='direction')
        action = self._create_action(updated_by=updater)
        self.assertEqual(action.updated_by, updater)
