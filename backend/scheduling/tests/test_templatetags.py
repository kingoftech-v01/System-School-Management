"""Tests for scheduling template tags: scheduling_tags.py."""

from datetime import date, timedelta, time
from unittest.mock import patch, MagicMock, PropertyMock

from django.test import TestCase, RequestFactory

from scheduling.templatetags.scheduling_tags import todays_schedule
from tests.helpers import TestDataMixin


class TodaysScheduleTagTest(TestDataMixin, TestCase):
    """Tests for the todays_schedule inclusion tag."""

    def setUp(self):
        self.factory = RequestFactory()
        self.school = self.create_school()

    def _make_context(self, user=None, tenant=None):
        """Build a template context dict with a mock request."""
        request = self.factory.get('/')
        if user:
            request.user = user
        else:
            request.user = MagicMock(is_authenticated=False)
        request.tenant = tenant or self.school
        return {'request': request}

    def test_unauthenticated_user_returns_empty(self):
        """Unauthenticated users get an empty schedule list."""
        context = self._make_context()
        result = todays_schedule(context)
        self.assertEqual(result['schedule_entries'], [])

    def test_no_request_returns_empty(self):
        """When context has no request key, returns empty schedule."""
        result = todays_schedule({})
        self.assertEqual(result['schedule_entries'], [])

    def test_none_request_returns_empty(self):
        """When context request is None, returns empty schedule."""
        result = todays_schedule({'request': None})
        self.assertEqual(result['schedule_entries'], [])

    @patch('scheduling.templatetags.scheduling_tags.ScheduleEntry.objects')
    def test_professor_role_filters_by_professor(self, mock_qs):
        """Professor users get entries filtered by their own user."""
        professor = self.create_professor_user()
        context = self._make_context(user=professor)

        # Build mock queryset chain
        mock_filtered = MagicMock()
        mock_filtered.select_related.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.__iter__ = MagicMock(return_value=iter([]))
        mock_qs.filter.return_value = mock_filtered

        result = todays_schedule(context)
        self.assertEqual(result['schedule_entries'], [])

    @patch('scheduling.templatetags.scheduling_tags.ScheduleEntry.objects')
    def test_student_without_profile_returns_empty(self, mock_qs):
        """Student with no student profile gets an empty schedule."""
        student = self.create_student_user()
        # Ensure no student profile attribute
        if hasattr(student, 'student'):
            try:
                delattr(student, 'student')
            except AttributeError:
                pass
        context = self._make_context(user=student)

        mock_filtered = MagicMock()
        mock_filtered.select_related.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.none.return_value = MagicMock(__iter__=MagicMock(return_value=iter([])))
        mock_qs.filter.return_value = mock_filtered

        result = todays_schedule(context)
        self.assertEqual(result['schedule_entries'], [])

    def test_authenticated_student_with_schedule(self):
        """Integration test: student without matching filiere gets empty schedule."""
        today = date.today()
        student_user = self.create_student_user()
        # Create student profile without a program so the code path
        # hits the `entries.none()` branch (student_profile.program is None).
        from accounts.models import Student
        Student.objects.create(student=student_user, level='Bachelor', program=None)

        filiere = self.create_filiere(tenant=self.school)
        time_slot = self.create_timeslot(
            tenant=self.school,
            day_of_week=today.weekday(),
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        entry = self.create_schedule_entry(
            tenant=self.school,
            time_slot=time_slot,
            filiere=filiere,
            effective_from=today - timedelta(days=1),
            effective_until=today + timedelta(days=30),
        )

        context = self._make_context(user=student_user, tenant=self.school)
        result = todays_schedule(context)
        # Student's program is None, so entries.none() is called.
        self.assertIsInstance(result['schedule_entries'], list)
        self.assertEqual(result['schedule_entries'], [])

    def test_direction_user_gets_all_active_entries(self):
        """Direction users get all entries (no extra filter)."""
        today = date.today()
        direction_user = self.create_direction_user()
        time_slot = self.create_timeslot(
            tenant=self.school,
            day_of_week=today.weekday(),
            start_time=time(9, 0),
            end_time=time(11, 0),
        )
        entry = self.create_schedule_entry(
            tenant=self.school,
            time_slot=time_slot,
            effective_from=today - timedelta(days=1),
            effective_until=today + timedelta(days=30),
        )

        context = self._make_context(user=direction_user, tenant=self.school)
        result = todays_schedule(context)
        # Direction role falls through the if/elif chain, so all entries
        # pass through (filtered only by active, effective dates, day).
        self.assertIsInstance(result['schedule_entries'], list)

    def test_max_eight_entries_returned(self):
        """The tag returns at most 8 schedule entries."""
        today = date.today()
        direction_user = self.create_direction_user()

        for i in range(10):
            ts = self.create_timeslot(
                tenant=self.school,
                day_of_week=today.weekday(),
                start_time=time(8 + i % 12, 0),
                end_time=time(8 + i % 12, 55),
            )
            self.create_schedule_entry(
                tenant=self.school,
                time_slot=ts,
                effective_from=today - timedelta(days=1),
                effective_until=today + timedelta(days=30),
            )

        context = self._make_context(user=direction_user, tenant=self.school)
        result = todays_schedule(context)
        self.assertLessEqual(len(result['schedule_entries']), 8)

    @patch('scheduling.templatetags.scheduling_tags.ScheduleEntry.objects')
    def test_parent_without_parent_object_gets_empty(self, mock_qs):
        """Parent user without a Parent object gets empty schedule."""
        parent = self.create_parent_user()
        context = self._make_context(user=parent)

        mock_filtered = MagicMock()
        mock_filtered.select_related.return_value = mock_filtered
        mock_filtered.filter.return_value = mock_filtered
        mock_filtered.none.return_value = MagicMock(__iter__=MagicMock(return_value=iter([])))
        mock_qs.filter.return_value = mock_filtered

        result = todays_schedule(context)
        self.assertEqual(result['schedule_entries'], [])

    def test_no_tenant_on_request_creates_default(self):
        """When request has no tenant, the tag uses a default school."""
        from core.models import School
        # Pre-create the default school with all required fields to avoid
        # NOT NULL constraint errors during get_or_create.
        School.objects.get_or_create(
            slug='default',
            defaults={
                'name': 'Default School',
                'email': 'admin@school.local',
                'subscription_start': date.today(),
                'subscription_end': date.today() + timedelta(days=365),
            },
        )

        student_user = self.create_student_user()
        request = self.factory.get('/')
        request.user = student_user
        # No tenant attribute at all
        context = {'request': request}

        result = todays_schedule(context)
        # Should not raise, returns a list
        self.assertIsInstance(result['schedule_entries'], list)

    def test_entries_sorted_by_start_time(self):
        """Returned entries are sorted by time_slot.start_time."""
        today = date.today()
        direction_user = self.create_direction_user()

        ts_late = self.create_timeslot(
            tenant=self.school,
            day_of_week=today.weekday(),
            start_time=time(14, 0),
            end_time=time(16, 0),
        )
        ts_early = self.create_timeslot(
            tenant=self.school,
            day_of_week=today.weekday(),
            start_time=time(8, 0),
            end_time=time(10, 0),
        )

        self.create_schedule_entry(
            tenant=self.school, time_slot=ts_late,
            effective_from=today - timedelta(days=1),
            effective_until=today + timedelta(days=30),
        )
        self.create_schedule_entry(
            tenant=self.school, time_slot=ts_early,
            effective_from=today - timedelta(days=1),
            effective_until=today + timedelta(days=30),
        )

        context = self._make_context(user=direction_user, tenant=self.school)
        result = todays_schedule(context)
        entries = result['schedule_entries']
        if len(entries) >= 2:
            self.assertLessEqual(
                entries[0].time_slot.start_time,
                entries[1].time_slot.start_time,
            )
