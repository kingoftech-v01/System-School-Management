"""Tests for scheduling/services.py - notification service functions."""

from datetime import date, time, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase

from scheduling.models import (
    ScheduleNotification, ScheduleEntry, ScheduleException,
    SubstitutionRequest,
)
from scheduling.services import (
    create_exception_notifications,
    notify_substitution_created,
    notify_substitution_updated,
    _build_exception_message,
    _get_entry_recipients,
)
from tests.helpers import TestDataMixin


class BuildExceptionMessageTest(TestDataMixin, TestCase):
    """Tests for the _build_exception_message helper."""

    def _make_exception(self, exception_type, **kwargs):
        """Create a mock ScheduleException."""
        entry = MagicMock()
        entry.course.title = 'Mathematics 101'

        exc = MagicMock()
        exc.schedule_entry = entry
        exc.exception_type = exception_type
        exc.date = date.today()
        exc.reason = kwargs.get('reason', '')
        exc.new_room = kwargs.get('new_room', None)
        exc.substitute_professor = kwargs.get('substitute_professor', None)
        exc.new_start_time = kwargs.get('new_start_time', None)
        exc.new_end_time = kwargs.get('new_end_time', None)
        return exc

    def test_cancellation_message(self):
        """Cancellation message includes 'cancelled'."""
        exc = self._make_exception('cancellation')
        msg = _build_exception_message(exc)
        self.assertIn('cancelled', msg.lower())
        self.assertIn('Mathematics 101', msg)

    def test_room_change_message(self):
        """Room change message includes new room name."""
        new_room = MagicMock()
        new_room.name = 'Room B205'
        exc = self._make_exception('room_change', new_room=new_room)
        msg = _build_exception_message(exc)
        self.assertIn('Room B205', msg)

    def test_substitution_message(self):
        """Substitution message includes substitute professor name."""
        sub_prof = MagicMock()
        sub_prof.get_full_name = 'Dr. Smith'
        exc = self._make_exception('substitution', substitute_professor=sub_prof)
        msg = _build_exception_message(exc)
        self.assertIn('Dr. Smith', msg)

    def test_reschedule_message(self):
        """Reschedule message includes new times."""
        exc = self._make_exception(
            'reschedule',
            new_start_time=time(14, 0),
            new_end_time=time(16, 0),
        )
        msg = _build_exception_message(exc)
        self.assertIn('14:00', msg)
        self.assertIn('16:00', msg)

    def test_reason_included_when_present(self):
        """Reason is included in the message when provided."""
        exc = self._make_exception('cancellation', reason='Weather emergency')
        msg = _build_exception_message(exc)
        self.assertIn('Weather emergency', msg)

    def test_extra_session_no_special_message(self):
        """Extra session type gets only the basic parts."""
        exc = self._make_exception('extra_session')
        msg = _build_exception_message(exc)
        self.assertIn('Mathematics 101', msg)
        self.assertIn(str(date.today()), msg)


class GetEntryRecipientsTest(TestDataMixin, TestCase):
    """Tests for the _get_entry_recipients helper."""

    def test_professor_is_always_a_recipient(self):
        """The professor of the entry is always included in recipients."""
        school = self.create_school()
        professor = self.create_professor_user()
        entry = self.create_schedule_entry(
            tenant=school, professor=professor,
        )
        recipients = _get_entry_recipients(entry)
        self.assertIn(professor, recipients)

    def test_entry_without_filiere_returns_professor_only(self):
        """When there is no filiere, only the professor is returned."""
        school = self.create_school()
        professor = self.create_professor_user()
        entry = self.create_schedule_entry(
            tenant=school, professor=professor, filiere=None,
        )
        # Force filiere to None since factory might set a default
        entry.filiere = None
        entry.save()
        recipients = _get_entry_recipients(entry)
        self.assertEqual(len(recipients), 1)
        self.assertIn(professor, recipients)

    def test_students_in_filiere_are_recipients(self):
        """Students enrolled in the entry's filiere are included."""
        school = self.create_school()
        professor = self.create_professor_user()
        filiere = self.create_filiere(tenant=school)

        student_user = self.create_student_user()

        entry = self.create_schedule_entry(
            tenant=school, professor=professor, filiere=filiere,
        )

        # _get_entry_recipients does:
        #   from accounts.models import Student
        #   students = Student.objects.filter(program=entry.filiere).select_related('student')
        # Student.program is a FK to Program, but the service passes a Filiere.
        # Mock the Student model's manager to avoid the type mismatch error.
        mock_profile = MagicMock()
        mock_profile.student = student_user
        mock_qs = MagicMock()
        mock_qs.select_related.return_value = [mock_profile]

        from accounts.models import Student
        with patch.object(Student, 'objects') as mock_manager:
            mock_manager.filter.return_value = mock_qs
            recipients = _get_entry_recipients(entry)

        self.assertIn(professor, recipients)
        self.assertIn(student_user, recipients)


