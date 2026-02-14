"""
Monitoring URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:monitoring:view_name
- API: api:v1:monitoring:endpoint-name
"""

from django.urls import path, include

from . import views_frontend
from . import views_api
from . import views_superadmin


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('dashboard/', views_api.DashboardStatsAPIView.as_view(), name='dashboard-stats'),
    path('enrollment/', views_api.EnrollmentStatsAPIView.as_view(), name='enrollment-stats'),
    path('library/', views_api.LibraryStatsAPIView.as_view(), name='library-stats'),
    path('export/', views_api.ExportDashboardAPIView.as_view(), name='export-dashboard'),
]


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    path('', views_frontend.monitoring_dashboard, name='dashboard'),
    path('enrollment-stats/', views_frontend.enrollment_statistics, name='enrollment_stats'),
    path('library-stats/', views_frontend.library_statistics, name='library_stats'),
    path('export/csv/', views_frontend.export_dashboard_csv, name='export_csv'),
    path('tenants/', views_superadmin.tenant_comparison, name='tenant_comparison'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
