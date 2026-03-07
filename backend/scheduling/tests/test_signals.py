"""
Tests for scheduling signal handlers.

Signals tested:
1. notify_schedule_exception (post_save on ScheduleException) - calls
   create_exception_notifications when a new exception is created with
   notify_students=True
2. notify_substitution_status (post_save on SubstitutionRequest) - calls
   notify_substitution_created on creation, notify_substitution_updated
   on status change to approved/rejected/fulfilled
"""

from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase

from scheduling.models import (
    ScheduleException,
    SubstitutionRequest,
)
from tests.helpers import TestDataMixin


class NotifyScheduleExceptionSignalTest(TestDataMixin, TestCase):
    """Tests for the notify_schedule_exception post_save signal."""

    def _make_exception(self, schedule_entry=None, notify_students=True,
                        exception_type='cancellation', **kwargs):
        """Helper to create a ScheduleException."""
        if schedule_entry is None:
            school = self.create_school()
            schedule_entry = self.create_schedule_entry(tenant=school)
        return ScheduleException.objects.create(
            tenant=schedule_entry.tenant,
            schedule_entry=schedule_entry,
            exception_type=exception_type,
            date=date.today() + timedelta(days=1),
            notify_students=notify_students,
            **kwargs,
        )

    @patch('scheduling.services.create_exception_notifications')
    def test_new_exception_with_notify_triggers_notification(
        self, mock_create_notif
    ):
        """Creating a ScheduleException with notify_students=True calls
        create_exception_notifications."""
        exc = self._make_exception(notify_students=True)
        mock_create_notif.assert_called_once_with(exc)

    @patch('scheduling.services.create_exception_notifications')
    def test_new_exception_without_notify_skips_notification(
        self, mock_create_notif
    ):
        """Creating a ScheduleException with notify_students=False does NOT
        call create_exception_notifications."""
        self._make_exception(notify_students=False)
        mock_create_notif.assert_not_called()

    @patch('scheduling.services.create_exception_notifications')
    def test_update_exception_does_not_trigger_notification(
        self, mock_create_notif
    ):
        """Updating an existing ScheduleException does NOT trigger
        create_exception_notifications (only created=True fires)."""
        exc = self._make_exception(notify_students=True)
        mock_create_notif.reset_mock()

        exc.reason = 'Updated reason'
        exc.save()

        mock_create_notif.assert_not_called()

    @patch('scheduling.services.create_exception_notifications')
    def test_cancellation_exception_notifies(self, mock_create_notif):
        """A cancellation exception with notifications triggers the service."""
        exc = self._make_exception(
            exception_type='cancellation', notify_students=True
        )
        mock_create_notif.assert_called_once_with(exc)

    @patch('scheduling.services.create_exception_notifications')
    def test_room_change_exception_notifies(self, mock_create_notif):
        """A room_change exception with notifications triggers the service."""
        exc = self._make_exception(
            exception_type='room_change', notify_students=True
        )
        mock_create_notif.assert_called_once_with(exc)


class NotifySubstitutionStatusSignalTest(TestDataMixin, TestCase):
    """Tests for the notify_substitution_status post_save signal."""

    def _make_substitution(self, schedule_entry=None, **kwargs):
        """Helper to create a SubstitutionRequest."""
        if schedule_entry is None:
            school = self.create_school()
            schedule_entry = self.create_schedule_entry(tenant=school)
        professor = schedule_entry.professor
        defaults = {
            'tenant': schedule_entry.tenant,
            'schedule_entry': schedule_entry,
            'date': date.today() + timedelta(days=3),
            'requesting_professor': professor,
            'reason': 'Medical leave',
            'status': 'pending',
        }
        defaults.update(kwargs)
        return SubstitutionRequest.objects.create(**defaults)

    @patch('scheduling.services.notify_substitution_created')
    def test_new_substitution_triggers_created_notification(
        self, mock_notify_created
    ):
        """Creating a SubstitutionRequest calls notify_substitution_created."""
        sub = self._make_substitution()
        mock_notify_created.assert_called_once_with(sub)

    @patch('scheduling.services.notify_substitution_created')
    def test_update_substitution_does_not_trigger_created_notification(
        self, mock_notify_created
    ):
        """Updating a SubstitutionRequest does NOT call
        notify_substitution_created."""
        sub = self._make_substitution()
        mock_notify_created.reset_mock()

        sub.reason = 'Updated reason'
        sub.save()

        mock_notify_created.assert_not_called()

    @patch('scheduling.services.notify_substitution_updated')
    @patch('scheduling.services.notify_substitution_created')
    def test_approved_status_triggers_updated_notification(
        self, mock_created, mock_updated
    ):
        """Setting status to 'approved' on update calls
        notify_substitution_updated."""
        sub = self._make_substitution()
        mock_updated.reset_mock()

        sub.status = 'approved'
        sub.save()

        mock_updated.assert_called_once_with(sub)

    @patch('scheduling.services.notify_substitution_updated')
    @patch('scheduling.services.notify_substitution_created')
    def test_rejected_status_triggers_updated_notification(
        self, mock_created, mock_updated
    ):
        """Setting status to 'rejected' on update calls
        notify_substitution_updated."""
        sub = self._make_substitution()
        mock_updated.reset_mock()

        sub.status = 'rejected'
        sub.save()

        mock_updated.assert_called_once_with(sub)

    @patch('scheduling.services.notify_substitution_updated')
    @patch('scheduling.services.notify_substitution_created')
    def test_fulfilled_status_triggers_updated_notification(
        self, mock_created, mock_updated
    ):
        """Setting status to 'fulfilled' on update calls
        notify_substitution_updated."""
        sub = self._make_substitution()
        mock_updated.reset_mock()

        sub.status = 'fulfilled'
        sub.save()

        mock_updated.assert_called_once_with(sub)

    @patch('scheduling.services.notify_substitution_updated')
    @patch('scheduling.services.notify_substitution_created')
    def test_pending_status_update_does_not_trigger_updated_notification(
        self, mock_created, mock_updated
    ):
        """Saving with status still 'pending' does NOT call
        notify_substitution_updated."""
        sub = self._make_substitution()
        mock_updated.reset_mock()

        sub.reason = 'Different reason'
        sub.save()

        mock_updated.assert_not_called()

    @patch('scheduling.services.notify_substitution_updated')
    @patch('scheduling.services.notify_substitution_created')
    def test_created_with_approved_status_calls_created_not_updated(
        self, mock_created, mock_updated
    ):
        """Creating a substitution request directly with 'approved' status
        calls notify_substitution_created (created=True), not
        notify_substitution_updated."""
        sub = self._make_substitution(status='approved')
        mock_created.assert_called_once()
        mock_updated.assert_not_called()
