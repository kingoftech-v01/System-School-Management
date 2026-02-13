"""Tests for admissions app models."""

from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase

from admissions.models import (
    AdmissionSession, AdmissionStudent, CounselingComment, AdmissionPayment,
)
from tests.helpers import TestDataMixin


class AdmissionSessionTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        session = AdmissionSession.objects.create(
            name='2024-2025',
            start_date=date(2024, 9, 1),
            end_date=date(2025, 6, 30),
        )
        self.assertEqual(str(session), '2024-2025')

    def test_defaults(self):
        session = AdmissionSession.objects.create(
            name='Test Session',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        self.assertTrue(session.is_active)

    def test_unique_name(self):
        AdmissionSession.objects.create(
            name='Unique', start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        with self.assertRaises(Exception):
            AdmissionSession.objects.create(
                name='Unique', start_date=date.today(),
                end_date=date.today() + timedelta(days=365),
            )


class AdmissionStudentTest(TestDataMixin, TestCase):
    def _create_session(self):
        return AdmissionSession.objects.create(
            name=f'Session-{id(self)}',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )

    def _create_application(self, **kwargs):
        session = kwargs.pop('session', None) or self._create_session()
        defaults = {
            'session': session,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': f'john{id(kwargs)}@example.com',
            'phone': '1234567890',
            'date_of_birth': date(2005, 1, 1),
            'gender': 'M',
            'guardian_first_name': 'Jane', 'guardian_last_name': 'Doe',
            'guardian_phone': '0987654321',
            'previous_school': 'Old School',
            'previous_grade': 'A',
        }
        defaults.update(kwargs)
        return AdmissionStudent.objects.create(**defaults)

    def test_create_and_str(self):
        app = self._create_application()
        self.assertIn('John', str(app))
        self.assertIn('Pending', str(app))

    def test_defaults(self):
        app = self._create_application()
        self.assertEqual(app.status, 'pending')
        self.assertFalse(app.application_fee_paid)
        self.assertFalse(app.admitted)

    def test_get_full_name(self):
        app = self._create_application(first_name='Alice', last_name='Smith')
        self.assertEqual(app.get_full_name(), 'Alice Smith')

    def test_status_choices(self):
        session = self._create_session()
        for status in ['pending', 'under_review', 'counseling', 'payment_pending', 'admitted', 'rejected']:
            app = self._create_application(session=session, status=status)
            self.assertEqual(app.status, status)


class CounselingCommentTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        session = AdmissionSession.objects.create(
            name='CC Session', start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        app = AdmissionStudent.objects.create(
            session=session, first_name='Test', last_name='Student',
            email='cc@test.com', phone='123', date_of_birth=date(2005, 1, 1),
            gender='F', guardian_first_name='Parent', guardian_last_name='Test', guardian_phone='456',
            previous_school='School', previous_grade='B',
        )
        counselor = self.create_user(role='direction')
        comment = CounselingComment.objects.create(
            application=app, counselor=counselor,
            comment='Good candidate',
        )
        self.assertIn('Comment by', str(comment))

    def test_defaults(self):
        session = AdmissionSession.objects.create(
            name='CC2', start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        app = AdmissionStudent.objects.create(
            session=session, first_name='T', last_name='S',
            email='cc2@test.com', phone='123', date_of_birth=date(2005, 1, 1),
            gender='M', guardian_first_name='P', guardian_last_name='T', guardian_phone='456',
            previous_school='S', previous_grade='C',
        )
        comment = CounselingComment.objects.create(
            application=app, counselor=self.create_user(role='direction'),
            comment='Test',
        )
        self.assertFalse(comment.is_recommendation)


class AdmissionPaymentTest(TestDataMixin, TestCase):
    def test_create_and_str(self):
        session = AdmissionSession.objects.create(
            name='Pay Session', start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        app = AdmissionStudent.objects.create(
            session=session, first_name='Pay', last_name='Test',
            email='pay@test.com', phone='123', date_of_birth=date(2005, 1, 1),
            gender='M', guardian_first_name='P', guardian_last_name='T', guardian_phone='456',
            previous_school='S', previous_grade='A',
        )
        payment = AdmissionPayment.objects.create(
            application=app, amount=Decimal('500.00'),
            transaction_id='TXN-12345',
        )
        self.assertIn('500', str(payment))

    def test_defaults(self):
        session = AdmissionSession.objects.create(
            name='Pay2', start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        app = AdmissionStudent.objects.create(
            session=session, first_name='P', last_name='T',
            email='pay2@test.com', phone='123', date_of_birth=date(2005, 1, 1),
            gender='F', guardian_first_name='G', guardian_last_name='T', guardian_phone='789',
            previous_school='S', previous_grade='B',
        )
        payment = AdmissionPayment.objects.create(
            application=app, amount=Decimal('100.00'),
            transaction_id='TXN-99999',
        )
        self.assertEqual(payment.payment_method, 'stripe')
        self.assertFalse(payment.verified)

    def test_unique_transaction_id(self):
        session = AdmissionSession.objects.create(
            name='PayU', start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
        )
        app1 = AdmissionStudent.objects.create(
            session=session, first_name='A', last_name='A',
            email='a@test.com', phone='1', date_of_birth=date(2005, 1, 1),
            gender='M', guardian_first_name='G', guardian_last_name='T', guardian_phone='2',
            previous_school='S', previous_grade='A',
        )
        app2 = AdmissionStudent.objects.create(
            session=session, first_name='B', last_name='B',
            email='b@test.com', phone='3', date_of_birth=date(2005, 1, 1),
            gender='F', guardian_first_name='G', guardian_last_name='T', guardian_phone='4',
            previous_school='S', previous_grade='B',
        )
        AdmissionPayment.objects.create(
            application=app1, amount=Decimal('100'), transaction_id='DUP',
        )
        with self.assertRaises(Exception):
            AdmissionPayment.objects.create(
                application=app2, amount=Decimal('100'), transaction_id='DUP',
            )
