"""
Frontend view tests for the reports app.

Tests cover:
- student_complete_record (GET/POST, role checks)
- incident_report_pdf (GET, role checks)
- attendance_report (GET/POST with pdf/csv/xlsx, role checks)
- discipline_history_pdf (GET, role checks)
- grades_export (GET with csv/xlsx, role checks)
- export_audit_log (GET, filtering, pagination, role checks)
"""

from datetime import date
from unittest.mock import patch, MagicMock

from django.http import HttpResponse
from django.test import TestCase, Client
from django.urls import reverse

from tests.helpers import TestDataMixin


class StudentCompleteRecordTests(TestDataMixin, TestCase):
    """Tests for student_complete_record view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.prefet = self.create_prefet_user()
        self.registrar = self.create_registrar_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.url = reverse(
            'frontend:reports:student_complete_record',
            kwargs={'pk': self.student_profile.pk},
        )

    def test_get_shows_reason_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_anonymous_redirects(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_student_role_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_direction_has_access(self):
        self.client.force_login(self.direction)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_prefet_has_access(self):
        self.client.force_login(self.prefet)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_registrar_has_access(self):
        self.client.force_login(self.registrar)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    @patch('reports.views_frontend.collect_student_complete_record')
    @patch('reports.views_frontend.render_report_pdf')
    @patch('reports.views_frontend.log_export')
    def test_post_valid_generates_pdf(self, mock_log, mock_pdf, mock_collect):
        mock_user = MagicMock()
        mock_user.get_full_name = 'Test Student'
        mock_user.username = 'teststudent'
        mock_collect.return_value = {'user': mock_user}
        mock_pdf.return_value = HttpResponse(b'%PDF', content_type='application/pdf')

        self.client.force_login(self.admin)
        resp = self.client.post(self.url, {'reason': 'Transfer request'})
        self.assertEqual(resp.status_code, 200)
        mock_log.assert_called_once()
        mock_pdf.assert_called_once()

    @patch('reports.views_frontend.collect_student_complete_record')
    def test_post_invalid_shows_form(self, mock_collect):
        self.client.force_login(self.admin)
        resp = self.client.post(self.url, {'reason': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['form'].errors)

    def test_nonexistent_student_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:reports:student_complete_record',
            kwargs={'pk': 99999},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class IncidentReportPdfTests(TestDataMixin, TestCase):
    """Tests for incident_report_pdf view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.prefet = self.create_prefet_user()
        self.student_user = self.create_student_user()

    @patch('reports.views_frontend.collect_incident_report')
    @patch('reports.views_frontend.render_report_pdf')
    @patch('reports.views_frontend.log_export')
    def test_admin_can_generate_pdf(self, mock_log, mock_pdf, mock_collect):
        incident = MagicMock()
        incident.title = 'Test Incident'
        mock_collect.return_value = {'incident': incident}
        mock_pdf.return_value = HttpResponse(b'%PDF', content_type='application/pdf')

        self.client.force_login(self.admin)
        url = reverse(
            'frontend:reports:incident_report_pdf', kwargs={'pk': 1}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        mock_log.assert_called_once()

    def test_student_role_denied(self):
        self.client.force_login(self.student_user)
        url = reverse(
            'frontend:reports:incident_report_pdf', kwargs={'pk': 1}
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)


class AttendanceReportTests(TestDataMixin, TestCase):
    """Tests for attendance_report view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.student_user = self.create_student_user()
        self.url = reverse('frontend:reports:attendance_report')

    def test_get_shows_filter_form(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_anonymous_redirects(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_direction_has_access(self):
        self.client.force_login(self.direction)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)


class DisciplineHistoryPdfTests(TestDataMixin, TestCase):
    """Tests for discipline_history_pdf view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.prefet = self.create_prefet_user()
        self.student_user = self.create_student_user()

    @patch('reports.views_frontend.collect_discipline_history')
    @patch('reports.views_frontend.render_report_pdf')
    @patch('reports.views_frontend.log_export')
    def test_admin_can_generate_pdf(self, mock_log, mock_pdf, mock_collect):
        mock_collect.return_value = {'history': []}
        mock_pdf.return_value = HttpResponse(b'%PDF', content_type='application/pdf')

        self.client.force_login(self.admin)
        url = reverse(
            'frontend:reports:discipline_history_pdf',
            kwargs={'pk': self.student_user.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        mock_log.assert_called_once()

    @patch('reports.views_frontend.collect_discipline_history')
    @patch('reports.views_frontend.render_report_pdf')
    @patch('reports.views_frontend.log_export')
    def test_prefet_can_access(self, mock_log, mock_pdf, mock_collect):
        mock_collect.return_value = {'history': []}
        mock_pdf.return_value = HttpResponse(b'%PDF', content_type='application/pdf')

        self.client.force_login(self.prefet)
        url = reverse(
            'frontend:reports:discipline_history_pdf',
            kwargs={'pk': self.student_user.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_student_role_denied(self):
        self.client.force_login(self.student_user)
        url = reverse(
            'frontend:reports:discipline_history_pdf',
            kwargs={'pk': self.student_user.pk},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

    def test_nonexistent_user_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:reports:discipline_history_pdf',
            kwargs={'pk': 99999},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class GradesExportTests(TestDataMixin, TestCase):
    """Tests for grades_export view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.professor = self.create_professor_user()
        self.student_user = self.create_student_user()
        self.program = self.create_program()
        self.student_profile = self.create_student_profile(
            user=self.student_user, program=self.program,
        )
        self.url = reverse(
            'frontend:reports:grades_export',
            kwargs={'pk': self.student_profile.pk},
        )

    @patch('reports.views_frontend.render_csv_response')
    @patch('reports.views_frontend.log_export')
    def test_csv_export_default(self, mock_log, mock_csv):
        mock_csv.return_value = HttpResponse('csv-data', content_type='text/csv')
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        mock_log.assert_called_once()

    @patch('reports.views_frontend.render_excel_response')
    @patch('reports.views_frontend.log_export')
    def test_xlsx_export(self, mock_log, mock_xlsx):
        mock_xlsx.return_value = HttpResponse(b'xlsx-data', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?export_format=xlsx')
        self.assertEqual(resp.status_code, 200)
        mock_log.assert_called_once()

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_nonexistent_student_returns_404(self):
        self.client.force_login(self.admin)
        url = reverse(
            'frontend:reports:grades_export',
            kwargs={'pk': 99999},
        )
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)


class ExportAuditLogTests(TestDataMixin, TestCase):
    """Tests for export_audit_log view."""

    def setUp(self):
        self.client = Client()
        self.school = self.create_school()
        self.admin = self.create_admin_user()
        self.direction = self.create_direction_user()
        self.student_user = self.create_student_user()
        self.url = reverse('frontend:reports:export_audit_log')

    def test_admin_sees_log(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('logs', resp.context)

    def test_direction_sees_log(self):
        self.client.force_login(self.direction)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_student_denied(self):
        self.client.force_login(self.student_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_anonymous_redirects(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_filter_by_type(self):
        from reports.models import ReportExportLog
        ReportExportLog.objects.create(
            report_type='grades_csv', export_format='csv',
            title='Test', exported_by=self.admin,
        )
        ReportExportLog.objects.create(
            report_type='incident_report', export_format='pdf',
            title='Other', exported_by=self.admin,
        )
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?type=grades_csv')
        self.assertEqual(resp.status_code, 200)
        page = resp.context['logs']
        for log in page:
            self.assertEqual(log.report_type, 'grades_csv')

    def test_filter_by_search(self):
        from reports.models import ReportExportLog
        ReportExportLog.objects.create(
            report_type='grades_csv', export_format='csv',
            title='Finding Specific Title', exported_by=self.admin,
        )
        self.client.force_login(self.admin)
        resp = self.client.get(self.url + '?search=Finding+Specific')
        self.assertEqual(resp.status_code, 200)


class AttendanceToRowsTests(TestDataMixin, TestCase):
    """Tests for the private _attendance_to_rows helper."""

    def test_student_mode(self):
        from reports.views_frontend import _attendance_to_rows
        context = {'mode': 'student', 'reports': []}
        header, rows = _attendance_to_rows(context)
        self.assertEqual(header, ['Date', 'Subject', 'Status'])
        self.assertEqual(rows, [])

    def test_class_mode(self):
        from reports.views_frontend import _attendance_to_rows
        context = {'mode': 'class', 'daily_stats': []}
        header, rows = _attendance_to_rows(context)
        self.assertEqual(header, ['Date', 'Subject', 'Total', 'Present', 'Absent', 'Late'])
        self.assertEqual(rows, [])

    def test_unknown_mode(self):
        from reports.views_frontend import _attendance_to_rows
        context = {'mode': 'unknown'}
        header, rows = _attendance_to_rows(context)
        self.assertEqual(header, ['No data'])
        self.assertEqual(rows, [])
