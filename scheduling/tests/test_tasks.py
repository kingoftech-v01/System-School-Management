"""
Tests for scheduling app Celery tasks.

Note: The scheduling tasks use lazy imports (imports inside the function body),
so we must patch at the original module path (e.g. django.core.mail.send_mail)
rather than at the task module path.
"""

from datetime import date, time, timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase

from scheduling.models import (
    ScheduleEntry,
    ScheduleNotification,
    TimeSlot,
    TimetableGeneration,
)
from scheduling.tasks import (
    generate_timetable_task,
    send_daily_schedule_reminder,
    send_schedule_change_notifications,
)
from tests.helpers import TestDataMixin


class TestGenerateTimetableTask(TestDataMixin, TestCase):
    """Tests for generate_timetable_task."""

    def setUp(self):
        self.school = self.create_school()
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)

    def test_runs_generator_for_valid_id(self):
        """Task should instantiate TimetableGenerator and call generate()."""
        generation = TimetableGeneration.objects.create(
            tenant=self.school,
            session=self.session,
            semester=self.semester,
            status='pending',
        )

        mock_generator_instance = MagicMock()
        mock_generator_cls = MagicMock(return_value=mock_generator_instance)

        with patch.dict(
            'sys.modules',
            {'scheduling.engine.generator': MagicMock(TimetableGenerator=mock_generator_cls)}
        ):
            # Re-import to pick up the mock
            import importlib
            import scheduling.tasks as tasks_mod
            importlib.reload(tasks_mod)

            tasks_mod.generate_timetable_task(generation.id)

            mock_generator_cls.assert_called_once()
            mock_generator_instance.generate.assert_called_once()

        # Reload the original module to clean up
        import importlib
        importlib.reload(tasks_mod)

    def test_raises_for_nonexistent_id(self):
        """Task should raise DoesNotExist for non-existent generation ID."""
        with self.assertRaises(TimetableGeneration.DoesNotExist):
            generate_timetable_task(99999)


class TestSendScheduleChangeNotifications(TestDataMixin, TestCase):
    """Tests for send_schedule_change_notifications task."""

    def setUp(self):
        self.school = self.create_school()

    @patch('django.core.mail.send_mail')
    def test_sends_email_for_pending_notifications(self, mock_send_mail):
        """Task should send emails for pending notifications."""
        user = self.create_user()
        user.email = 'test@example.com'
        user.save()

        notification = ScheduleNotification.objects.create(
            tenant=self.school,
            recipient=user,
            notification_type='cancellation',
            title='Class Cancelled',
            message='Your math class has been cancelled.',
            email_sent=False,
        )

        send_schedule_change_notifications()

        notification.refresh_from_db()
        self.assertTrue(notification.email_sent)
        mock_send_mail.assert_called_once()

    @patch('django.core.mail.send_mail')
    def test_skips_already_sent_notifications(self, mock_send_mail):
        """Task should not resend already sent notifications."""
        user = self.create_user()
        ScheduleNotification.objects.create(
            tenant=self.school,
            recipient=user,
            notification_type='cancellation',
            title='Already Sent',
            message='This was already sent.',
            email_sent=True,
        )

        send_schedule_change_notifications()

        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')
    def test_marks_sent_even_if_no_email(self, mock_send_mail):
        """Task should mark notification as sent even if user has no email."""
        user = self.create_user()
        user.email = ''
        user.save()

        notification = ScheduleNotification.objects.create(
            tenant=self.school,
            recipient=user,
            notification_type='room_change',
            title='Room Changed',
            message='Room changed.',
            email_sent=False,
        )

        send_schedule_change_notifications()

        notification.refresh_from_db()
        self.assertTrue(notification.email_sent)
        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')
    def test_handles_empty_notifications(self, mock_send_mail):
        """Task should handle gracefully when no pending notifications exist."""
        send_schedule_change_notifications()
        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')
    def test_batches_up_to_50_notifications(self, mock_send_mail):
        """Task should process up to 50 notifications per batch."""
        user = self.create_user()
        user.email = 'batch@example.com'
        user.save()

        for i in range(55):
            ScheduleNotification.objects.create(
                tenant=self.school,
                recipient=user,
                notification_type='reminder',
                title=f'Reminder {i}',
                message=f'Reminder message {i}',
                email_sent=False,
            )

        send_schedule_change_notifications()

        # Should only process 50 (batch limit)
        sent_count = ScheduleNotification.objects.filter(email_sent=True).count()
        self.assertEqual(sent_count, 50)
        self.assertEqual(mock_send_mail.call_count, 50)


class TestSendDailyScheduleReminder(TestDataMixin, TestCase):
    """Tests for send_daily_schedule_reminder task."""

    def setUp(self):
        self.school = self.create_school()

    @patch('django.core.mail.send_mail')
    def test_sends_reminder_to_professor(self, mock_send_mail):
        """Task should send tomorrow's schedule to professors."""
        tomorrow = date.today() + timedelta(days=1)
        day_of_week = tomorrow.weekday()

        professor = self.create_professor_user(email='prof@example.com')
        course = self.create_course()
        time_slot = self.create_timeslot(
            tenant=self.school,
            day_of_week=day_of_week,
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        self.create_schedule_entry(
            tenant=self.school,
            course=course,
            professor=professor,
            time_slot=time_slot,
            effective_from=tomorrow - timedelta(days=7),
            effective_until=tomorrow + timedelta(days=7),
            status='active',
        )

        send_daily_schedule_reminder()

        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args
        # Verify the recipient is the professor
        recipient_list = call_kwargs.kwargs.get('recipient_list') or call_kwargs[1].get('recipient_list', [])
        if not recipient_list and len(call_kwargs.args) > 3:
            recipient_list = call_kwargs.args[3]
        self.assertIn('prof@example.com', recipient_list)

    @patch('django.core.mail.send_mail')
    def test_no_email_for_cancelled_entries(self, mock_send_mail):
        """Task should not send reminders for cancelled entries."""
        tomorrow = date.today() + timedelta(days=1)
        day_of_week = tomorrow.weekday()

        professor = self.create_professor_user(email='prof2@example.com')
        course = self.create_course()
        time_slot = self.create_timeslot(
            tenant=self.school,
            day_of_week=day_of_week,
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        self.create_schedule_entry(
            tenant=self.school,
            course=course,
            professor=professor,
            time_slot=time_slot,
            effective_from=tomorrow - timedelta(days=7),
            effective_until=tomorrow + timedelta(days=7),
            status='cancelled',
        )

        send_daily_schedule_reminder()

        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')
    def test_no_email_when_no_entries(self, mock_send_mail):
        """Task should send no emails when there are no schedule entries."""
        send_daily_schedule_reminder()
        mock_send_mail.assert_not_called()

    @patch('django.core.mail.send_mail')
    def test_no_email_for_professor_without_email(self, mock_send_mail):
        """Task should skip professors without email addresses."""
        tomorrow = date.today() + timedelta(days=1)
        day_of_week = tomorrow.weekday()

        professor = self.create_professor_user(email='')
        course = self.create_course()
        time_slot = self.create_timeslot(
            tenant=self.school,
            day_of_week=day_of_week,
            start_time=time(8, 0),
            end_time=time(10, 0),
        )
        self.create_schedule_entry(
            tenant=self.school,
            course=course,
            professor=professor,
            time_slot=time_slot,
            effective_from=tomorrow - timedelta(days=7),
            effective_until=tomorrow + timedelta(days=7),
            status='active',
        )

        send_daily_schedule_reminder()

        mock_send_mail.assert_not_called()
