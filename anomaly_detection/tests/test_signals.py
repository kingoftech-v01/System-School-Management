"""
Tests for anomaly_detection signal handlers.

Signals tested:
1. check_grade_anomalies (post_save on result.TakenCourse) - runs
   GradeJumpDetector and GradeAbnormallyHighDetector when total != 0
2. check_grade_history_anomalies (post_save on result.GradeHistory) - runs
   GradeUnauthorizedChangeDetector on new GradeHistory entries
3. check_payment_anomalies (post_save on payments.Payment) - runs
   PaymentAmountMismatchDetector always, DoublePaymentDetector on create
4. check_payment_status_reversal (pre_save on payments.Payment) - runs
   PaymentStatusReversalDetector on existing payments
5. check_invoice_anomalies (post_save on payments.Invoice) - runs
   InvoiceFeeStructureMismatchDetector on new invoices
6. check_enrollment_anomalies (post_save on enrollment.RegistrationForm) -
   runs DuplicateEnrollmentDetector on create, InvalidStatusTransitionDetector
   and UnauthorizedApprovalDetector on update

Note: The signal handlers use lazy (local) imports inside each function body,
so we must patch the detector classes at their *source* module
(anomaly_detection.detectors.<module>), NOT at anomaly_detection.signals.
"""

from decimal import Decimal
from unittest.mock import patch, MagicMock, call

from django.test import TestCase

from tests.helpers import TestDataMixin


class CheckGradeAnomaliesSignalTest(TestDataMixin, TestCase):
    """Tests for the check_grade_anomalies signal on TakenCourse save."""

    def _create_taken_course(self, **scores):
        """Helper to create a TakenCourse for testing."""
        from result.models import TakenCourse
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        defaults = {
            'student': student,
            'course': course,
            'assignment': Decimal('80'),
            'mid_exam': Decimal('75'),
            'quiz': Decimal('85'),
            'attendance': Decimal('90'),
            'final_exam': Decimal('70'),
        }
        defaults.update(scores)
        return TakenCourse.objects.create(**defaults)

    @patch('anomaly_detection.detectors.grade.GradeAbnormallyHighDetector')
    @patch('anomaly_detection.detectors.grade.GradeJumpDetector')
    def test_grade_detectors_called_on_save(
        self, mock_jump_cls, mock_high_cls
    ):
        """Both GradeJumpDetector and GradeAbnormallyHighDetector are called
        when a TakenCourse is saved with total != 0."""
        mock_jump_instance = MagicMock()
        mock_jump_cls.return_value = mock_jump_instance
        mock_high_instance = MagicMock()
        mock_high_cls.return_value = mock_high_instance

        tc = self._create_taken_course()

        mock_jump_instance.check.assert_called_once_with(tc)
        mock_high_instance.check.assert_called_once_with(tc)

    @patch('anomaly_detection.detectors.grade.GradeAbnormallyHighDetector')
    @patch('anomaly_detection.detectors.grade.GradeJumpDetector')
    def test_grade_detectors_skipped_when_total_zero(
        self, mock_jump_cls, mock_high_cls
    ):
        """Grade detectors are NOT called when total == 0."""
        self._create_taken_course(
            assignment=Decimal('0'),
            mid_exam=Decimal('0'),
            quiz=Decimal('0'),
            attendance=Decimal('0'),
            final_exam=Decimal('0'),
        )

        mock_jump_cls.assert_not_called()
        mock_high_cls.assert_not_called()

    @patch('anomaly_detection.detectors.grade.GradeAbnormallyHighDetector')
    @patch('anomaly_detection.detectors.grade.GradeJumpDetector')
    def test_exception_in_detector_does_not_crash_save(
        self, mock_jump_cls, mock_high_cls
    ):
        """An exception raised inside a detector does not prevent the
        TakenCourse from being saved."""
        mock_jump_instance = MagicMock()
        mock_jump_instance.check.side_effect = RuntimeError('Detector failed')
        mock_jump_cls.return_value = mock_jump_instance

        # Should not raise
        tc = self._create_taken_course()
        self.assertIsNotNone(tc.pk)


