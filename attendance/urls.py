"""
Attendance URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:attendance:view_name
- API: api:v1:attendance:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'students', views_api.StudentViewSet, basename='student')
api_router.register(r'groups', views_api.GroupViewSet, basename='group')
api_router.register(r'subjects', views_api.SubjectViewSet, basename='subject')
api_router.register(r'attendances', views_api.AttendanceViewSet, basename='attendance')
api_router.register(r'reports', views_api.AttendanceReportViewSet, basename='report')


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
]


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Dashboard
    path('', views_frontend.attendance_dashboard, name='dashboard'),

    # Attendance taking
    path('take/', views_frontend.take_attendance, name='take_attendance'),
    path('<int:pk>/mark/', views_frontend.mark_attendance, name='mark_attendance'),
    path('<int:pk>/', views_frontend.attendance_detail, name='attendance_detail'),

    # Reports
    path('student/<int:student_id>/report/', views_frontend.student_attendance_report, name='student_report'),

    # Management
    path('students/', views_frontend.student_list, name='student_list'),
    path('groups/', views_frontend.group_list, name='group_list'),
    path('subjects/', views_frontend.subject_list, name='subject_list'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
