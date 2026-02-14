"""Tests for anomaly_detection detectors."""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase

from anomaly_detection.detectors.base import BaseDetector
from anomaly_detection.detectors.grade import (
    GradeJumpDetector,
    GradeAbnormallyHighDetector,
    GradeUnauthorizedChangeDetector,
)
from anomaly_detection.detectors.payment import (
    PaymentAmountMismatchDetector,
    DoublePaymentDetector,
    PaymentStatusReversalDetector,
    InvoiceFeeStructureMismatchDetector,
)
from anomaly_detection.detectors.enrollment import (
    DuplicateEnrollmentDetector,
    InvalidStatusTransitionDetector,
    UnauthorizedApprovalDetector,
)
from anomaly_detection.models import AnomalyType, AnomalyAlert, AnomalyThreshold
from tests.helpers import TestDataMixin


# ---------------------------------------------------------------------------
# BaseDetector tests
# ---------------------------------------------------------------------------

class BaseDetectorTest(TestDataMixin, TestCase):
    """Tests for the BaseDetector abstract class."""

    def test_check_raises_not_implemented(self):
        """BaseDetector.check() raises NotImplementedError."""
        detector = BaseDetector()
        with self.assertRaises(NotImplementedError):
            detector.check(None)

    def test_get_anomaly_type_returns_none_when_not_found(self):
        """get_anomaly_type returns None if no matching AnomalyType exists."""
        detector = BaseDetector()
        detector.anomaly_code = 'nonexistent_code'
        self.assertIsNone(detector.get_anomaly_type())

    def test_get_anomaly_type_returns_enabled_type(self):
        """get_anomaly_type returns the AnomalyType when it exists and is enabled."""
        at = self.create_anomaly_type(code='base_test', domain='grade', is_enabled=True)
        detector = BaseDetector()
        detector.anomaly_code = 'base_test'
        result = detector.get_anomaly_type()
        self.assertEqual(result.pk, at.pk)

    def test_get_anomaly_type_returns_none_when_disabled(self):
        """get_anomaly_type returns None if AnomalyType is disabled."""
        self.create_anomaly_type(code='disabled_test', domain='grade', is_enabled=False)
        detector = BaseDetector()
        detector.anomaly_code = 'disabled_test'
        self.assertIsNone(detector.get_anomaly_type())

    def test_get_threshold_returns_default_when_no_type(self):
        """get_threshold falls back to default if anomaly type does not exist."""
        detector = BaseDetector()
        detector.anomaly_code = 'missing_type'
        result = detector.get_threshold('some_key', 5.0)
        self.assertEqual(result, Decimal('5.0'))

    def test_get_threshold_returns_configured_value(self):
        """get_threshold returns the configured threshold value."""
        at = self.create_anomaly_type(code='thresh_det', domain='grade')
        AnomalyThreshold.objects.create(
            anomaly_type=at, key='my_threshold', value=Decimal('3.5'),
        )
        detector = BaseDetector()
        detector.anomaly_code = 'thresh_det'
        result = detector.get_threshold('my_threshold', 2.0)
        self.assertEqual(result, Decimal('3.5'))

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_create_alert_returns_alert(self, mock_notify):
        """create_alert creates and returns an AnomalyAlert."""
        at = self.create_anomaly_type(code='create_alert_test', domain='grade')
        detector = BaseDetector()
        detector.anomaly_code = 'create_alert_test'
        alert = detector.create_alert(
            title='Test Title',
            details={'key': 'value'},
        )
        self.assertIsNotNone(alert)
        self.assertEqual(alert.title, 'Test Title')
        self.assertEqual(alert.anomaly_type, at)

    def test_create_alert_returns_none_when_type_missing(self):
        """create_alert returns None when anomaly type does not exist."""
        detector = BaseDetector()
        detector.anomaly_code = 'missing_anomaly_type'
        result = detector.create_alert(title='Test', details={})
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# GradeJumpDetector tests
# ---------------------------------------------------------------------------

