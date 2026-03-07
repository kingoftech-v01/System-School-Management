"""
Monitoring URLs - API-only routing.

URL Namespaces:
- API: api:v1:monitoring:endpoint-name
"""

from django.urls import path, include

from . import views_api


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
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
