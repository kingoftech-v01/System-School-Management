"""
Attendance URLs - API-only routing.

URL Namespaces:
- API: api:v1:attendance:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

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
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