class GradeJumpDetectorTest(TestDataMixin, TestCase):
    """Tests for GradeJumpDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='grade_sudden_jump', domain='grade',
        )
        self.detector = GradeJumpDetector()

    def test_anomaly_code(self):
        """Detector has the correct anomaly_code."""
        self.assertEqual(self.detector.anomaly_code, 'grade_sudden_jump')

    @patch('anomaly_detection.detectors.grade.GradeJumpDetector.create_alert')
    def test_zero_total_skips_check(self, mock_alert):
        """Grades with total=0 are skipped."""
        taken_course = MagicMock()
        taken_course.total = Decimal('0.00')
        self.detector.check(taken_course)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_not_enough_data_skips(self, mock_notify):
        """When there is not enough historical data, no alert is created."""
        program = self.create_program()
        course = self.create_course(program=program)
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)

        from result.models import TakenCourse
        # Create only 1 past grade (need >= 3 for personal stats)
        tc1 = TakenCourse.objects.create(student=student_profile, course=course)
        TakenCourse.objects.filter(pk=tc1.pk).update(total=Decimal('50.00'))

        # Create the new grade (only 1 class grade excluding self, need >= 2 for class stats)
        new_tc = TakenCourse.objects.create(student=student_profile, course=course)
        TakenCourse.objects.filter(pk=new_tc.pk).update(total=Decimal('85.00'))
        new_tc.refresh_from_db()

        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(new_tc)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_creates_alert_for_large_jump(self, mock_notify):
        """When score exceeds threshold, an alert is created."""
        program = self.create_program()
        course = self.create_course(program=program)
        student_user = self.create_student_user()
        student_profile = self.create_student_profile(user=student_user, program=program)

        from result.models import TakenCourse
        # Create past grades (>= 3 for personal stats)
        for score in [50, 55, 52, 48]:
            tc = TakenCourse.objects.create(student=student_profile, course=course)
            TakenCourse.objects.filter(pk=tc.pk).update(total=Decimal(str(score)))

        # Create a new grade with a large jump
        new_tc = TakenCourse.objects.create(student=student_profile, course=course)
        TakenCourse.objects.filter(pk=new_tc.pk).update(total=Decimal('95.00'))
        new_tc.refresh_from_db()

        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(new_tc)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertGreater(alert_count_after, alert_count_before)
        latest = AnomalyAlert.objects.filter(anomaly_type=self.at).order_by('-pk').first()
        self.assertIn('grade jump', latest.title.lower())


# ---------------------------------------------------------------------------
# GradeAbnormallyHighDetector tests
# ---------------------------------------------------------------------------

class GradeAbnormallyHighDetectorTest(TestDataMixin, TestCase):
    """Tests for GradeAbnormallyHighDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='grade_abnormally_high', domain='grade',
        )
        self.detector = GradeAbnormallyHighDetector()

    def test_anomaly_code(self):
        """Detector has the correct anomaly_code."""
        self.assertEqual(self.detector.anomaly_code, 'grade_abnormally_high')

    @patch('anomaly_detection.detectors.grade.GradeAbnormallyHighDetector.create_alert')
    def test_zero_total_skips(self, mock_alert):
        """Grades with total=0 are skipped."""
        taken_course = MagicMock()
        taken_course.total = Decimal('0.00')
        self.detector.check(taken_course)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_creates_alert_for_abnormally_high_grade(self, mock_notify):
        """When a grade is significantly above the class mean, an alert is created."""
        program = self.create_program()
        course = self.create_course(program=program)

        from result.models import TakenCourse

        # Create class grades (need >= 3)
        for score in [50, 55, 52, 48, 53]:
            student_user = self.create_student_user()
            sp = self.create_student_profile(user=student_user, program=program)
            tc = TakenCourse.objects.create(student=sp, course=course)
            TakenCourse.objects.filter(pk=tc.pk).update(total=Decimal(str(score)))

        # Create an abnormally high grade
        outlier_user = self.create_student_user()
        outlier_profile = self.create_student_profile(user=outlier_user, program=program)
        new_tc = TakenCourse.objects.create(student=outlier_profile, course=course)
        TakenCourse.objects.filter(pk=new_tc.pk).update(total=Decimal('98.00'))
        new_tc.refresh_from_db()

        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(new_tc)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertGreater(alert_count_after, alert_count_before)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_no_alert_for_normal_grade(self, mock_notify):
        """Grades close to the class mean do not trigger an alert."""
        program = self.create_program()
        course = self.create_course(program=program)

        from result.models import TakenCourse

        for score in [50, 55, 52, 48]:
            su = self.create_student_user()
            sp = self.create_student_profile(user=su, program=program)
            tc = TakenCourse.objects.create(student=sp, course=course)
            TakenCourse.objects.filter(pk=tc.pk).update(total=Decimal(str(score)))

        normal_user = self.create_student_user()
        normal_profile = self.create_student_profile(user=normal_user, program=program)
        new_tc = TakenCourse.objects.create(student=normal_profile, course=course)
        TakenCourse.objects.filter(pk=new_tc.pk).update(total=Decimal('53.00'))
        new_tc.refresh_from_db()

        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(new_tc)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)


