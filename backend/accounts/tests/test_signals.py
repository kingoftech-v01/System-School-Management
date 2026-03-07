"""
Tests for accounts signal handlers.

The post_save_account_receiver signal fires on User creation and:
- Generates student credentials (username + password) for students
- Generates lecturer credentials (username + password) for lecturers
- Sends a new-account email with the generated credentials
- Does NOT fire on updates (only on created=True)
"""

from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from tests.helpers import TestDataMixin

User = get_user_model()


class PostSaveAccountReceiverTest(TestDataMixin, TestCase):
    """Tests for the post_save_account_receiver signal."""

    # ------------------------------------------------------------------
    # Student creation
    # ------------------------------------------------------------------

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials',
           return_value=('STU-2025-1', 'randompass123'))
    def test_student_creation_generates_credentials(
        self, mock_gen_creds, mock_send_email
    ):
        """Creating a student user triggers credential generation."""
        user = User(
            first_name='Alice',
            last_name='Student',
            email='alice@example.com',
            is_student=True,
            role='student',
        )
        user.set_password('temp')
        user.save()

        mock_gen_creds.assert_called_once()

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials',
           return_value=('STU-2025-2', 'randompass456'))
    def test_student_creation_sets_username(
        self, mock_gen_creds, mock_send_email
    ):
        """Generated student username is saved to the user instance."""
        user = User(
            first_name='Bob',
            last_name='Student',
            email='bob@example.com',
            is_student=True,
            role='student',
        )
        user.set_password('temp')
        user.save()

        user.refresh_from_db()
        self.assertEqual(user.username, 'STU-2025-2')

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials',
           return_value=('STU-2025-3', 'pass789'))
    def test_student_creation_sends_email(
        self, mock_gen_creds, mock_send_email
    ):
        """Creating a student user sends a new-account email."""
        user = User(
            first_name='Carol',
            last_name='Student',
            email='carol@example.com',
            is_student=True,
            role='student',
        )
        user.set_password('temp')
        user.save()

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        # First arg is the user instance, second is the password
        self.assertEqual(call_args[0][1], 'pass789')

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials',
           return_value=('STU-2025-4', 'pwd'))
    def test_student_creation_sets_password(
        self, mock_gen_creds, mock_send_email
    ):
        """Generated password is hashed and saved to the user."""
        user = User(
            first_name='Dave',
            last_name='Student',
            email='dave@example.com',
            is_student=True,
            role='student',
        )
        user.set_password('temp')
        user.save()

        user.refresh_from_db()
        # Password should now be the generated one, not 'temp'
        self.assertTrue(user.check_password('pwd'))

    # ------------------------------------------------------------------
    # Lecturer creation
    # ------------------------------------------------------------------

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_lecturer_credentials',
           return_value=('LEC-2025-1', 'lecpass123'))
    def test_lecturer_creation_generates_credentials(
        self, mock_gen_creds, mock_send_email
    ):
        """Creating a lecturer user triggers lecturer credential generation."""
        user = User(
            first_name='Eve',
            last_name='Lecturer',
            email='eve@example.com',
            is_lecturer=True,
            role='professor',
        )
        user.set_password('temp')
        user.save()

        mock_gen_creds.assert_called_once()

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_lecturer_credentials',
           return_value=('LEC-2025-2', 'lecpass456'))
    def test_lecturer_creation_sets_username(
        self, mock_gen_creds, mock_send_email
    ):
        """Generated lecturer username is saved to the user instance."""
        user = User(
            first_name='Frank',
            last_name='Lecturer',
            email='frank@example.com',
            is_lecturer=True,
            role='professor',
        )
        user.set_password('temp')
        user.save()

        user.refresh_from_db()
        self.assertEqual(user.username, 'LEC-2025-2')

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_lecturer_credentials',
           return_value=('LEC-2025-3', 'lecpass789'))
    def test_lecturer_creation_sends_email(
        self, mock_gen_creds, mock_send_email
    ):
        """Creating a lecturer user sends a new-account email."""
        user = User(
            first_name='Grace',
            last_name='Lecturer',
            email='grace@example.com',
            is_lecturer=True,
            role='professor',
        )
        user.set_password('temp')
        user.save()

        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        self.assertEqual(call_args[0][1], 'lecpass789')

    # ------------------------------------------------------------------
    # Signal does NOT fire on update
    # ------------------------------------------------------------------

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials',
           return_value=('STU-2025-UP', 'uppass'))
    def test_signal_does_not_fire_on_update(
        self, mock_gen_creds, mock_send_email
    ):
        """Updating an existing user does NOT regenerate credentials."""
        user = User(
            first_name='Hank',
            last_name='Student',
            email='hank@example.com',
            is_student=True,
            role='student',
        )
        user.set_password('temp')
        user.save()

        # Reset mocks after initial creation
        mock_gen_creds.reset_mock()
        mock_send_email.reset_mock()

        # Update the user
        user.first_name = 'Hank Updated'
        user.save()

        mock_gen_creds.assert_not_called()
        mock_send_email.assert_not_called()

    # ------------------------------------------------------------------
    # Non-student/non-lecturer users
    # ------------------------------------------------------------------

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials')
    @patch('accounts.signals.generate_lecturer_credentials')
    def test_non_student_non_lecturer_no_credentials(
        self, mock_lec_creds, mock_stu_creds, mock_send_email
    ):
        """Creating a non-student, non-lecturer user generates no credentials."""
        user = User(
            first_name='Ivan',
            last_name='Admin',
            email='ivan@example.com',
            is_student=False,
            is_lecturer=False,
            role='direction',
        )
        user.set_password('temp')
        user.save()

        mock_stu_creds.assert_not_called()
        mock_lec_creds.assert_not_called()
        mock_send_email.assert_not_called()

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials')
    @patch('accounts.signals.generate_lecturer_credentials')
    def test_parent_creation_no_credentials(
        self, mock_lec_creds, mock_stu_creds, mock_send_email
    ):
        """Creating a parent user generates no credentials."""
        user = User(
            first_name='Jane',
            last_name='Parent',
            email='jane@example.com',
            is_parent=True,
            role='parent',
        )
        user.set_password('temp')
        user.save()

        mock_stu_creds.assert_not_called()
        mock_lec_creds.assert_not_called()
        mock_send_email.assert_not_called()

    # ------------------------------------------------------------------
    # Email args verification
    # ------------------------------------------------------------------

    @patch('accounts.signals.send_new_account_email')
    @patch('accounts.signals.generate_student_credentials',
           return_value=('STU-2025-X', 'xpass'))
    def test_email_receives_user_instance_and_password(
        self, mock_gen_creds, mock_send_email
    ):
        """send_new_account_email is called with (user_instance, password)."""
        user = User(
            first_name='Kyle',
            last_name='Student',
            email='kyle@example.com',
            is_student=True,
            role='student',
        )
        user.set_password('temp')
        user.save()

        mock_send_email.assert_called_once()
        user_arg, password_arg = mock_send_email.call_args[0]
        self.assertEqual(user_arg.pk, user.pk)
        self.assertEqual(password_arg, 'xpass')