class CheckGradeHistoryAnomaliesSignalTest(TestDataMixin, TestCase):
    """Tests for the check_grade_history_anomalies signal on GradeHistory."""

    def _create_grade_history(self):
        """Helper to create a GradeHistory entry."""
        from result.models import TakenCourse, GradeHistory
        user = self.create_student_user()
        student = self.create_student_profile(user)
        course = self.create_course()
        tc = TakenCourse.objects.create(
            student=student, course=course,
            assignment=Decimal('80'), mid_exam=Decimal('75'),
            quiz=Decimal('85'), attendance=Decimal('90'),
            final_exam=Decimal('70'),
        )
        admin = self.create_admin_user()
        return GradeHistory.objects.create(
            taken_course=tc,
            old_assignment=Decimal('80'), old_mid_exam=Decimal('75'),
            old_quiz=Decimal('85'), old_attendance=Decimal('90'),
            old_final_exam=Decimal('70'), old_total=tc.total,
            old_grade='A',
            new_assignment=Decimal('90'), new_mid_exam=Decimal('85'),
            new_quiz=Decimal('95'), new_attendance=Decimal('95'),
            new_final_exam=Decimal('80'), new_total=Decimal('89.00'),
            new_grade='A',
            changed_by=admin,
            change_reason='Correction',
        )

    @patch('anomaly_detection.detectors.grade.GradeUnauthorizedChangeDetector')
    def test_unauthorized_change_detector_called_on_create(
        self, mock_detector_cls
    ):
        """GradeUnauthorizedChangeDetector is called when a new
        GradeHistory is created."""
        mock_instance = MagicMock()
        mock_detector_cls.return_value = mock_instance

        gh = self._create_grade_history()

        mock_instance.check.assert_called_once_with(gh)

    @patch('anomaly_detection.detectors.grade.GradeUnauthorizedChangeDetector')
    def test_exception_in_history_detector_does_not_crash(
        self, mock_detector_cls
    ):
        """An exception in the detector does not prevent GradeHistory save."""
        mock_instance = MagicMock()
        mock_instance.check.side_effect = RuntimeError('Detector error')
        mock_detector_cls.return_value = mock_instance

        gh = self._create_grade_history()
        self.assertIsNotNone(gh.pk)


class CheckPaymentAnomaliesSignalTest(TestDataMixin, TestCase):
    """Tests for payment anomaly detection signals."""

    @patch('anomaly_detection.detectors.payment.DoublePaymentDetector')
    @patch('anomaly_detection.detectors.payment.PaymentAmountMismatchDetector')
    def test_payment_detectors_called_on_create(
        self, mock_mismatch_cls, mock_double_cls
    ):
        """Both PaymentAmountMismatchDetector and DoublePaymentDetector
        are called when a Payment is created."""
        mock_mismatch = MagicMock()
        mock_mismatch_cls.return_value = mock_mismatch
        mock_double = MagicMock()
        mock_double_cls.return_value = mock_double

        payment = self.create_payment()

        mock_mismatch.check.assert_called_once_with(payment)
        mock_double.check.assert_called_once_with(payment)

    @patch('anomaly_detection.detectors.payment.DoublePaymentDetector')
    @patch('anomaly_detection.detectors.payment.PaymentAmountMismatchDetector')
    def test_double_payment_not_called_on_update(
        self, mock_mismatch_cls, mock_double_cls
    ):
        """DoublePaymentDetector is NOT called when a Payment is updated
        (only on creation)."""
        mock_mismatch = MagicMock()
        mock_mismatch_cls.return_value = mock_mismatch
        mock_double = MagicMock()
        mock_double_cls.return_value = mock_double

        payment = self.create_payment()
        mock_double.reset_mock()
        mock_mismatch.reset_mock()

        payment.amount = Decimal('600.00')
        payment.save()

        # Mismatch detector still called on update
        mock_mismatch.check.assert_called_once_with(payment)
        # Double payment NOT called on update
        mock_double.check.assert_not_called()

    @patch('anomaly_detection.detectors.payment.DoublePaymentDetector')
    @patch('anomaly_detection.detectors.payment.PaymentAmountMismatchDetector')
    def test_exception_in_payment_detector_does_not_crash(
        self, mock_mismatch_cls, mock_double_cls
    ):
        """An exception in payment detector does not prevent Payment save."""
        mock_mismatch = MagicMock()
        mock_mismatch.check.side_effect = RuntimeError('Detector error')
        mock_mismatch_cls.return_value = mock_mismatch
        mock_double = MagicMock()
        mock_double_cls.return_value = mock_double

        payment = self.create_payment()
        self.assertIsNotNone(payment.pk)