# ---------------------------------------------------------------------------
# GradeUnauthorizedChangeDetector tests
# ---------------------------------------------------------------------------

class GradeUnauthorizedChangeDetectorTest(TestDataMixin, TestCase):
    """Tests for GradeUnauthorizedChangeDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='grade_unauthorized_change', domain='grade',
        )
        self.detector = GradeUnauthorizedChangeDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'grade_unauthorized_change')

    @patch('anomaly_detection.detectors.grade.GradeUnauthorizedChangeDetector.create_alert')
    def test_no_changed_by_skips(self, mock_alert):
        """If changed_by is None, no alert is created."""
        grade_history = MagicMock()
        grade_history.changed_by = None
        self.detector.check(grade_history)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_superuser_is_not_flagged_for_authorization(self, mock_notify):
        """Superusers are never flagged for unauthorized changes."""
        program = self.create_program()
        course = self.create_course(program=program)
        admin = self.create_admin_user()
        student_user = self.create_student_user()
        sp = self.create_student_profile(user=student_user, program=program)

        from result.models import TakenCourse, GradeHistory
        tc = TakenCourse.objects.create(student=sp, course=course)
        gh = GradeHistory.objects.create(
            taken_course=tc, changed_by=admin,
            old_assignment=0, old_mid_exam=0, old_quiz=0, old_attendance=0,
            old_final_exam=0, old_total=0, old_grade='',
            new_assignment=20, new_mid_exam=20, new_quiz=10, new_attendance=10,
            new_final_exam=20, new_total=80, new_grade='A',
        )
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(gh)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_unallocated_professor_triggers_alert(self, mock_notify):
        """A professor not allocated to the course triggers an unauthorized change alert."""
        program = self.create_program()
        course = self.create_course(program=program)
        unalloc_prof = self.create_professor_user()
        student_user = self.create_student_user()
        sp = self.create_student_profile(user=student_user, program=program)

        from result.models import TakenCourse, GradeHistory
        tc = TakenCourse.objects.create(student=sp, course=course)
        gh = GradeHistory.objects.create(
            taken_course=tc, changed_by=unalloc_prof,
            old_assignment=0, old_mid_exam=0, old_quiz=0, old_attendance=0,
            old_final_exam=0, old_total=0, old_grade='',
            new_assignment=20, new_mid_exam=15, new_quiz=10, new_attendance=10,
            new_final_exam=20, new_total=75, new_grade='B',
        )
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(gh)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertGreater(alert_count_after, alert_count_before)
        latest = AnomalyAlert.objects.filter(anomaly_type=self.at).order_by('-pk').first()
        self.assertIn('Unauthorized', latest.title)


# ---------------------------------------------------------------------------
# PaymentAmountMismatchDetector tests
# ---------------------------------------------------------------------------

class PaymentAmountMismatchDetectorTest(TestDataMixin, TestCase):
    """Tests for PaymentAmountMismatchDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='payment_amount_mismatch', domain='payment',
        )
        self.detector = PaymentAmountMismatchDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'payment_amount_mismatch')

    @patch('anomaly_detection.detectors.payment.PaymentAmountMismatchDetector.create_alert')
    def test_no_invoice_skips(self, mock_alert):
        """Payments without an invoice are skipped."""
        payment = MagicMock()
        payment.invoice = None
        self.detector.check(payment)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.detectors.payment.PaymentAmountMismatchDetector.create_alert')
    def test_matching_amounts_no_alert(self, mock_alert):
        """When payment amount matches invoice amount, no alert is created."""
        payment = MagicMock()
        payment.amount = Decimal('500.00')
        payment.invoice.amount = Decimal('500.00')
        self.detector.check(payment)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.detectors.payment.PaymentAmountMismatchDetector.create_alert')
    def test_mismatched_amounts_triggers_alert(self, mock_alert):
        """When payment amount differs from invoice amount, alert is created."""
        payment = MagicMock()
        payment.amount = Decimal('300.00')
        payment.invoice.amount = Decimal('500.00')
        payment.invoice.invoice_code = 'INV-001'
        payment.pk = 1
        payment.transaction_id = 'TXN-001'
        payment.payment_gateway = 'stripe'
        payment.invoice.user = MagicMock()
        self.detector.check(payment)
        mock_alert.assert_called_once()


