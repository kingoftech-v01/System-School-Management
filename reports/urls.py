from django.urls import path

from . import views_frontend

frontend_urlpatterns = [
    path(
        'student/<int:pk>/complete-record/',
        views_frontend.student_complete_record,
        name='student_complete_record',
    ),
    path(
        'incident/<int:pk>/pdf/',
        views_frontend.incident_report_pdf,
        name='incident_report_pdf',
    ),
    path(
        'attendance/',
        views_frontend.attendance_report,
        name='attendance_report',
    ),
    path(
        'discipline/<int:pk>/pdf/',
        views_frontend.discipline_history_pdf,
        name='discipline_history_pdf',
    ),
    path(
        'grades/<int:pk>/export/',
        views_frontend.grades_export,
        name='grades_export',
    ),
    path(
        'audit-log/',
        views_frontend.export_audit_log,
        name='export_audit_log',
    ),
]

# No API endpoints for reports — all exports are frontend-only
api_urlpatterns = []