class CheckPaymentStatusReversalSignalTest(TestDataMixin, TestCase):
    """Tests for the check_payment_status_reversal pre_save signal."""

    @patch('anomaly_detection.detectors.payment.PaymentStatusReversalDetector')
    def test_status_reversal_detector_called_on_existing_payment(
        self, mock_detector_cls
    ):
        """PaymentStatusReversalDetector is called when saving an existing
        payment (has pk)."""
        mock_instance = MagicMock()
        mock_detector_cls.return_value = mock_instance

        payment = self.create_payment()
        mock_instance.reset_mock()

        payment.status = 'completed'
        payment.save()

        mock_instance.check.assert_called_once_with(payment)

    @patch('anomaly_detection.detectors.payment.PaymentStatusReversalDetector')
    def test_status_reversal_detector_skipped_on_new_payment(
        self, mock_detector_cls
    ):
        """PaymentStatusReversalDetector is NOT called on brand-new payments
        (instance.pk is None)."""
        mock_instance = MagicMock()
        mock_detector_cls.return_value = mock_instance

        # create_payment creates a new payment, but the pre_save fires
        # before the pk is assigned; verify the detector was not called
        # during the initial pre_save (pk is None at that point)
        self.create_payment()
        mock_instance.check.assert_not_called()


class CheckInvoiceAnomaliesSignalTest(TestDataMixin, TestCase):
    """Tests for the check_invoice_anomalies signal on Invoice creation."""

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector')
    def test_invoice_detector_called_on_create(self, mock_detector_cls):
        """InvoiceFeeStructureMismatchDetector is called when a new
        Invoice is created."""
        mock_instance = MagicMock()
        mock_detector_cls.return_value = mock_instance

        invoice = self.create_invoice()

        mock_instance.check.assert_called_once_with(invoice)

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector')
    def test_invoice_detector_not_called_on_update(self, mock_detector_cls):
        """InvoiceFeeStructureMismatchDetector is NOT called when an
        existing Invoice is updated."""
        mock_instance = MagicMock()
        mock_detector_cls.return_value = mock_instance

        invoice = self.create_invoice()
        mock_instance.reset_mock()

        invoice.total = Decimal('2000.00')
        invoice.save()

        mock_instance.check.assert_not_called()

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector')
    def test_exception_in_invoice_detector_does_not_crash(
        self, mock_detector_cls
    ):
        """An exception in InvoiceFeeStructureMismatchDetector does not
        prevent the Invoice from being saved."""
        mock_instance = MagicMock()
        mock_instance.check.side_effect = RuntimeError('Detector error')
        mock_detector_cls.return_value = mock_instance

        invoice = self.create_invoice()
        self.assertIsNotNone(invoice.pk)


class CheckEnrollmentAnomaliesSignalTest(TestDataMixin, TestCase):
    """Tests for the check_enrollment_anomalies signal on RegistrationForm."""

    @patch('anomaly_detection.detectors.enrollment.DuplicateEnrollmentDetector')
    def test_duplicate_detector_called_on_create(self, mock_detector_cls):
        """DuplicateEnrollmentDetector is called when a new
        RegistrationForm is created."""
        mock_instance = MagicMock()
        mock_detector_cls.return_value = mock_instance

        reg = self.create_registration()

        mock_instance.check.assert_called_once_with(reg)

    @patch('anomaly_detection.detectors.enrollment.UnauthorizedApprovalDetector')
    @patch('anomaly_detection.detectors.enrollment.InvalidStatusTransitionDetector')
    @patch('anomaly_detection.detectors.enrollment.DuplicateEnrollmentDetector')
    def test_update_detectors_called_on_update(
        self, mock_dup_cls, mock_invalid_cls, mock_unauth_cls
    ):
        """InvalidStatusTransitionDetector and UnauthorizedApprovalDetector
        are called when an existing RegistrationForm is updated."""
        mock_dup = MagicMock()
        mock_dup_cls.return_value = mock_dup
        mock_invalid = MagicMock()
        mock_invalid_cls.return_value = mock_invalid
        mock_unauth = MagicMock()
        mock_unauth_cls.return_value = mock_unauth

        reg = self.create_registration()
        mock_dup.reset_mock()
        mock_invalid.reset_mock()
        mock_unauth.reset_mock()

        reg.status = 'approved'
        reg.save()

        # Duplicate NOT called on update
        mock_dup.check.assert_not_called()
        # Both update detectors called
        mock_invalid.check.assert_called_once_with(reg)
        mock_unauth.check.assert_called_once_with(reg)

    @patch('anomaly_detection.detectors.enrollment.DuplicateEnrollmentDetector')
    def test_exception_in_enrollment_detector_does_not_crash(
        self, mock_detector_cls
    ):
        """An exception in DuplicateEnrollmentDetector does not prevent
        the RegistrationForm from being saved."""
        mock_instance = MagicMock()
        mock_instance.check.side_effect = RuntimeError('Detector error')
        mock_detector_cls.return_value = mock_instance

        reg = self.create_registration()
        self.assertIsNotNone(reg.pk)