# ---------------------------------------------------------------------------
# DoublePaymentDetector tests
# ---------------------------------------------------------------------------

class DoublePaymentDetectorTest(TestDataMixin, TestCase):
    """Tests for DoublePaymentDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='payment_double', domain='payment',
        )
        self.detector = DoublePaymentDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'payment_double')

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_single_completed_payment_no_alert(self, mock_notify):
        """A single completed payment does not trigger an alert."""
        invoice = self.create_invoice()
        payment = self.create_payment(invoice=invoice, status='completed')

        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(payment)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_double_completed_payment_triggers_alert(self, mock_notify):
        """Two completed payments for the same invoice trigger an alert."""
        invoice = self.create_invoice()
        p1 = self.create_payment(invoice=invoice, status='completed')
        p2 = self.create_payment(invoice=invoice, status='completed')

        # The signal may have already created alerts. Check that at least one exists
        # after our explicit check.
        self.detector.check(p2)
        alerts = AnomalyAlert.objects.filter(
            anomaly_type=self.at,
            title__icontains='Double payment',
        )
        self.assertTrue(alerts.exists())


# ---------------------------------------------------------------------------
# PaymentStatusReversalDetector tests
# ---------------------------------------------------------------------------

class PaymentStatusReversalDetectorTest(TestDataMixin, TestCase):
    """Tests for PaymentStatusReversalDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='payment_status_reversal', domain='payment',
        )
        self.detector = PaymentStatusReversalDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'payment_status_reversal')

    def test_valid_transitions_defined(self):
        """VALID_TRANSITIONS covers all expected statuses."""
        self.assertIn('pending', self.detector.VALID_TRANSITIONS)
        self.assertIn('completed', self.detector.VALID_TRANSITIONS)
        self.assertIn('refunded', self.detector.VALID_TRANSITIONS)

    @patch('anomaly_detection.detectors.payment.PaymentStatusReversalDetector.create_alert')
    def test_new_payment_skips(self, mock_alert):
        """New payments (no pk) are skipped."""
        payment = MagicMock()
        payment.pk = None
        self.detector.check(payment)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_valid_transition_no_alert(self, mock_notify):
        """Valid transitions (pending -> completed) do not trigger alerts."""
        invoice = self.create_invoice()
        payment = self.create_payment(invoice=invoice, status='pending')

        # Simulate status change by updating the in-memory object
        payment.status = 'completed'
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(payment)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_invalid_reversal_triggers_alert(self, mock_notify):
        """Invalid transitions (completed -> pending) trigger an alert."""
        invoice = self.create_invoice()
        payment = self.create_payment(invoice=invoice, status='completed')

        # Change status to an invalid reverse
        payment.status = 'pending'
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(payment)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertGreater(alert_count_after, alert_count_before)
        latest = AnomalyAlert.objects.filter(anomaly_type=self.at).order_by('-pk').first()
        self.assertIn('reversal', latest.title.lower())

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_same_status_no_alert(self, mock_notify):
        """No alert when status hasn't changed."""
        invoice = self.create_invoice()
        payment = self.create_payment(invoice=invoice, status='pending')
        # Status unchanged
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(payment)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)


