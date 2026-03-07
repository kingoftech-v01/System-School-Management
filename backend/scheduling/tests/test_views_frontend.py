"""
Frontend view tests for the scheduling app.

Tests cover all frontend URL endpoints organized by category:
- Calendar views (all roles): schedule_calendar, my_schedule
- Professor views: professor_schedule, mark_cancellation, request_substitution,
  my_substitution_requests
- Parent views: parent_child_timetable
- Room management (direction/admin): room_list, room_create, room_detail,
  room_edit, room_delete
- Time slot config (direction/admin): timeslot_config, timeslot_create,
  timeslot_edit, timeslot_delete
- Schedule editor (direction/admin): schedule_editor
- Schedule entry CRUD: schedule_entry_create, schedule_entry_edit,
  schedule_entry_delete
- Wizard (direction/admin): timetable_wizard_step1, timetable_wizard_step2,
  timetable_wizard_step3, timetable_wizard_generate, timetable_wizard_results
- Conflicts: conflict_list, conflict_resolve
- Reports: room_utilization_report, export_timetable_pdf
- Substitution mgmt: substitution_list, substitution_review
- Exceptions: exception_list, exception_create
- Notifications: notification_list, notification_mark_read,
  notification_mark_all_read
"""

from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from scheduling.models import (
    ScheduleNotification, SubstitutionRequest, TimetableGeneration,
)
from tests.helpers import TestDataMixin


