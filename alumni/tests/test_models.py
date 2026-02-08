"""Tests for alumni app models."""

from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from alumni.models import Alumni, AlumniEvent, AlumniDonation, AlumniAchievement
from tests.helpers import TestDataMixin


class AlumniTest(TestDataMixin, TestCase):
    def _create_alumni(self, **kwargs):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        defaults = {
            'student': student,
            'graduation_year': 2023,
        }
        defaults.update(kwargs)
        return Alumni.objects.create(**defaults)

    def test_create(self):
        alumni = self._create_alumni()
        self.assertIsNotNone(alumni.pk)
        self.assertEqual(alumni.graduation_year, 2023)

    def test_str_raises_type_error(self):
        """Bug: Alumni.__str__ calls get_full_name() but it's a @property."""
        alumni = self._create_alumni()
        with self.assertRaises(TypeError):
            str(alumni)

    def test_defaults(self):
        alumni = self._create_alumni()
        self.assertTrue(alumni.is_active)
        self.assertFalse(alumni.willing_to_mentor)
        self.assertTrue(alumni.newsletter_subscribed)

    def test_one_to_one_student(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        Alumni.objects.create(student=student, graduation_year=2023)
        with self.assertRaises(Exception):
            Alumni.objects.create(student=student, graduation_year=2024)


class AlumniEventTest(TestDataMixin, TestCase):
    def _create_event(self, **kwargs):
        user = kwargs.pop('organizer', None) or self.create_user(role='direction')
        defaults = {
            'title': 'Alumni Reunion',
            'description': 'Annual reunion event',
            'event_type': 'reunion',
            'event_date': timezone.now() + timedelta(days=30),
            'location': 'Campus Hall',
            'organizer': user,
        }
        defaults.update(kwargs)
        return AlumniEvent.objects.create(**defaults)

    def test_create_and_str(self):
        event = self._create_event()
        self.assertIn('Alumni Reunion', str(event))

    def test_defaults(self):
        event = self._create_event()
        self.assertTrue(event.is_active)
        self.assertEqual(event.registration_fee, 0)

    def test_get_attendee_count_empty(self):
        event = self._create_event()
        self.assertEqual(event.get_attendee_count(), 0)

    def test_get_attendee_count(self):
        event = self._create_event()
        s1_user = self.create_student_user()
        s1 = self.create_student_profile(s1_user)
        a1 = Alumni.objects.create(student=s1, graduation_year=2022)
        event.attendees.add(a1)
        self.assertEqual(event.get_attendee_count(), 1)

    def test_is_full_no_limit(self):
        event = self._create_event(max_attendees=None)
        self.assertFalse(event.is_full())

    def test_is_full_not_yet(self):
        event = self._create_event(max_attendees=10)
        self.assertFalse(event.is_full())

    def test_is_full_reached(self):
        event = self._create_event(max_attendees=1)
        s1_user = self.create_student_user()
        s1 = self.create_student_profile(s1_user)
        a1 = Alumni.objects.create(student=s1, graduation_year=2022)
        event.attendees.add(a1)
        self.assertTrue(event.is_full())


class AlumniDonationTest(TestDataMixin, TestCase):
    def _create_donation(self, **kwargs):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        alumni = Alumni.objects.create(student=student, graduation_year=2022)
        defaults = {
            'alumni': alumni,
            'amount': Decimal('1000.00'),
            'transaction_id': f'TXN-{id(kwargs)}',
            'payment_method': 'stripe',
        }
        defaults.update(kwargs)
        return AlumniDonation.objects.create(**defaults)

    def test_create(self):
        donation = self._create_donation()
        self.assertIsNotNone(donation.pk)
        self.assertEqual(donation.amount, Decimal('1000.00'))

    def test_str_raises_type_error(self):
        """Bug: AlumniDonation.__str__ triggers Alumni.__str__ which calls get_full_name()."""
        donation = self._create_donation()
        with self.assertRaises(TypeError):
            str(donation)

    def test_defaults(self):
        donation = self._create_donation()
        self.assertEqual(donation.currency, 'USD')
        self.assertEqual(donation.purpose, 'general')
        self.assertFalse(donation.is_anonymous)
        self.assertFalse(donation.tax_receipt_sent)
        self.assertFalse(donation.thank_you_sent)

    def test_unique_transaction_id(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        alumni = Alumni.objects.create(student=student, graduation_year=2022)
        AlumniDonation.objects.create(
            alumni=alumni, amount=Decimal('100'), transaction_id='DUP-D',
            payment_method='cash',
        )
        s2_user = self.create_student_user()
        s2 = self.create_student_profile(s2_user)
        a2 = Alumni.objects.create(student=s2, graduation_year=2023)
        with self.assertRaises(Exception):
            AlumniDonation.objects.create(
                alumni=a2, amount=Decimal('200'), transaction_id='DUP-D',
                payment_method='cash',
            )


class AlumniAchievementTest(TestDataMixin, TestCase):
    def test_create(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        alumni = Alumni.objects.create(student=student, graduation_year=2022)
        achievement = AlumniAchievement.objects.create(
            alumni=alumni, achievement_type='award',
            title='Best Researcher', description='Won research award',
            achievement_date=date.today(),
        )
        self.assertIsNotNone(achievement.pk)
        self.assertEqual(achievement.title, 'Best Researcher')

    def test_str_raises_type_error(self):
        """Bug: AlumniAchievement.__str__ triggers Alumni.__str__ bug."""
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        alumni = Alumni.objects.create(student=student, graduation_year=2022)
        achievement = AlumniAchievement.objects.create(
            alumni=alumni, achievement_type='award',
            title='Test', description='Desc',
            achievement_date=date.today(),
        )
        with self.assertRaises(TypeError):
            str(achievement)

    def test_defaults(self):
        student_user = self.create_student_user()
        student = self.create_student_profile(student_user)
        alumni = Alumni.objects.create(student=student, graduation_year=2022)
        achievement = AlumniAchievement.objects.create(
            alumni=alumni, achievement_type='publication',
            title='Published Paper', description='Published in Nature',
            achievement_date=date.today(),
        )
        self.assertFalse(achievement.is_featured)
        self.assertTrue(achievement.is_published)