# ---------------------------------------------------------------------------
# InvoiceFeeStructureMismatchDetector tests
# ---------------------------------------------------------------------------

class InvoiceFeeStructureMismatchDetectorTest(TestDataMixin, TestCase):
    """Tests for InvoiceFeeStructureMismatchDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='payment_fee_mismatch', domain='payment',
        )
        self.detector = InvoiceFeeStructureMismatchDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'payment_fee_mismatch')

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector.create_alert')
    def test_no_fee_structure_skips(self, mock_alert):
        """Invoices without a fee structure are skipped."""
        invoice = MagicMock()
        invoice.fee_structure = None
        invoice.amount = Decimal('1000')
        self.detector.check(invoice)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector.create_alert')
    def test_no_amount_skips(self, mock_alert):
        """Invoices without an amount are skipped."""
        invoice = MagicMock()
        invoice.fee_structure = MagicMock()
        invoice.amount = None
        self.detector.check(invoice)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector.create_alert')
    def test_matching_amounts_no_alert(self, mock_alert):
        """When invoice amount matches fee structure total, no alert."""
        invoice = MagicMock()
        invoice.fee_structure.get_total_fee.return_value = Decimal('5000')
        invoice.amount = Decimal('5000')
        self.detector.check(invoice)
        mock_alert.assert_not_called()

    @patch('anomaly_detection.detectors.payment.InvoiceFeeStructureMismatchDetector.create_alert')
    def test_mismatch_triggers_alert(self, mock_alert):
        """When invoice amount differs from fee structure total, alert is created."""
        invoice = MagicMock()
        invoice.fee_structure.get_total_fee.return_value = Decimal('5000')
        invoice.amount = Decimal('4000')
        invoice.invoice_code = 'INV-999'
        invoice.user = MagicMock()
        self.detector.check(invoice)
        mock_alert.assert_called_once()


# ---------------------------------------------------------------------------
# DuplicateEnrollmentDetector tests
# ---------------------------------------------------------------------------

class DuplicateEnrollmentDetectorTest(TestDataMixin, TestCase):
    """Tests for DuplicateEnrollmentDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='enrollment_duplicate', domain='enrollment',
        )
        self.detector = DuplicateEnrollmentDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'enrollment_duplicate')

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_no_duplicate_no_alert(self, mock_notify):
        """A single registration does not trigger a duplicate alert."""
        school = self.create_school()
        filiere = self.create_filiere(tenant=school)
        reg = self.create_registration(
            tenant=school,
            email='unique@test.com',
            filiere=filiere,
            academic_year='2024-2025',
        )
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_duplicate_triggers_alert(self, mock_notify):
        """Two registrations with same email+filiere+year trigger an alert."""
        school = self.create_school()
        filiere = self.create_filiere(tenant=school)
        self.create_registration(
            tenant=school,
            email='dup@test.com',
            filiere=filiere,
            academic_year='2024-2025',
            status='pending',
        )
        reg2 = self.create_registration(
            tenant=school,
            email='dup@test.com',
            filiere=filiere,
            academic_year='2024-2025',
            status='pending',
        )
        # Signal may have already triggered detection. Check that alert exists after check.
        self.detector.check(reg2)
        alerts = AnomalyAlert.objects.filter(
            anomaly_type=self.at,
            title__icontains='Duplicate',
        )
        self.assertTrue(alerts.exists())


# ---------------------------------------------------------------------------
# InvalidStatusTransitionDetector tests
# ---------------------------------------------------------------------------

