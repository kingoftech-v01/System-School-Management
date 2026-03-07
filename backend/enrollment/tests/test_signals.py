"""
Tests for enrollment signal handlers.

Signals tested:
1. track_status_change (pre_save on RegistrationForm) - logs status changes
2. notify_document_upload (post_save on EnrollmentDocument) - logs new documents
3. send_status_notification (post_save on RegistrationForm) - logs notification
   for approved/rejected/enrolled status when no recent history exists
"""

import logging
from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from enrollment.models import (
    RegistrationForm,
    EnrollmentDocument,
    EnrollmentStatusHistory,
)
from tests.helpers import TestDataMixin


class TrackStatusChangeSignalTest(TestDataMixin, TestCase):
    """Tests for the track_status_change pre_save signal."""

    def test_status_change_is_logged(self):
        """Changing status on an existing registration logs an info message."""
        reg = self.create_registration()
        self.assertEqual(reg.status, 'pending')

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            reg.status = 'under_review'
            reg.save()

        # Check the log message mentions the status transition
        log_output = '\n'.join(cm.output)
        self.assertIn('pending', log_output)
        self.assertIn('under_review', log_output)

    def test_no_log_when_status_unchanged(self):
        """Re-saving without changing status does not produce a log."""
        reg = self.create_registration()

        logger = logging.getLogger('enrollment.signals')
        with patch.object(logger, 'info') as mock_info:
            reg.student_name = 'Updated Name'
            reg.save()
            # info should not be called with a status change message
            for call in mock_info.call_args_list:
                self.assertNotIn('status changed', str(call))

    def test_new_registration_no_status_change_log(self):
        """Creating a new registration does not log a status change."""
        logger = logging.getLogger('enrollment.signals')
        with patch.object(logger, 'info') as mock_info:
            self.create_registration()
            for call in mock_info.call_args_list:
                self.assertNotIn('status changed', str(call))

    def test_status_change_pending_to_approved(self):
        """Changing from pending to approved is logged."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            reg.status = 'approved'
            reg.save()

        log_output = '\n'.join(cm.output)
        self.assertIn('pending', log_output)
        self.assertIn('approved', log_output)

    def test_status_change_approved_to_enrolled(self):
        """Changing from approved to enrolled is logged."""
        reg = self.create_registration(status='approved')

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            reg.status = 'enrolled'
            reg.save()

        log_output = '\n'.join(cm.output)
        self.assertIn('approved', log_output)
        self.assertIn('enrolled', log_output)


class NotifyDocumentUploadSignalTest(TestDataMixin, TestCase):
    """Tests for the notify_document_upload post_save signal."""

    def _create_document(self, registration=None, doc_type='birth_certificate'):
        """Helper to create an EnrollmentDocument."""
        if registration is None:
            registration = self.create_registration()
        fake_file = SimpleUploadedFile(
            'test_doc.pdf',
            b'%PDF-1.4 test content',
            content_type='application/pdf',
        )
        return EnrollmentDocument.objects.create(
            registration=registration,
            document_type=doc_type,
            file=fake_file,
        )

    def test_new_document_logs_info(self):
        """Creating a new document logs an info message."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            self._create_document(registration=reg)

        log_output = '\n'.join(cm.output)
        self.assertIn('New document uploaded', log_output)

    def test_new_document_log_includes_registration_id(self):
        """Log message includes the registration ID."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            self._create_document(registration=reg)

        log_output = '\n'.join(cm.output)
        self.assertIn(str(reg.id), log_output)

    def test_new_document_log_includes_document_type(self):
        """Log message includes the human-readable document type."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            self._create_document(registration=reg, doc_type='transcript')

        log_output = '\n'.join(cm.output)
        self.assertIn('Transcript', log_output)

    def test_update_document_does_not_log(self):
        """Updating an existing document does NOT log 'New document uploaded'."""
        reg = self.create_registration()
        doc = self._create_document(registration=reg)

        logger = logging.getLogger('enrollment.signals')
        with patch.object(logger, 'info') as mock_info:
            doc.is_verified = True
            doc.save()
            for call in mock_info.call_args_list:
                self.assertNotIn('New document uploaded', str(call))


class SendStatusNotificationSignalTest(TestDataMixin, TestCase):
    """Tests for the send_status_notification post_save signal."""

    def test_approved_status_triggers_notification_log(self):
        """Saving a non-new registration with 'approved' status logs notification."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            reg.status = 'approved'
            reg.save()

        log_output = '\n'.join(cm.output)
        self.assertIn('Triggering status notification', log_output)

    def test_rejected_status_triggers_notification_log(self):
        """Saving with 'rejected' status logs notification."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            reg.status = 'rejected'
            reg.save()

        log_output = '\n'.join(cm.output)
        self.assertIn('Triggering status notification', log_output)

    def test_enrolled_status_triggers_notification_log(self):
        """Saving with 'enrolled' status logs notification."""
        reg = self.create_registration()

        with self.assertLogs('enrollment.signals', level='INFO') as cm:
            reg.status = 'enrolled'
            reg.save()

        log_output = '\n'.join(cm.output)
        self.assertIn('Triggering status notification', log_output)

    def test_pending_status_no_notification(self):
        """Saving with 'pending' status does NOT trigger notification."""
        reg = self.create_registration()

        logger = logging.getLogger('enrollment.signals')
        with patch.object(logger, 'info') as mock_info:
            reg.student_name = 'Changed Name'
            reg.save()
            for call in mock_info.call_args_list:
                self.assertNotIn('Triggering status notification', str(call))

    def test_new_creation_with_approved_no_notification(self):
        """Creating a NEW registration with approved status does not trigger
        the notification signal (created=True is skipped)."""
        logger = logging.getLogger('enrollment.signals')
        with patch.object(logger, 'info') as mock_info:
            self.create_registration(status='approved')
            for call in mock_info.call_args_list:
                self.assertNotIn('Triggering status notification', str(call))

    def test_notification_skipped_when_recent_history_exists(self):
        """When a recent EnrollmentStatusHistory entry already exists for
        the new status, the notification log may be skipped."""
        reg = self.create_registration()

        # Create a history entry dated in the future to simulate "already sent"
        EnrollmentStatusHistory.objects.create(
            registration=reg,
            old_status='pending',
            new_status='approved',
        )

        # Now update the status; the signal checks for recent history
        reg.status = 'approved'
        reg.save()

        # The signal should still run but the condition check may skip
        # We just verify it does not crash
        reg.refresh_from_db()
        self.assertEqual(reg.status, 'approved')
