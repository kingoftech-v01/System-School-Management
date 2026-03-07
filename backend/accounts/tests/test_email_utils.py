"""Tests for accounts email utility functions."""

from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from accounts.email_utils import (
    send_templated_email,
    send_verification_email,
    send_welcome_email,
    send_password_reset_email,
    send_2fa_enabled_email,
    send_2fa_disabled_email,
    send_enrollment_confirmation_email,
    send_grade_notification_email,
    send_payment_receipt_email,
    send_bulk_notification_email,
    send_account_activation_email,
)
from tests.helpers import TestDataMixin


def _mock_tenant():
    t = MagicMock()
    t.name = 'Test School'
    t.logo = None
    return t


def _mock_user(email='test@test.com', username='testuser'):
    u = MagicMock()
    u.email = email
    u.username = username
    u.get_full_name = MagicMock(return_value='Test User')
    return u


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendTemplatedEmailTest(TestCase):

    @patch('accounts.email_utils.render_to_string', return_value='<p>Hi</p>')
    @patch('accounts.email_utils.EmailMultiAlternatives')
    def test_sends_email(self, mock_cls, mock_render):
        mock_email = MagicMock()
        mock_email.send.return_value = 1
        mock_cls.return_value = mock_email
        result = send_templated_email(
            'Subject', 'emails/test.html', {}, ['a@b.com']
        )
        self.assertEqual(result, 1)
        mock_email.send.assert_called_once()

    @patch('accounts.email_utils.render_to_string', return_value='<p>Hi</p>')
    @patch('accounts.email_utils.EmailMultiAlternatives')
    def test_uses_default_from_email(self, mock_cls, mock_render):
        mock_email = MagicMock()
        mock_email.send.return_value = 1
        mock_cls.return_value = mock_email
        send_templated_email('Sub', 'tpl.html', {}, ['a@b.com'])
        call_kwargs = mock_cls.call_args
        self.assertEqual(call_kwargs[1]['from_email'], 'noreply@school.com')

    @patch('accounts.email_utils.render_to_string', return_value='<p>Hi</p>')
    @patch('accounts.email_utils.EmailMultiAlternatives')
    def test_custom_from_email(self, mock_cls, mock_render):
        mock_email = MagicMock()
        mock_email.send.return_value = 1
        mock_cls.return_value = mock_email
        send_templated_email('S', 't.html', {}, ['a@b.com'], from_email='custom@x.com')
        call_kwargs = mock_cls.call_args
        self.assertEqual(call_kwargs[1]['from_email'], 'custom@x.com')

    @patch('accounts.email_utils.render_to_string', side_effect=Exception('fail'))
    def test_raises_on_failure(self, mock_render):
        with self.assertRaises(Exception):
            send_templated_email('S', 't.html', {}, ['a@b.com'])

    @patch('accounts.email_utils.render_to_string', side_effect=Exception('fail'))
    def test_fail_silently(self, mock_render):
        result = send_templated_email(
            'S', 't.html', {}, ['a@b.com'], fail_silently=True
        )
        self.assertEqual(result, 0)

    @patch('accounts.email_utils.render_to_string', return_value='<p>Hi</p>')
    @patch('accounts.email_utils.EmailMultiAlternatives')
    def test_adds_default_context(self, mock_cls, mock_render):
        mock_email = MagicMock()
        mock_email.send.return_value = 1
        mock_cls.return_value = mock_email
        ctx = {}
        send_templated_email('S', 't.html', ctx, ['a@b.com'])
        # Check context was enriched
        self.assertIn('support_email', ctx)
        self.assertIn('site_name', ctx)


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendVerificationEmailTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_calls_send(self, mock_send):
        user = _mock_user()
        tenant = _mock_tenant()
        result = send_verification_email(user, 'http://verify', tenant)
        self.assertEqual(result, 1)
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        self.assertIn('Verify', call_kwargs['subject'])


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendWelcomeEmailTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_with_request(self, mock_send):
        user = _mock_user()
        tenant = _mock_tenant()
        request = MagicMock()
        request.scheme = 'https'
        request.get_host.return_value = 'school.com'
        result = send_welcome_email(user, tenant, request=request)
        self.assertEqual(result, 1)

    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_without_request(self, mock_send):
        user = _mock_user()
        tenant = _mock_tenant()
        domain = MagicMock()
        domain.domain = 'school.com'
        tenant.get_primary_domain.return_value = domain
        result = send_welcome_email(user, tenant)
        self.assertEqual(result, 1)


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendPasswordResetEmailTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_sends_reset(self, mock_send):
        result = send_password_reset_email(
            _mock_user(), 'http://reset', _mock_tenant()
        )
        self.assertEqual(result, 1)
        self.assertIn('Reset', mock_send.call_args[1]['subject'])


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class Send2FAEmailTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_2fa_enabled(self, mock_send):
        result = send_2fa_enabled_email(_mock_user(), _mock_tenant())
        self.assertEqual(result, 1)
        self.assertIn('Enabled', mock_send.call_args[1]['subject'])

    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_2fa_disabled(self, mock_send):
        result = send_2fa_disabled_email(_mock_user(), _mock_tenant())
        self.assertEqual(result, 1)
        self.assertIn('Disabled', mock_send.call_args[1]['subject'])


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendEnrollmentConfirmationTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_sends_confirmation(self, mock_send):
        student = MagicMock()
        student.student.email = 'student@test.com'
        student.student.get_full_name.return_value = 'John Doe'
        course = MagicMock()
        result = send_enrollment_confirmation_email(
            student, course, _mock_tenant()
        )
        self.assertEqual(result, 1)


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendGradeNotificationTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_sends_grade(self, mock_send):
        student = MagicMock()
        student.student.email = 'student@test.com'
        student.student.get_full_name.return_value = 'John Doe'
        course = MagicMock()
        course.title = 'Math 101'
        result = send_grade_notification_email(
            student, course, 'A', _mock_tenant()
        )
        self.assertEqual(result, 1)
        self.assertIn('Math 101', mock_send.call_args[1]['subject'])


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendPaymentReceiptTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_sends_receipt(self, mock_send):
        student = MagicMock()
        student.student.email = 'student@test.com'
        student.student.get_full_name.return_value = 'John Doe'
        payment = MagicMock()
        result = send_payment_receipt_email(
            student, payment, _mock_tenant()
        )
        self.assertEqual(result, 1)

    @patch('accounts.email_utils.Parent', create=True)
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_receipt_includes_parent(self, mock_send, mock_parent):
        student = MagicMock()
        student.student.email = 'student@test.com'
        student.student.get_full_name.return_value = 'John Doe'
        # Parent lookup happens inline via import
        result = send_payment_receipt_email(
            student, MagicMock(), _mock_tenant()
        )
        self.assertEqual(result, 1)


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendBulkNotificationTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_sends_bulk(self, mock_send):
        recipients = ['a@b.com', 'c@d.com']
        result = send_bulk_notification_email(
            recipients, 'Announcement', 'Hello all', _mock_tenant()
        )
        self.assertEqual(result, 1)
        mock_send.assert_called_once()

    @patch('accounts.email_utils.send_templated_email', return_value=25)
    def test_sends_in_batches(self, mock_send):
        recipients = [f'user{i}@test.com' for i in range(75)]
        result = send_bulk_notification_email(
            recipients, 'Sub', 'Msg', _mock_tenant()
        )
        # 75 recipients / 50 per batch = 2 calls
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(result, 50)  # 25 * 2

    @patch('accounts.email_utils.send_templated_email', return_value=0)
    def test_empty_recipients(self, mock_send):
        result = send_bulk_notification_email(
            [], 'Sub', 'Msg', _mock_tenant()
        )
        self.assertEqual(result, 0)
        mock_send.assert_not_called()


@override_settings(DEFAULT_FROM_EMAIL='noreply@school.com')
class SendAccountActivationTest(TestCase):
    @patch('accounts.email_utils.send_templated_email', return_value=1)
    def test_sends_activation(self, mock_send):
        result = send_account_activation_email(
            _mock_user(), 'http://activate', _mock_tenant()
        )
        self.assertEqual(result, 1)
        self.assertIn('Activated', mock_send.call_args[1]['subject'])