class InvalidStatusTransitionDetectorTest(TestDataMixin, TestCase):
    """Tests for InvalidStatusTransitionDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='enrollment_invalid_transition', domain='enrollment',
        )
        self.detector = InvalidStatusTransitionDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'enrollment_invalid_transition')

    def test_valid_transitions_defined(self):
        """VALID_TRANSITIONS covers all enrollment statuses."""
        for status in ('pending', 'under_review', 'approved', 'rejected', 'enrolled'):
            self.assertIn(status, self.detector.VALID_TRANSITIONS)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_no_history_skips(self, mock_notify):
        """Registration with no status history does not trigger alert."""
        school = self.create_school()
        reg = self.create_registration(tenant=school)
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_valid_transition_no_alert(self, mock_notify):
        """Valid transition (pending -> under_review) does not trigger alert."""
        from enrollment.models import EnrollmentStatusHistory

        school = self.create_school()
        reg = self.create_registration(tenant=school, status='under_review')
        EnrollmentStatusHistory.objects.create(
            registration=reg,
            old_status='pending',
            new_status='under_review',
        )
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_invalid_transition_triggers_alert(self, mock_notify):
        """Invalid transition (pending -> enrolled) triggers an alert."""
        from enrollment.models import EnrollmentStatusHistory

        school = self.create_school()
        reg = self.create_registration(tenant=school, status='enrolled')
        EnrollmentStatusHistory.objects.create(
            registration=reg,
            old_status='pending',
            new_status='enrolled',
        )
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertGreater(alert_count_after, alert_count_before)
        latest = AnomalyAlert.objects.filter(anomaly_type=self.at).order_by('-pk').first()
        self.assertIn('Invalid', latest.title)


# ---------------------------------------------------------------------------
# UnauthorizedApprovalDetector tests
# ---------------------------------------------------------------------------

class UnauthorizedApprovalDetectorTest(TestDataMixin, TestCase):
    """Tests for UnauthorizedApprovalDetector."""

    def setUp(self):
        self.at = self.create_anomaly_type(
            code='enrollment_unauthorized_approval', domain='enrollment',
        )
        self.detector = UnauthorizedApprovalDetector()

    def test_anomaly_code(self):
        self.assertEqual(self.detector.anomaly_code, 'enrollment_unauthorized_approval')

    def test_authorized_roles_set(self):
        """AUTHORIZED_ROLES includes direction, admin, secretary, registrar."""
        for role in ('direction', 'admin', 'secretary', 'registrar'):
            self.assertIn(role, self.detector.AUTHORIZED_ROLES)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_non_approved_status_skips(self, mock_notify):
        """Registrations not in approved/enrolled status are skipped."""
        school = self.create_school()
        reg = self.create_registration(tenant=school, status='pending')
        reviewer = self.create_student_user()
        reg.reviewed_by = reviewer
        reg.save()
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_no_reviewer_skips(self, mock_notify):
        """Approved registrations without a reviewer are skipped."""
        school = self.create_school()
        reg = self.create_registration(tenant=school, status='approved')
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_superuser_reviewer_skips(self, mock_notify):
        """Superuser reviewers are not flagged."""
        school = self.create_school()
        admin = self.create_admin_user()
        reg = self.create_registration(tenant=school, status='approved')
        reg.reviewed_by = admin
        reg.save()
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_authorized_role_no_alert(self, mock_notify):
        """Reviewer with an authorized role (direction) does not trigger alert."""
        school = self.create_school()
        direction = self.create_direction_user()
        reg = self.create_registration(tenant=school, status='approved')
        reg.reviewed_by = direction
        reg.save()
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertEqual(alert_count_before, alert_count_after)

    @patch('anomaly_detection.notifications.notify_anomaly')
    def test_unauthorized_role_triggers_alert(self, mock_notify):
        """A student approving enrollment triggers an alert."""
        school = self.create_school()
        student = self.create_student_user()
        reg = self.create_registration(tenant=school, status='approved')
        reg.reviewed_by = student
        reg.save()
        alert_count_before = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.detector.check(reg)
        alert_count_after = AnomalyAlert.objects.filter(anomaly_type=self.at).count()
        self.assertGreater(alert_count_after, alert_count_before)
        latest = AnomalyAlert.objects.filter(anomaly_type=self.at).order_by('-pk').first()
        self.assertIn('Unauthorized', latest.title)
        self.assertEqual(latest.severity, 'critical')
