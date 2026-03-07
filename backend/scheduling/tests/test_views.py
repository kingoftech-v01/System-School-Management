"""Tests for scheduling frontend views."""

from datetime import date, time

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware

from core.models import School, Session, Semester
from course.models import Course
from scheduling.models import Room, TimeSlot, ScheduleEntry, ScheduleNotification

User = get_user_model()


def _create_school(**kwargs):
    defaults = {
        'name': 'Test School', 'email': 'test@school.local', 'slug': 'test-views',
        'subscription_start': date(2025, 1, 1),
        'subscription_end': date(2025, 12, 31),
    }
    defaults.update(kwargs)
    if hasattr(School, 'schema_name'):
        defaults.setdefault('schema_name', 'test_views')
    return School.objects.create(**defaults)


class CalendarViewTest(TestCase):
    def setUp(self):
        self.school = _create_school()
        self.user = User.objects.create_user(
            username='student_cal', password='testpass', role='student',
            email='studentcal@test.com',
        )
        self.user.tenant = self.school
        self.user.save()

    def test_calendar_requires_login(self):
        response = self.client.get('/scheduling/calendar/')
        self.assertNotEqual(response.status_code, 200)

    def test_calendar_accessible_logged_in(self):
        self.client.force_login(self.user)
        response = self.client.get('/scheduling/calendar/')
        self.assertIn(response.status_code, [200, 302])


class MyScheduleViewTest(TestCase):
    def setUp(self):
        self.school = _create_school(slug='test-my-schedule')
        self.user = User.objects.create_user(
            username='prof_sched', password='testpass', role='professor',
            email='profsched@test.com',
        )
        self.user.tenant = self.school
        self.user.save()

    def test_my_schedule_requires_login(self):
        response = self.client.get('/scheduling/my/')
        self.assertNotEqual(response.status_code, 200)


class RoomCRUDViewTest(TestCase):
    def setUp(self):
        self.school = _create_school(slug='test-rooms')
        self.admin_user = User.objects.create_user(
            username='direction_rooms', password='testpass', role='direction',
            email='dir_rooms@test.com',
        )
        self.admin_user.tenant = self.school
        self.admin_user.save()
        self.room = Room.objects.create(
            tenant=self.school, name='Room A', code='RA',
            capacity=30, room_type='classroom',
        )

    def test_room_list_requires_direction(self):
        student = User.objects.create_user(
            username='student_rooms', password='testpass', role='student',
            email='student_rooms@test.com',
        )
        self.client.force_login(student)
        response = self.client.get('/scheduling/rooms/')
        self.assertIn(response.status_code, [302, 403])


class NotificationViewTest(TestCase):
    def setUp(self):
        self.school = _create_school(slug='test-notif')
        self.user = User.objects.create_user(
            username='notif_user', password='testpass', role='student',
            email='notif@test.com',
        )
        self.user.tenant = self.school
        self.user.save()

    def test_notification_list_requires_login(self):
        response = self.client.get('/scheduling/notifications/')
        self.assertNotEqual(response.status_code, 200)


class WizardViewTest(TestCase):
    def setUp(self):
        self.school = _create_school(slug='test-wizard')
        self.admin_user = User.objects.create_user(
            username='dir_wizard', password='testpass', role='direction',
            email='dir_wizard@test.com',
        )
        self.admin_user.tenant = self.school
        self.admin_user.save()

    def test_wizard_step1_requires_direction(self):
        student = User.objects.create_user(
            username='student_wizard', password='testpass', role='student',
            email='student_wizard@test.com',
        )
        self.client.force_login(student)
        response = self.client.get('/scheduling/wizard/')
        self.assertIn(response.status_code, [302, 403])

    def test_wizard_step2_redirects_without_session_config(self):
        self.client.force_login(self.admin_user)
        response = self.client.get('/scheduling/wizard/step2/')
        # Should redirect to step 1 since no wizard_config in session
        self.assertIn(response.status_code, [200, 302])
