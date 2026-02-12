"""Tests for alumni app forms."""

from datetime import datetime, date
from django.test import TestCase

from tests.helpers import TestDataMixin
from alumni.forms import AlumniForm, AlumniEventForm, DonationForm, AlumniAchievementForm


class AlumniFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'graduation_year': 2024,
            'current_occupation': 'Engineer',
            'current_employer': 'Tech Corp',
            'industry': 'Technology',
            'job_title': 'Software Engineer',
            'personal_email': 'alumni@test.com',
            'phone': '+1234567890',
            'city': 'Paris',
            'country': 'France',
            'willing_to_mentor': True,
        }
        form = AlumniForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_minimal_valid_form(self):
        data = {'graduation_year': 2020}
        form = AlumniForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_graduation_year(self):
        data = {'current_occupation': 'Engineer'}
        form = AlumniForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('graduation_year', form.errors)

    def test_invalid_email(self):
        data = {'graduation_year': 2024, 'personal_email': 'bad-email'}
        form = AlumniForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('personal_email', form.errors)

    def test_invalid_linkedin_url(self):
        data = {'graduation_year': 2024, 'linkedin_url': 'not-a-url'}
        form = AlumniForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('linkedin_url', form.errors)


class AlumniEventFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'title': 'Reunion 2024',
            'description': 'Annual alumni reunion event',
            'event_type': 'reunion',
            'event_date': '2025-09-15 10:00',
            'location': 'Main Campus',
            'registration_fee': '0.00',
        }
        form = AlumniEventForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = AlumniEventForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('location', form.errors)

    def test_with_optional_fields(self):
        data = {
            'title': 'Networking Event',
            'description': 'Meet professionals',
            'event_type': 'networking',
            'event_date': '2025-10-01 14:00',
            'location': 'Conference Center',
            'max_attendees': 100,
            'registration_fee': '25.00',
        }
        form = AlumniEventForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)


class DonationFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'amount': '100.00',
            'purpose': 'scholarship',
            'purpose_details': 'Supporting underprivileged students',
            'is_anonymous': False,
        }
        form = DonationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_amount(self):
        data = {'purpose': 'general'}
        form = DonationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)


class AlumniAchievementFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'achievement_type': 'award',
            'title': 'Best Innovation Award',
            'description': 'Won the annual innovation award',
            'achievement_date': '2024-06-15',
        }
        form = AlumniAchievementForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = AlumniAchievementForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('achievement_type', form.errors)
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('achievement_date', form.errors)