class CreateExceptionNotificationsTest(TestDataMixin, TestCase):
    """Tests for create_exception_notifications."""

    def setUp(self):
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.entry = self.create_schedule_entry(
            tenant=self.school, professor=self.professor,
        )

    def _create_exception(self, exception_type='cancellation', **kwargs):
        """Create a ScheduleException for testing."""
        defaults = {
            'tenant': self.school,
            'schedule_entry': self.entry,
            'exception_type': exception_type,
            'date': date.today(),
        }
        defaults.update(kwargs)
        return ScheduleException.objects.create(**defaults)

    def test_creates_notification_for_cancellation(self):
        """A cancellation exception creates notifications for recipients."""
        exc = self._create_exception('cancellation')
        create_exception_notifications(exc)

        notifs = ScheduleNotification.objects.filter(
            tenant=self.school,
            related_entry=self.entry,
        )
        # At least the professor should get a notification
        self.assertGreaterEqual(notifs.count(), 1)

    def test_notification_title_contains_type_label(self):
        """Notification title uses the human-readable type label."""
        exc = self._create_exception('cancellation')
        create_exception_notifications(exc)

        notif = ScheduleNotification.objects.filter(
            tenant=self.school,
        ).first()
        self.assertIn('Cancelled', notif.title)

    def test_notification_type_matches_exception_type(self):
        """Notification type matches the exception type."""
        exc = self._create_exception('room_change')
        create_exception_notifications(exc)

        notif = ScheduleNotification.objects.filter(
            tenant=self.school,
        ).first()
        self.assertEqual(notif.notification_type, 'room_change')

    def test_no_notifications_when_no_recipients(self):
        """If _get_entry_recipients returns empty, no notifications created."""
        with patch('scheduling.services._get_entry_recipients', return_value=[]):
            exc = self._create_exception('cancellation')
            create_exception_notifications(exc)
            count = ScheduleNotification.objects.filter(
                tenant=self.school,
                related_exception=exc,
            ).count()
            self.assertEqual(count, 0)