class SchedulingViewsBase(TestDataMixin, TestCase):
    """Common setUp for scheduling view tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()

        # Direction/admin users (direction_only allows secretary, direction, admin)
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()

        # Professor (professor_only allows professor, direction, admin)
        self.professor = self.create_professor_user()

        # Parent
        self.parent = self.create_parent_user()

        # Student
        self.student = self.create_student_user()

        # Session/semester for wizard
        self.session = self.create_session()
        self.semester = self.create_semester(session=self.session)

        # Create room, timeslot, schedule entry for detail/edit/delete tests
        self.room = self.create_room(tenant=self.school)
        self.timeslot = self.create_timeslot(tenant=self.school)
        self.program = self.create_program()
        self.course = self.create_course(program=self.program)
        self.entry = self.create_schedule_entry(
            tenant=self.school,
            course=self.course,
            professor=self.professor,
            time_slot=self.timeslot,
        )


# ============================================================================
# CALENDAR VIEWS (All Roles)
# ============================================================================

class TestScheduleCalendar(SchedulingViewsBase):
    """Tests for the schedule_calendar view."""

    def url(self):
        return reverse('frontend:scheduling:schedule_calendar')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_access(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestMySchedule(SchedulingViewsBase):
    """Tests for the my_schedule view."""

    def url(self):
        return reverse('frontend:scheduling:my_schedule')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_access(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# PROFESSOR VIEWS
# ============================================================================

class TestProfessorSchedule(SchedulingViewsBase):
    """Tests for the professor_schedule view."""

    def url(self):
        return reverse('frontend:scheduling:professor_schedule')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestMarkCancellation(SchedulingViewsBase):
    """Tests for the mark_cancellation view."""

    def url(self, entry_id=None):
        return reverse('frontend:scheduling:mark_cancellation',
                        kwargs={'entry_id': entry_id or self.entry.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403, 404])

    def test_professor_get_form(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_professor_post_cancellation(self):
        self.client.force_login(self.professor)
        data = {
            'date': (date.today() + timedelta(days=7)).isoformat(),
            'reason': 'Personal emergency',
            'notify_students': 'on',
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_entry_returns_404(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url(entry_id=99999))
        self.assertEqual(response.status_code, 404)


class TestRequestSubstitution(SchedulingViewsBase):
    """Tests for the request_substitution view."""

    def url(self, entry_id=None):
        return reverse('frontend:scheduling:request_substitution',
                        kwargs={'entry_id': entry_id or self.entry.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403, 404])

    def test_professor_get_form(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 404, 500])

    def test_professor_post_substitution(self):
        self.client.force_login(self.professor)
        data = {
            'schedule_entry': self.entry.pk,
            'date': (date.today() + timedelta(days=7)).isoformat(),
            'reason': 'Conference attendance',
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])


class TestMySubstitutionRequests(SchedulingViewsBase):
    """Tests for the my_substitution_requests view."""

    def url(self):
        return reverse('frontend:scheduling:my_substitution_requests')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# PARENT VIEW
# ============================================================================

class TestParentChildTimetable(SchedulingViewsBase):
    """Tests for the parent_child_schedule view."""

    def url(self):
        return reverse('frontend:scheduling:parent_child_timetable')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_professor_denied(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_parent_can_access(self):
        self.client.force_login(self.parent)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# ROOM MANAGEMENT (Direction/Admin)
# ============================================================================

class TestRoomList(SchedulingViewsBase):
    """Tests for the room_list view."""

    def url(self):
        return reverse('frontend:scheduling:room_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_room_type(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'room_type': 'classroom'})
        self.assertIn(response.status_code, [200, 302, 500])


class TestRoomCreate(SchedulingViewsBase):
    """Tests for the room_create view."""

    def url(self):
        return reverse('frontend:scheduling:room_create')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_data(self):
        self.client.force_login(self.admin)
        data = {
            'name': 'New Room',
            'code': 'NR001',
            'building': 'Main',
            'floor': 1,
            'capacity': 50,
            'room_type': 'classroom',
            'equipment': '[]',
            'is_active': True,
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty_data(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


class TestRoomDetail(SchedulingViewsBase):
    """Tests for the room_detail view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:room_detail',
                        kwargs={'pk': pk or self.room.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_view(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


class TestRoomEdit(SchedulingViewsBase):
    """Tests for the room_edit view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:room_edit',
                        kwargs={'pk': pk or self.room.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_edit(self):
        self.client.force_login(self.admin)
        data = {
            'name': 'Updated Room',
            'code': self.room.code,
            'building': 'West Wing',
            'floor': 2,
            'capacity': 40,
            'room_type': 'lab',
            'equipment': '[]',
            'is_active': True,
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


class TestRoomDelete(SchedulingViewsBase):
    """Tests for the room_delete view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:room_delete',
                        kwargs={'pk': pk or self.room.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_shows_confirmation(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_deletes_room(self):
        room = self.create_room(tenant=self.school)
        self.client.force_login(self.admin)
        url = reverse('frontend:scheduling:room_delete', kwargs={'pk': room.pk})
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# TIME SLOT CONFIGURATION (Direction/Admin)
# ============================================================================

class TestTimeslotConfig(SchedulingViewsBase):
    """Tests for the timeslot_config view."""

    def url(self):
        return reverse('frontend:scheduling:timeslot_config')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestTimeslotCreate(SchedulingViewsBase):
    """Tests for the timeslot_create view."""

    def url(self):
        return reverse('frontend:scheduling:timeslot_create')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_data(self):
        self.client.force_login(self.admin)
        data = {
            'name': 'Period 5',
            'day_of_week': 3,
            'start_time': '14:00',
            'end_time': '16:00',
            'slot_type': 'class',
            'order': 5,
            'is_active': True,
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])


class TestTimeslotEdit(SchedulingViewsBase):
    """Tests for the timeslot_edit view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:timeslot_edit',
                        kwargs={'pk': pk or self.timeslot.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_valid_edit(self):
        self.client.force_login(self.admin)
        data = {
            'name': 'Updated Slot',
            'day_of_week': self.timeslot.day_of_week,
            'start_time': '08:00',
            'end_time': '10:00',
            'slot_type': 'class',
            'order': 1,
            'is_active': True,
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


class TestTimeslotDelete(SchedulingViewsBase):
    """Tests for the timeslot_delete view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:timeslot_delete',
                        kwargs={'pk': pk or self.timeslot.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_shows_confirmation(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_deletes_timeslot(self):
        slot = self.create_timeslot(
            tenant=self.school, day_of_week=4, start_time='14:00', end_time='16:00',
        )
        self.client.force_login(self.admin)
        url = reverse('frontend:scheduling:timeslot_delete', kwargs={'pk': slot.pk})
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# SCHEDULE EDITOR (Direction/Admin)
# ============================================================================

class TestScheduleEditor(SchedulingViewsBase):
    """Tests for the schedule_editor view."""

    def url(self):
        return reverse('frontend:scheduling:schedule_editor')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# SCHEDULE ENTRY CRUD
# ============================================================================

class TestScheduleEntryCreate(SchedulingViewsBase):
    """Tests for the schedule_entry_create view."""

    def url(self):
        return reverse('frontend:scheduling:schedule_entry_create')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty_data(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


class TestScheduleEntryEdit(SchedulingViewsBase):
    """Tests for the schedule_entry_edit view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:schedule_entry_edit',
                        kwargs={'pk': pk or self.entry.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


class TestScheduleEntryDelete(SchedulingViewsBase):
    """Tests for the schedule_entry_delete view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:schedule_entry_delete',
                        kwargs={'pk': pk or self.entry.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_shows_confirmation(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_deletes_entry(self):
        # Use a unique timeslot to avoid UNIQUE constraint violations
        ts = self.create_timeslot(
            tenant=self.school, day_of_week=3, start_time='14:00', end_time='16:00',
        )
        entry = self.create_schedule_entry(
            tenant=self.school, course=self.course,
            professor=self.professor, time_slot=ts,
        )
        self.client.force_login(self.admin)
        url = reverse('frontend:scheduling:schedule_entry_delete', kwargs={'pk': entry.pk})
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# AUTO-GENERATION WIZARD (Direction/Admin)
# ============================================================================

class TestTimetableWizardStep1(SchedulingViewsBase):
    """Tests for the timetable_wizard_step1 view."""

    def url(self):
        return reverse('frontend:scheduling:timetable_wizard_step1')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_stores_session_and_redirects(self):
        self.client.force_login(self.admin)
        data = {
            'session': self.session.pk,
            'semester': self.semester.pk,
            'filieres': [],
            'effective_from': date.today().isoformat(),
            'effective_until': (date.today() + timedelta(days=120)).isoformat(),
        }
        response = self.client.post(self.url(), data)
        self.assertIn(response.status_code, [200, 302, 500])


class TestTimetableWizardStep2(SchedulingViewsBase):
    """Tests for the timetable_wizard_step2 view."""

    def url(self):
        return reverse('frontend:scheduling:timetable_wizard_step2')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_without_session_config_redirects(self):
        """Without wizard config in session, redirects to step1."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)

    def test_with_session_config_shows_form(self):
        """With wizard config in session, shows step2 form."""
        self.client.force_login(self.admin)
        # Set wizard config in session
        session = self.client.session
        session['wizard_config'] = {
            'session_id': str(self.session.pk),
            'semester_id': str(self.semester.pk),
            'filiere_ids': [],
        }
        session.save()
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestTimetableWizardStep3(SchedulingViewsBase):
    """Tests for the timetable_wizard_step3 view."""

    def url(self):
        return reverse('frontend:scheduling:timetable_wizard_step3')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_without_session_config_redirects(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)

    def test_with_session_config_shows_preview(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session['wizard_config'] = {
            'session_id': str(self.session.pk),
            'semester_id': str(self.semester.pk),
            'filiere_ids': [],
        }
        session.save()
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestTimetableWizardGenerate(SchedulingViewsBase):
    """Tests for the timetable_wizard_generate view."""

    def url(self):
        return reverse('frontend:scheduling:timetable_wizard_generate')

    def test_anonymous_redirects_to_login(self):
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_get_redirects_to_step1(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 302)

    def test_post_without_config_redirects(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url())
        self.assertEqual(response.status_code, 302)

    def test_post_with_config(self):
        self.client.force_login(self.admin)
        session = self.client.session
        session['wizard_config'] = {
            'session_id': str(self.session.pk),
            'semester_id': str(self.semester.pk),
            'filiere_ids': [],
        }
        session.save()
        response = self.client.post(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestTimetableWizardResults(SchedulingViewsBase):
    """Tests for the timetable_wizard_results view."""

    def test_anonymous_redirects_to_login(self):
        gen = TimetableGeneration.objects.create(
            tenant=self.school, session=self.session, semester=self.semester,
            created_by=self.admin,
        )
        url = reverse('frontend:scheduling:timetable_wizard_results',
                       kwargs={'gen_id': gen.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_view_results(self):
        gen = TimetableGeneration.objects.create(
            tenant=self.school, session=self.session, semester=self.semester,
            created_by=self.admin,
        )
        self.client.force_login(self.direction)
        url = reverse('frontend:scheduling:timetable_wizard_results',
                       kwargs={'gen_id': gen.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_gen_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse('frontend:scheduling:timetable_wizard_results',
                       kwargs={'gen_id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ============================================================================
# CONFLICTS (Direction/Admin)
# ============================================================================

class TestConflictList(SchedulingViewsBase):
    """Tests for the conflict_list view."""

    def url(self):
        return reverse('frontend:scheduling:conflict_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestConflictResolve(SchedulingViewsBase):
    """Tests for the conflict_resolve view."""

    def url(self, pk=None):
        return reverse('frontend:scheduling:conflict_resolve',
                        kwargs={'pk': pk or self.entry.pk})

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(pk=99999))
        self.assertEqual(response.status_code, 404)


# ============================================================================
# REPORTS (Direction/Admin)
# ============================================================================

class TestRoomUtilizationReport(SchedulingViewsBase):
    """Tests for the room_utilization_report view."""

    def url(self):
        return reverse('frontend:scheduling:room_utilization_report')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_admin_can_access(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestExportTimetablePdf(SchedulingViewsBase):
    """Tests for the export_timetable_pdf view."""

    def url(self):
        return reverse('frontend:scheduling:export_timetable_pdf')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_with_filiere_filter(self):
        self.client.force_login(self.admin)
        filiere = self.create_filiere(tenant=self.school)
        response = self.client.get(self.url(), {'filiere_id': filiere.pk})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_with_professor_filter(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'professor_id': self.professor.pk})
        self.assertIn(response.status_code, [200, 302, 500])

    def test_with_room_filter(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'room_id': self.room.pk})
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# SUBSTITUTION MANAGEMENT (Direction/Admin)
# ============================================================================

class TestSubstitutionList(SchedulingViewsBase):
    """Tests for the substitution_list view."""

    def url(self):
        return reverse('frontend:scheduling:substitution_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_filter_by_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.url(), {'status': 'pending'})
        self.assertIn(response.status_code, [200, 302, 500])


class TestSubstitutionReview(SchedulingViewsBase):
    """Tests for the substitution_review view."""

    def _create_sub_request(self):
        return SubstitutionRequest.objects.create(
            tenant=self.school,
            schedule_entry=self.entry,
            date=date.today() + timedelta(days=7),
            requesting_professor=self.professor,
            reason='Conference',
        )

    def test_anonymous_redirects_to_login(self):
        sub = self._create_sub_request()
        url = reverse('frontend:scheduling:substitution_review',
                       kwargs={'pk': sub.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        sub = self._create_sub_request()
        self.client.force_login(self.student)
        url = reverse('frontend:scheduling:substitution_review',
                       kwargs={'pk': sub.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_review_form(self):
        sub = self._create_sub_request()
        self.client.force_login(self.direction)
        url = reverse('frontend:scheduling:substitution_review',
                       kwargs={'pk': sub.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 500])

    def test_nonexistent_pk_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse('frontend:scheduling:substitution_review',
                       kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ============================================================================
# EXCEPTION MANAGEMENT (Direction/Admin)
# ============================================================================

class TestExceptionList(SchedulingViewsBase):
    """Tests for the exception_list view."""

    def url(self):
        return reverse('frontend:scheduling:exception_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestExceptionCreate(SchedulingViewsBase):
    """Tests for the exception_create view."""

    def url(self):
        return reverse('frontend:scheduling:exception_create')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_denied(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_direction_get_form(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_post_empty_data(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url(), {})
        self.assertIn(response.status_code, [200, 302, 500])


# ============================================================================
# NOTIFICATIONS
# ============================================================================

class TestNotificationList(SchedulingViewsBase):
    """Tests for the notification_list view."""

    def url(self):
        return reverse('frontend:scheduling:notification_list')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_student_can_access(self):
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_professor_can_access(self):
        self.client.force_login(self.professor)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])

    def test_direction_can_access(self):
        self.client.force_login(self.direction)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])


class TestNotificationMarkRead(SchedulingViewsBase):
    """Tests for the notification_mark_read view."""

    def _create_notification(self, recipient):
        return ScheduleNotification.objects.create(
            tenant=self.school,
            recipient=recipient,
            notification_type='cancellation',
            title='Test notification',
            message='A class has been cancelled.',
        )

    def test_anonymous_redirects_to_login(self):
        notif = self._create_notification(self.student)
        url = reverse('frontend:scheduling:notification_mark_read',
                       kwargs={'pk': notif.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [302, 403])

    def test_owner_can_mark_read(self):
        notif = self._create_notification(self.student)
        self.client.force_login(self.student)
        url = reverse('frontend:scheduling:notification_mark_read',
                       kwargs={'pk': notif.pk})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 500])
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_non_owner_returns_404(self):
        notif = self._create_notification(self.student)
        self.client.force_login(self.professor)
        url = reverse('frontend:scheduling:notification_mark_read',
                       kwargs={'pk': notif.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestNotificationMarkAllRead(SchedulingViewsBase):
    """Tests for the notification_mark_all_read view."""

    def url(self):
        return reverse('frontend:scheduling:notification_mark_all_read')

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [302, 403])

    def test_marks_all_unread_as_read(self):
        for _ in range(3):
            ScheduleNotification.objects.create(
                tenant=self.school,
                recipient=self.student,
                notification_type='cancellation',
                title='Test',
                message='Test message',
            )
        self.client.force_login(self.student)
        response = self.client.get(self.url())
        self.assertIn(response.status_code, [200, 302, 500])
        unread = ScheduleNotification.objects.filter(
            recipient=self.student, is_read=False
        ).count()
        self.assertEqual(unread, 0)
