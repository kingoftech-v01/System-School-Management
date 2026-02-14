"""Tests for scheduling app forms."""

from datetime import date, timedelta, time
from django.test import TestCase

from tests.helpers import TestDataMixin
from scheduling.forms import (
    RoomForm, TimeSlotForm, ScheduleEntryForm,
    ScheduleExceptionForm, SubstitutionRequestForm, CancellationForm,
)


class RoomFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'name': 'Room 101',
            'code': 'R101',
            'building': 'Main Building',
            'floor': 1,
            'capacity': 30,
            'room_type': 'classroom',
            'is_active': True,
        }
        form = RoomForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name(self):
        data = {'code': 'R101', 'capacity': 30, 'room_type': 'classroom'}
        form = RoomForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_missing_code(self):
        data = {'name': 'Room 101', 'capacity': 30, 'room_type': 'classroom'}
        form = RoomForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('code', form.errors)

    def test_all_room_types(self):
        for room_type in ['classroom', 'lab', 'amphitheatre', 'computer_room', 'meeting', 'gym', 'online']:
            data = {
                'name': f'Room {room_type}',
                'code': f'R-{room_type[:3]}',
                'capacity': 30,
                'room_type': room_type,
                'floor': 0,
            }
            form = RoomForm(data=data)
            self.assertTrue(form.is_valid(), f"Failed for room_type={room_type}: {form.errors}")

    def test_has_crispy_helper(self):
        form = RoomForm()
        self.assertTrue(hasattr(form, 'helper'))

    def test_meta_fields(self):
        form = RoomForm()
        expected = ['name', 'code', 'building', 'floor', 'capacity', 'room_type', 'equipment', 'is_active']
        for field_name in expected:
            self.assertIn(field_name, form.fields)


class TimeSlotFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'name': 'Period 1',
            'day_of_week': 0,
            'start_time': '08:00',
            'end_time': '10:00',
            'slot_type': 'class',
            'order': 1,
            'is_active': True,
        }
        form = TimeSlotForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_end_before_start_invalid(self):
        data = {
            'name': 'Bad Slot',
            'day_of_week': 0,
            'start_time': '14:00',
            'end_time': '08:00',
            'slot_type': 'class',
        }
        form = TimeSlotForm(data=data)
        self.assertFalse(form.is_valid())

    def test_end_equals_start_invalid(self):
        data = {
            'name': 'Equal Slot',
            'day_of_week': 0,
            'start_time': '10:00',
            'end_time': '10:00',
            'slot_type': 'class',
        }
        form = TimeSlotForm(data=data)
        self.assertFalse(form.is_valid())

    def test_missing_required_fields(self):
        form = TimeSlotForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('start_time', form.errors)
        self.assertIn('end_time', form.errors)

    def test_all_day_of_week_choices(self):
        for day in range(7):
            data = {
                'name': f'Day {day}',
                'day_of_week': day,
                'start_time': '08:00',
                'end_time': '10:00',
                'slot_type': 'class',
                'order': day,
            }
            form = TimeSlotForm(data=data)
            self.assertTrue(form.is_valid(), f"Failed for day={day}: {form.errors}")

    def test_has_crispy_helper(self):
        form = TimeSlotForm()
        self.assertTrue(hasattr(form, 'helper'))


class ScheduleEntryFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.course = self.create_course()
        self.professor = self.create_professor_user()
        self.room = self.create_room(tenant=self.tenant)
        self.time_slot = self.create_timeslot(tenant=self.tenant)

    def test_valid_form(self):
        data = {
            'course': self.course.pk,
            'professor': self.professor.pk,
            'room': self.room.pk,
            'time_slot': self.time_slot.pk,
            'effective_from': date.today().isoformat(),
            'effective_until': (date.today() + timedelta(days=120)).isoformat(),
            'recurrence': 'weekly',
            'status': 'active',
            'color': '#3788d8',
        }
        form = ScheduleEntryForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_effective_until_before_from_invalid(self):
        data = {
            'course': self.course.pk,
            'professor': self.professor.pk,
            'time_slot': self.time_slot.pk,
            'effective_from': (date.today() + timedelta(days=120)).isoformat(),
            'effective_until': date.today().isoformat(),
            'recurrence': 'weekly',
            'status': 'active',
        }
        form = ScheduleEntryForm(data=data)
        self.assertFalse(form.is_valid())

    def test_tenant_filters_querysets(self):
        form = ScheduleEntryForm(tenant=self.tenant)
        # Room and time_slot querysets should be filtered
        room_qs = form.fields['room'].queryset
        self.assertTrue(all(r.tenant == self.tenant for r in room_qs))

    def test_missing_required_fields(self):
        form = ScheduleEntryForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('course', form.errors)
        self.assertIn('professor', form.errors)
        self.assertIn('time_slot', form.errors)
        self.assertIn('effective_from', form.errors)
        self.assertIn('effective_until', form.errors)


class ScheduleExceptionFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.entry = self.create_schedule_entry(tenant=self.tenant)

    def test_valid_form(self):
        data = {
            'schedule_entry': self.entry.pk,
            'exception_type': 'cancellation',
            'date': date.today().isoformat(),
            'reason': 'Professor is sick',
            'notify_students': True,
        }
        form = ScheduleExceptionForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_required_fields(self):
        form = ScheduleExceptionForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('schedule_entry', form.errors)
        self.assertIn('exception_type', form.errors)
        self.assertIn('date', form.errors)

    def test_has_crispy_helper(self):
        form = ScheduleExceptionForm()
        self.assertTrue(hasattr(form, 'helper'))


class SubstitutionRequestFormTest(TestDataMixin, TestCase):
    def setUp(self):
        self.tenant = self.create_school()
        self.entry = self.create_schedule_entry(tenant=self.tenant)

    def test_valid_form(self):
        data = {
            'schedule_entry': self.entry.pk,
            'date': date.today().isoformat(),
            'reason': 'Cannot attend due to conference',
        }
        form = SubstitutionRequestForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_reason(self):
        data = {
            'schedule_entry': self.entry.pk,
            'date': date.today().isoformat(),
        }
        form = SubstitutionRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)

    def test_has_crispy_helper(self):
        form = SubstitutionRequestForm()
        self.assertTrue(hasattr(form, 'helper'))


class CancellationFormTest(TestDataMixin, TestCase):
    def test_valid_form(self):
        data = {
            'date': date.today().isoformat(),
            'reason': 'National holiday',
            'notify_students': True,
        }
        form = CancellationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_date(self):
        data = {'reason': 'Some reason', 'notify_students': True}
        form = CancellationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_missing_reason(self):
        data = {'date': date.today().isoformat(), 'notify_students': True}
        form = CancellationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('reason', form.errors)

    def test_notify_students_default_true(self):
        form = CancellationForm()
        self.assertTrue(form.fields['notify_students'].initial)

    def test_notify_students_optional(self):
        data = {
            'date': date.today().isoformat(),
            'reason': 'Reason text',
        }
        form = CancellationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_has_crispy_helper(self):
        form = CancellationForm()
        self.assertTrue(hasattr(form, 'helper'))