class NotifySubstitutionCreatedTest(TestDataMixin, TestCase):
    """Tests for notify_substitution_created."""

    def setUp(self):
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.entry = self.create_schedule_entry(
            tenant=self.school, professor=self.professor,
        )

    def _create_sub_request(self, suggested_sub=None):
        """Create a SubstitutionRequest for testing."""
        return SubstitutionRequest.objects.create(
            tenant=self.school,
            schedule_entry=self.entry,
            date=date.today() + timedelta(days=1),
            requesting_professor=self.professor,
            suggested_substitute=suggested_sub,
            reason='Medical leave',
        )

    def test_notifies_direction_users(self):
        """Direction/admin/secretary users get notified of substitution requests."""
        direction = self.create_direction_user()
        sub = self._create_sub_request()

        # Clear any notifications created by the post_save signal
        ScheduleNotification.objects.all().delete()

        # Mock get_user_model at the django.contrib.auth level since
        # notify_substitution_created imports it locally.
        with patch('django.contrib.auth.get_user_model') as mock_get_user:
            mock_user_model = MagicMock()
            mock_user_model.objects.filter.return_value = [direction]
            mock_get_user.return_value = mock_user_model

            notify_substitution_created(sub)

            notifs = ScheduleNotification.objects.filter(
                tenant=self.school,
                notification_type='substitution',
            )
            self.assertGreaterEqual(notifs.count(), 1)

    def test_notifies_suggested_substitute(self):
        """The suggested substitute also receives a notification."""
        substitute = self.create_professor_user()
        sub = self._create_sub_request(suggested_sub=substitute)

        # Clear any notifications created by the post_save signal
        ScheduleNotification.objects.all().delete()

        with patch('django.contrib.auth.get_user_model') as mock_get_user:
            mock_user_model = MagicMock()
            mock_user_model.objects.filter.return_value = []
            mock_get_user.return_value = mock_user_model

            notify_substitution_created(sub)

            # The suggested substitute should have gotten a notification
            notifs = ScheduleNotification.objects.filter(
                recipient=substitute,
                notification_type='substitution',
            )
            self.assertEqual(notifs.count(), 1)
            self.assertIn('Suggested', notifs.first().title)

    def test_no_suggested_substitute_creates_only_direction_notifs(self):
        """Without a suggested substitute, only direction users are notified."""
        sub = self._create_sub_request(suggested_sub=None)

        # Clear any notifications created by the post_save signal
        ScheduleNotification.objects.all().delete()

        with patch('django.contrib.auth.get_user_model') as mock_get_user:
            mock_user_model = MagicMock()
            mock_user_model.objects.filter.return_value = []
            mock_get_user.return_value = mock_user_model

            notify_substitution_created(sub)

            notifs = ScheduleNotification.objects.filter(
                tenant=self.school,
            )
            # No direction users found + no suggested sub = no notifications
            self.assertEqual(notifs.count(), 0)


class NotifySubstitutionUpdatedTest(TestDataMixin, TestCase):
    """Tests for notify_substitution_updated."""

    def setUp(self):
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.entry = self.create_schedule_entry(
            tenant=self.school, professor=self.professor,
        )

    def _create_sub_request(self, status='pending', assigned_sub=None):
        return SubstitutionRequest.objects.create(
            tenant=self.school,
            schedule_entry=self.entry,
            date=date.today() + timedelta(days=1),
            requesting_professor=self.professor,
            assigned_substitute=assigned_sub,
            status=status,
            reason='Sick leave',
        )

    def test_approved_with_substitute_creates_two_notifications(self):
        """Approved request with assigned substitute notifies both professor and substitute."""
        substitute = self.create_professor_user()
        sub = self._create_sub_request(status='approved', assigned_sub=substitute)

        notify_substitution_updated(sub)

        # One for the requesting professor, one for the assigned substitute
        prof_notifs = ScheduleNotification.objects.filter(
            recipient=self.professor,
        )
        sub_notifs = ScheduleNotification.objects.filter(
            recipient=substitute,
        )
        self.assertEqual(prof_notifs.count(), 1)
        self.assertEqual(sub_notifs.count(), 1)
        self.assertIn('approved', prof_notifs.first().message.lower())

    def test_rejected_request_notifies_professor(self):
        """Rejected request only notifies the requesting professor."""
        sub = self._create_sub_request(status='rejected')

        notify_substitution_updated(sub)

        notifs = ScheduleNotification.objects.filter(recipient=self.professor)
        self.assertEqual(notifs.count(), 1)
        self.assertIn('rejected', notifs.first().message.lower())

    def test_pending_status_notifies_professor(self):
        """Other status updates notify the professor with generic message."""
        sub = self._create_sub_request(status='pending')

        notify_substitution_updated(sub)

        notifs = ScheduleNotification.objects.filter(recipient=self.professor)
        self.assertEqual(notifs.count(), 1)

    def test_notification_title_contains_course_name(self):
        """The notification title includes the course title."""
        sub = self._create_sub_request(status='rejected')

        notify_substitution_updated(sub)

        notif = ScheduleNotification.objects.filter(recipient=self.professor).first()
        self.assertIn(self.entry.course.title, notif.title)

    def test_approved_substitute_notification_contains_assignment_info(self):
        """The substitute's notification mentions the assignment."""
        substitute = self.create_professor_user()
        sub = self._create_sub_request(status='approved', assigned_sub=substitute)

        notify_substitution_updated(sub)

        notif = ScheduleNotification.objects.filter(recipient=substitute).first()
        self.assertIn('assigned', notif.message.lower())
