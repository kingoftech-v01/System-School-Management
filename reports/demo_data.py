"""Demo data generator for reports app: ReportExportLog."""

import random

from .models import ReportExportLog


REPORT_ENTRIES = [
    ('student_complete_record', 'pdf', 'Student Complete Record - John Doe'),
    ('incident_report', 'pdf', 'Incident Report #1024'),
    ('visitor_log', 'pdf', 'Visitor Log - January 2026'),
    ('attendance_report', 'pdf', 'Attendance Report - CS Year 1'),
    ('discipline_history', 'pdf', 'Discipline History - All Students'),
    ('attendance_csv', 'csv', 'Attendance Export - Fall 2025'),
    ('attendance_xlsx', 'xlsx', 'Attendance Export - Spring 2026'),
    ('grades_csv', 'csv', 'Grades Export - Computer Science'),
    ('grades_xlsx', 'xlsx', 'Grades Export - All Programs'),
    ('student_complete_record', 'pdf', 'Student Record - Jane Smith'),
    ('incident_report', 'pdf', 'Incident Report #1025'),
    ('attendance_report', 'pdf', 'Attendance Summary - February 2026'),
    ('grades_csv', 'csv', 'Final Grades Export - Fall 2025'),
    ('visitor_log', 'xlsx', 'Visitor Log - February 2026'),
    ('discipline_history', 'pdf', 'Discipline Summary - Q1 2026'),
]


def generate(tenant=None, stdout=None, verbosity=1, context=None, fake=None):
    staff = context['accounts']['staff_users']
    professors = context['accounts']['professors']
    exporters = professors + staff
    total = 0

    logs = []
    for report_type, fmt, title in REPORT_ENTRIES:
        log = ReportExportLog.objects.create(
            report_type=report_type,
            export_format=fmt,
            title=title,
            exported_by=random.choice(exporters),
            export_reason=fake.sentence() if random.random() < 0.4 else '',
            student_id=random.randint(1, 150) if 'student' in report_type else None,
            incident_id=random.randint(1, 10) if 'incident' in report_type else None,
            filter_params={'date_range': 'last_30_days'} if random.random() < 0.5 else {},
            ip_address=fake.ipv4(),
            user_agent=fake.user_agent(),
            tenant=tenant,
        )
        logs.append(log)
    total += len(logs)

    if stdout and verbosity >= 1:
        stdout.write(f'  [reports] Created {total} records')

    return {'_total': total}
