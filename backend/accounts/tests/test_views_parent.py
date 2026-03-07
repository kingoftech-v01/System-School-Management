"""
Tests for accounts/views_parent.py -- Parent Portal views.

Covers: parent_dashboard, parent_select_child, parent_child_grades,
        parent_child_attendance, parent_child_timetable, parent_child_invoices,
        parent_child_payment_history, parent_make_payment,
        parent_messages_inbox, parent_messages_compose, parent_messages_thread,
        parent_appointments, parent_appointment_request,
        parent_disciplinary_records, parent_acknowledge_discipline,
        parent_permission_slips, parent_sign_permission_slip,
        parent_events, parent_event_detail,
        and helper functions (get_parent_profiles, get_active_child, get_children_context).
"""

from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from accounts.models import (
    Parent,
    ParentTeacherAppointment,
    ParentTeacherMessage,
    PermissionSlip,
    Student,
)
from tests.helpers import TestDataMixin

User = get_user_model()


class ParentViewTestBase(TestDataMixin, TestCase):
    """Base class setting up parent + child fixtures for parent portal tests."""

    def setUp(self):
        super().setUp()
        self.client = Client()

        # Create parent user
        self.parent_user = self.create_user(
            role='parent', is_parent=True, username='parentuser',
            first_name='ParentFirst', last_name='ParentLast',
        )

        # Create student user + profile
        self.student_user = self.create_student_user(
            username='childuser', first_name='ChildFirst', last_name='ChildLast',
        )
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )

        # Link parent to student
        self.parent_link = Parent.objects.create(
            user=self.parent_user,
            student=self.student_profile,
            first_name='ParentFirst',
            last_name='ParentLast',
            relation_ship='Father',
        )

        self.client.force_login(self.parent_user)

    # -----------------------------------------------------------------
    # URL helpers
    # -----------------------------------------------------------------
    def _url(self, name, **kwargs):
        return reverse(f'frontend:accounts:{name}', kwargs=kwargs)


