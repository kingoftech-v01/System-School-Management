"""
Scheduling URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:scheduling:view_name
- API: api:v1:scheduling:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'rooms', views_api.RoomViewSet, basename='room')
api_router.register(r'timeslots', views_api.TimeSlotViewSet, basename='timeslot')
api_router.register(r'entries', views_api.ScheduleEntryViewSet, basename='scheduleentry')
api_router.register(r'exceptions', views_api.ScheduleExceptionViewSet, basename='scheduleexception')
api_router.register(r'substitutions', views_api.SubstitutionRequestViewSet, basename='substitutionrequest')
api_router.register(r'notifications', views_api.ScheduleNotificationViewSet, basename='schedulenotification')
api_router.register(r'generations', views_api.TimetableGenerationViewSet, basename='timetablegeneration')


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
]


# ============================================================================
# FRONTEND URLPATTERNS (HTML Template Views)
# ============================================================================

frontend_urlpatterns = [
    # ---- Calendar views (all roles) ----
    path('calendar/', views_frontend.schedule_calendar, name='schedule_calendar'),
    path('my/', views_frontend.my_schedule, name='my_schedule'),

    # ---- Professor views ----
    path('professor/', views_frontend.professor_schedule, name='professor_schedule'),
    path(
        'professor/cancel/<int:entry_id>/',
        views_frontend.mark_cancellation,
        name='mark_cancellation',
    ),
    path(
        'professor/substitute/<int:entry_id>/',
        views_frontend.request_substitution,
        name='request_substitution',
    ),
    path(
        'professor/substitutions/',
        views_frontend.my_substitution_requests,
        name='my_substitution_requests',
    ),

    # ---- Parent view ----
    path('parent/', views_frontend.parent_child_schedule, name='parent_child_timetable'),

    # ---- Room management (direction/admin) ----
    path('rooms/', views_frontend.room_list, name='room_list'),
    path('rooms/create/', views_frontend.room_create, name='room_create'),
    path('rooms/<int:pk>/', views_frontend.room_detail, name='room_detail'),
    path('rooms/<int:pk>/edit/', views_frontend.room_edit, name='room_edit'),
    path('rooms/<int:pk>/delete/', views_frontend.room_delete, name='room_delete'),

    # ---- Time slot configuration (direction/admin) ----
    path('timeslots/', views_frontend.timeslot_config, name='timeslot_config'),
    path('timeslots/create/', views_frontend.timeslot_create, name='timeslot_create'),
    path('timeslots/<int:pk>/edit/', views_frontend.timeslot_edit, name='timeslot_edit'),
    path('timeslots/<int:pk>/delete/', views_frontend.timeslot_delete, name='timeslot_delete'),

    # ---- Schedule editor (direction/admin) ----
    path('editor/', views_frontend.schedule_editor, name='schedule_editor'),

    # ---- Schedule entries CRUD ----
    path('entries/create/', views_frontend.schedule_entry_create, name='schedule_entry_create'),
    path('entries/<int:pk>/edit/', views_frontend.schedule_entry_edit, name='schedule_entry_edit'),
    path('entries/<int:pk>/delete/', views_frontend.schedule_entry_delete, name='schedule_entry_delete'),

    # ---- Auto-generation wizard (direction/admin) ----
    path('wizard/', views_frontend.timetable_wizard_step1, name='timetable_wizard_step1'),
    path('wizard/step2/', views_frontend.timetable_wizard_step2, name='timetable_wizard_step2'),
    path('wizard/step3/', views_frontend.timetable_wizard_step3, name='timetable_wizard_step3'),
    path('wizard/generate/', views_frontend.timetable_wizard_generate, name='timetable_wizard_generate'),
    path(
        'wizard/results/<int:gen_id>/',
        views_frontend.timetable_wizard_results,
        name='timetable_wizard_results',
    ),

    # ---- Conflicts (direction/admin) ----
    path('conflicts/', views_frontend.conflict_list, name='conflict_list'),
    path('conflicts/<int:pk>/resolve/', views_frontend.conflict_resolve, name='conflict_resolve'),

    # ---- Reports (direction/admin) ----
    path('reports/utilization/', views_frontend.room_utilization_report, name='room_utilization_report'),
    path('export/pdf/', views_frontend.export_timetable_pdf, name='export_timetable_pdf'),

    # ---- Substitution management (direction/admin) ----
    path('substitutions/', views_frontend.substitution_list, name='substitution_list'),
    path(
        'substitutions/<int:pk>/review/',
        views_frontend.substitution_review,
        name='substitution_review',
    ),

    # ---- Exceptions (direction/admin) ----
    path('exceptions/', views_frontend.exception_list, name='exception_list'),
    path('exceptions/create/', views_frontend.exception_create, name='exception_create'),

    # ---- Notifications ----
    path('notifications/', views_frontend.notification_list, name='notification_list'),
    path(
        'notifications/<int:pk>/read/',
        views_frontend.notification_mark_read,
        name='notification_mark_read',
    ),
    path(
        'notifications/mark-all-read/',
        views_frontend.notification_mark_all_read,
        name='notification_mark_all_read',
    ),
]
