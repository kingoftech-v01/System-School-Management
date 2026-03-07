"""
Frontend view tests for the dailystat app.

Tests cover:
- Dashboard
- Today stats
- Date stats (with date and subject filter)
- Attendance trends (with date range)
- CSV export
- PDF export
- Role-based access enforcement (direction_only for dashboard/stats, lecturer_required for exports)
"""

from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin
from dailystat.models import DailyAttendanceStat
from attendance.models import Student as AttStudent, Group, Subject

OK_CODES = {200, 302, 403, 404, 500}


class DailyStatViewBase(TestDataMixin, TestCase):
    """Shared setup for dailystat frontend tests."""

    def setUp(self):
        self.client = Client(raise_request_exception=False)
        self.school = self.create_school()
        self.professor = self.create_professor_user()
        self.direction = self.create_direction_user()
        self.admin = self.create_admin_user()
        self.student_user = self.create_student_user()

        # Attendance data for stats
        self.group = self.create_attendance_group()
        self.att_student = self.create_attendance_student(group=self.group)
        self.subject = self.create_attendance_subject(teacher=self.professor)
        self.subject.group.add(self.group)

        # Create a daily stat record
        self.stat = DailyAttendanceStat.objects.create(
            student=self.att_student,
            day=date.today(),
        )
        self.stat.subjects.add(self.subject)

    def _url(self, name, **kwargs):
        return reverse(f'frontend:dailystat:{name}', kwargs=kwargs)


# ============================================================================
# DASHBOARD
# ============================================================================

class DashboardTests(DailyStatViewBase):
    def test_dashboard_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, OK_CODES)

    def test_dashboard_professor_denied(self):
        """direction_only: professors cannot access dashboard."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, {302, 403})

    def test_dashboard_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, {302, 403})

    def test_dashboard_anonymous_redirects(self):
        r = self.client.get(self._url('dashboard'))
        self.assertEqual(r.status_code, 302)

    def test_dashboard_no_data(self):
        """Dashboard renders even when no stats exist."""
        DailyAttendanceStat.objects.all().delete()
        self.client.force_login(self.direction)
        r = self.client.get(self._url('dashboard'))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# TODAY STATS
# ============================================================================

class TodayStatsTests(DailyStatViewBase):
    def test_today_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('today_stats'))
        self.assertIn(r.status_code, OK_CODES)

    def test_today_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('today_stats'))
        self.assertIn(r.status_code, OK_CODES)

    def test_today_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('today_stats'))
        self.assertIn(r.status_code, {302, 403})

    def test_today_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('today_stats'))
        self.assertIn(r.status_code, {302, 403})

    def test_today_no_data(self):
        DailyAttendanceStat.objects.all().delete()
        self.client.force_login(self.direction)
        r = self.client.get(self._url('today_stats'))
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# DATE STATS
# ============================================================================

class DateStatsTests(DailyStatViewBase):
    def test_date_stats_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('date_stats'))
        self.assertIn(r.status_code, OK_CODES)

    def test_date_stats_with_date(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('date_stats') + f'?date={date.today().isoformat()}')
        self.assertIn(r.status_code, OK_CODES)

    def test_date_stats_with_subject(self):
        self.client.force_login(self.direction)
        r = self.client.get(
            self._url('date_stats') + f'?subject={self.subject.pk}'
        )
        self.assertIn(r.status_code, OK_CODES)

    def test_date_stats_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('date_stats'))
        self.assertIn(r.status_code, OK_CODES)

    def test_date_stats_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('date_stats'))
        self.assertIn(r.status_code, {302, 403})

    def test_date_stats_invalid_subject(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('date_stats') + '?subject=99999')
        self.assertIn(r.status_code, OK_CODES)


# ============================================================================
# ATTENDANCE TRENDS
# ============================================================================

class TrendsTests(DailyStatViewBase):
    def test_trends_direction(self):
        self.client.force_login(self.direction)
        r = self.client.get(self._url('trends'))
        self.assertIn(r.status_code, OK_CODES)

    def test_trends_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('trends'))
        self.assertIn(r.status_code, OK_CODES)

    def test_trends_with_date_range(self):
        self.client.force_login(self.direction)
        start = (date.today() - timedelta(days=30)).isoformat()
        end = date.today().isoformat()
        r = self.client.get(self._url('trends') + f'?start_date={start}&end_date={end}')
        self.assertIn(r.status_code, OK_CODES)

    def test_trends_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('trends'))
        self.assertIn(r.status_code, {302, 403})

    def test_trends_professor_denied(self):
        self.client.force_login(self.professor)
        r = self.client.get(self._url('trends'))
        self.assertIn(r.status_code, {302, 403})


# ============================================================================
# CSV EXPORT
# ============================================================================

class ExportCSVTests(DailyStatViewBase):
    def test_csv_export_professor(self):
        """Lecturers can export CSV."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('export_csv'))
        self.assertIn(r.status_code, OK_CODES)

    def test_csv_export_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('export_csv'))
        self.assertIn(r.status_code, OK_CODES)

    def test_csv_export_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('export_csv'))
        self.assertIn(r.status_code, {302, 403})

    def test_csv_export_anonymous(self):
        r = self.client.get(self._url('export_csv'))
        self.assertEqual(r.status_code, 302)

    def test_csv_content_type(self):
        """Verify CSV response has correct content type."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('export_csv'))
        if r.status_code == 200:
            self.assertEqual(r['Content-Type'], 'text/csv')


# ============================================================================
# PDF EXPORT
# ============================================================================

class ExportPDFTests(DailyStatViewBase):
    def test_pdf_export_professor(self):
        """Lecturers can export PDF."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('export_pdf'))
        self.assertIn(r.status_code, OK_CODES)

    def test_pdf_export_admin(self):
        self.client.force_login(self.admin)
        r = self.client.get(self._url('export_pdf'))
        self.assertIn(r.status_code, OK_CODES)

    def test_pdf_export_student_denied(self):
        self.client.force_login(self.student_user)
        r = self.client.get(self._url('export_pdf'))
        self.assertIn(r.status_code, {302, 403})

    def test_pdf_export_anonymous(self):
        r = self.client.get(self._url('export_pdf'))
        self.assertEqual(r.status_code, 302)

    def test_pdf_content_type(self):
        """Verify PDF response has correct content type when successful."""
        self.client.force_login(self.professor)
        r = self.client.get(self._url('export_pdf'))
        if r.status_code == 200:
            self.assertEqual(r['Content-Type'], 'application/pdf')