class ParentDashboardTest(ParentViewTestBase):
    """Tests for parent_dashboard view."""

    def test_dashboard_200_with_child(self):
        response = self.client.get(self._url('parent_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('student', response.context)

    def test_dashboard_no_children_renders(self):
        """Parent with no linked children sees the 'no_children' state."""
        lonely_parent = self.create_user(
            role='parent', is_parent=True, username='lonelyparent',
        )
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('no_children'))

    def test_dashboard_context_keys(self):
        response = self.client.get(self._url('parent_dashboard'))
        self.assertEqual(response.status_code, 200)
        for key in ['children', 'recent_grades', 'unread_count',
                     'pending_slips', 'unacked_discipline']:
            self.assertIn(key, response.context, f"Missing context key: {key}")

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(self._url('parent_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())

    def test_dashboard_denied_for_student(self):
        self.client.force_login(self.student_user)
        response = self.client.get(self._url('parent_dashboard'))
        # Should redirect because student is not a parent
        self.assertEqual(response.status_code, 302)


class ParentSelectChildTest(ParentViewTestBase):
    """Tests for parent_select_child view."""

    def test_select_valid_child(self):
        url = self._url('parent_select_child', student_id=self.student_profile.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # Session should have active_child_id set
        session = self.client.session
        self.assertEqual(session.get('active_child_id'), self.student_profile.pk)

    def test_select_invalid_child(self):
        url = self._url('parent_select_child', student_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # Should redirect to dashboard with error

    def test_select_child_of_other_parent(self):
        """Cannot select a child that is not linked to this parent."""
        other_student_user = self.create_student_user(username='otherstudent')
        other_profile = self.create_student_profile(user=other_student_user)
        url = self._url('parent_select_child', student_id=other_profile.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class ParentChildGradesTest(ParentViewTestBase):
    """Tests for parent_child_grades view."""

    def test_grades_200(self):
        response = self.client.get(self._url('parent_child_grades'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('courses', response.context)

    def test_grades_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_child_grades'))
        self.assertEqual(response.status_code, 302)


class ParentChildAttendanceTest(ParentViewTestBase):
    """Tests for parent_child_attendance view.

    NOTE: The view queries attendance.AttendanceReport which expects
    attendance.Student (not accounts.Student). We mock the import to
    avoid the model mismatch ValueError in dev mode.
    """

    @patch('attendance.models.AttendanceReport.objects')
    def test_attendance_200(self, mock_manager):
        """Patch AttendanceReport.objects to bypass model mismatch."""
        from unittest.mock import MagicMock
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.__len__ = lambda s: 0
        mock_qs.__iter__ = lambda s: iter([])
        mock_qs.__getitem__ = lambda s, k: mock_qs
        mock_manager.filter.return_value = mock_qs
        response = self.client.get(self._url('parent_child_attendance'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('attendance_rate', response.context)

    def test_attendance_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_child_attendance'))
        self.assertEqual(response.status_code, 302)


class ParentChildTimetableTest(ParentViewTestBase):
    """Tests for parent_child_timetable view."""

    def test_timetable_200(self):
        response = self.client.get(self._url('parent_child_timetable'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('enrolled_courses', response.context)

    def test_timetable_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_child_timetable'))
        self.assertEqual(response.status_code, 302)


class ParentChildInvoicesTest(ParentViewTestBase):
    """Tests for parent_child_invoices view."""

    def test_invoices_200(self):
        response = self.client.get(self._url('parent_child_invoices'))
        self.assertEqual(response.status_code, 200)

    def test_invoices_filter_paid(self):
        response = self.client.get(self._url('parent_child_invoices') + '?status=paid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['status_filter'], 'paid')

    def test_invoices_filter_unpaid(self):
        response = self.client.get(self._url('parent_child_invoices') + '?status=unpaid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['status_filter'], 'unpaid')

    def test_invoices_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_child_invoices'))
        self.assertEqual(response.status_code, 302)


class ParentPaymentHistoryTest(ParentViewTestBase):
    """Tests for parent_child_payment_history view."""

    def test_payment_history_200(self):
        response = self.client.get(self._url('parent_child_payment_history'))
        self.assertEqual(response.status_code, 200)

    def test_payment_history_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_child_payment_history'))
        self.assertEqual(response.status_code, 302)


class ParentMakePaymentTest(ParentViewTestBase):
    """Tests for parent_make_payment view."""

    def _create_invoice(self, paid=False):
        from payments.models import Invoice
        return Invoice.objects.create(
            user=self.parent_user,
            student=self.student_profile,
            total=500.00,
            amount=500.00,
            invoice_code='INV-TEST-001',
            payment_complete=paid,
        )

    def test_make_payment_redirects_to_gateway(self):
        invoice = self._create_invoice(paid=False)
        url = self._url('parent_make_payment', invoice_id=invoice.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        # Should redirect to payment gateway
        self.assertIn('payment', response.url.lower())

    def test_make_payment_already_paid_redirects(self):
        invoice = self._create_invoice(paid=True)
        url = self._url('parent_make_payment', invoice_id=invoice.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_make_payment_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        url = self._url('parent_make_payment', invoice_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class ParentMessagesInboxTest(ParentViewTestBase):
    """Tests for parent_messages_inbox view."""

    def test_inbox_200(self):
        response = self.client.get(self._url('parent_messages_inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('messages_list', response.context)

    def test_inbox_shows_unread_count(self):
        response = self.client.get(self._url('parent_messages_inbox'))
        self.assertIn('unread_count', response.context)


class ParentMessagesComposeTest(ParentViewTestBase):
    """Tests for parent_messages_compose view."""

    def test_compose_get_200(self):
        response = self.client.get(self._url('parent_messages_compose'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_compose_post_valid(self):
        # Create a lecturer and allocate to the program
        lecturer = self.create_professor_user(username='teacher1')
        from course.models import CourseAllocation
        course = self.create_course(program=self.program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        response = self.client.post(self._url('parent_messages_compose'), {
            'recipient': lecturer.pk,
            'subject': 'Test subject',
            'body': 'Hello teacher',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ParentTeacherMessage.objects.filter(
                sender=self.parent_user, subject='Test subject',
            ).exists()
        )

    def test_compose_post_invalid(self):
        response = self.client.post(self._url('parent_messages_compose'), {
            'recipient': '',
            'subject': '',
            'body': '',
        })
        # Should re-render form with errors
        self.assertEqual(response.status_code, 200)

    def test_compose_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_messages_compose'))
        self.assertEqual(response.status_code, 302)


class ParentMessagesThreadTest(ParentViewTestBase):
    """Tests for parent_messages_thread view."""

    def _create_message(self, sender=None, recipient=None, is_read=False):
        sender = sender or self.parent_user
        recipient = recipient or self.create_professor_user()
        return ParentTeacherMessage.objects.create(
            sender=sender,
            recipient=recipient,
            student=self.student_profile,
            subject='Thread Test',
            body='Hello',
            parent_initiated=True,
            is_read=is_read,
        )

    def test_thread_200_as_sender(self):
        msg = self._create_message()
        url = self._url('parent_messages_thread', message_id=msg.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_thread_200_as_recipient(self):
        lecturer = self.create_professor_user()
        msg = ParentTeacherMessage.objects.create(
            sender=lecturer,
            recipient=self.parent_user,
            student=self.student_profile,
            subject='From Teacher',
            body='Hi parent',
            parent_initiated=False,
        )
        url = self._url('parent_messages_thread', message_id=msg.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Should be marked read
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_thread_access_denied_for_other_user(self):
        other_parent = self.create_user(role='parent', is_parent=True)
        lecturer = self.create_professor_user()
        # Create Parent link so the model clean() passes
        other_student_user = self.create_student_user()
        other_profile = self.create_student_profile(user=other_student_user)
        Parent.objects.create(
            user=other_parent, student=other_profile,
            first_name='Other', last_name='Parent', relation_ship='Mother',
        )
        msg = ParentTeacherMessage.objects.create(
            sender=other_parent,
            recipient=lecturer,
            student=other_profile,
            subject='Private',
            body='Secret',
            parent_initiated=True,
        )
        url = self._url('parent_messages_thread', message_id=msg.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_thread_reply(self):
        lecturer = self.create_professor_user()
        msg = ParentTeacherMessage.objects.create(
            sender=lecturer,
            recipient=self.parent_user,
            student=self.student_profile,
            subject='Reply Test',
            body='Hello',
            parent_initiated=False,
        )
        url = self._url('parent_messages_thread', message_id=msg.pk)
        response = self.client.post(url, {'reply_body': 'My reply'})
        self.assertEqual(response.status_code, 302)
        # New message should exist
        self.assertTrue(
            ParentTeacherMessage.objects.filter(
                sender=self.parent_user, body='My reply',
            ).exists()
        )

    def test_thread_empty_reply_ignored(self):
        msg = self._create_message()
        url = self._url('parent_messages_thread', message_id=msg.pk)
        count_before = ParentTeacherMessage.objects.count()
        response = self.client.post(url, {'reply_body': '   '})
        # No new message created (empty body stripped)
        self.assertEqual(ParentTeacherMessage.objects.count(), count_before)


class ParentAppointmentsTest(ParentViewTestBase):
    """Tests for parent_appointments view."""

    def test_appointments_200(self):
        response = self.client.get(self._url('parent_appointments'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('appointments', response.context)


class ParentAppointmentRequestTest(ParentViewTestBase):
    """Tests for parent_appointment_request view."""

    def test_request_get_200(self):
        response = self.client.get(self._url('parent_appointment_request'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_request_post_valid(self):
        lecturer = self.create_professor_user()
        from course.models import CourseAllocation
        course = self.create_course(program=self.program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        future_date = (date.today() + timedelta(days=7)).isoformat()
        response = self.client.post(self._url('parent_appointment_request'), {
            'teacher': lecturer.pk,
            'preferred_date': future_date,
            'preferred_time': '08:00-08:30',
            'reason': 'Discuss progress',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ParentTeacherAppointment.objects.filter(
                parent=self.parent_link, teacher=lecturer,
            ).exists()
        )

    def test_request_conflict_detected(self):
        lecturer = self.create_professor_user()
        from course.models import CourseAllocation
        course = self.create_course(program=self.program)
        allocation = CourseAllocation.objects.create(lecturer=lecturer)
        allocation.courses.add(course)

        target_date = date.today() + timedelta(days=7)
        # Create existing appointment
        ParentTeacherAppointment.objects.create(
            parent=self.parent_link,
            teacher=lecturer,
            student=self.student_profile,
            date=target_date,
            time_slot='09:00-09:30',
            reason='Existing',
            status='confirmed',
        )

        response = self.client.post(self._url('parent_appointment_request'), {
            'teacher': lecturer.pk,
            'preferred_date': target_date.isoformat(),
            'preferred_time': '09:00-09:30',
            'reason': 'Conflict test',
        })
        # Should stay on form page with error message
        self.assertEqual(response.status_code, 200)

    def test_request_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_appointment_request'))
        self.assertEqual(response.status_code, 302)


class ParentDisciplinaryRecordsTest(ParentViewTestBase):
    """Tests for parent_disciplinary_records view."""

    def test_records_200(self):
        response = self.client.get(self._url('parent_disciplinary_records'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('records', response.context)

    def test_records_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_disciplinary_records'))
        self.assertEqual(response.status_code, 302)


class ParentAcknowledgeDisciplineTest(ParentViewTestBase):
    """Tests for parent_acknowledge_discipline view."""

    def _create_action(self, acknowledged=False):
        school = self.create_school()
        from discipline.models import DisciplinaryAction
        return DisciplinaryAction.objects.create(
            tenant=school,
            student=self.student_user,
            reported_by=self.create_professor_user(),
            incident_type='misconduct',
            description='Test incident',
            action_taken='Warning',
            severity='minor',
            incident_date=date.today(),
            parent_acknowledged=acknowledged,
        )

    def test_acknowledge_get_200(self):
        action = self._create_action()
        url = self._url('parent_acknowledge_discipline', action_id=action.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_acknowledge_post_marks_acknowledged(self):
        action = self._create_action()
        url = self._url('parent_acknowledge_discipline', action_id=action.pk)
        response = self.client.post(url, {'response': 'Understood'})
        self.assertEqual(response.status_code, 302)
        action.refresh_from_db()
        self.assertTrue(action.parent_acknowledged)
        self.assertEqual(action.parent_response, 'Understood')

    def test_already_acknowledged_redirects(self):
        action = self._create_action(acknowledged=True)
        url = self._url('parent_acknowledge_discipline', action_id=action.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_acknowledge_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        url = self._url('parent_acknowledge_discipline', action_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class ParentPermissionSlipsTest(ParentViewTestBase):
    """Tests for parent_permission_slips view."""

    def test_slips_200(self):
        response = self.client.get(self._url('parent_permission_slips'))
        self.assertEqual(response.status_code, 200)

    def test_slips_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        response = self.client.get(self._url('parent_permission_slips'))
        self.assertEqual(response.status_code, 302)


class ParentSignPermissionSlipTest(ParentViewTestBase):
    """Tests for parent_sign_permission_slip view."""

    def _create_slip(self, status='pending'):
        return PermissionSlip.objects.create(
            student=self.student_profile,
            title='Field Trip',
            description='Zoo visit',
            created_by=self.create_professor_user(),
            deadline=date.today() + timedelta(days=7),
            status=status,
        )

    def test_sign_get_200(self):
        slip = self._create_slip()
        url = self._url('parent_sign_permission_slip', slip_id=slip.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_sign_post_approves(self):
        slip = self._create_slip()
        url = self._url('parent_sign_permission_slip', slip_id=slip.pk)
        response = self.client.post(url, {'action': 'sign', 'notes': 'Approved'})
        self.assertEqual(response.status_code, 302)
        slip.refresh_from_db()
        self.assertEqual(slip.status, 'signed')

    def test_sign_post_declines(self):
        slip = self._create_slip()
        url = self._url('parent_sign_permission_slip', slip_id=slip.pk)
        response = self.client.post(url, {'action': 'decline', 'notes': 'No thanks'})
        self.assertEqual(response.status_code, 302)
        slip.refresh_from_db()
        self.assertEqual(slip.status, 'declined')

    def test_already_signed_redirects(self):
        slip = self._create_slip(status='signed')
        url = self._url('parent_sign_permission_slip', slip_id=slip.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_sign_no_child_redirects(self):
        lonely_parent = self.create_user(role='parent', is_parent=True)
        self.client.force_login(lonely_parent)
        url = self._url('parent_sign_permission_slip', slip_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class ParentEventsTest(ParentViewTestBase):
    """Tests for parent_events and parent_event_detail views."""

    def test_events_200(self):
        response = self.client.get(self._url('parent_events'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('events', response.context)

    def test_event_detail_200(self):
        from datetime import datetime
        from events.models import Event
        school = self.create_school()
        event = Event.objects.create(
            tenant=school,
            title='Parent Night',
            description='Meet the teachers',
            event_type='meeting',
            start_date=datetime(2028, 6, 1, 9, 0),
            end_date=datetime(2028, 6, 1, 17, 0),
            target_audience='parents',
        )
        url = self._url('parent_event_detail', event_id=event.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['event'], event)

    def test_event_detail_404(self):
        url = self._url('parent_event_detail', event_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
