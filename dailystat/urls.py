"""
Daily Stats URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:dailystat:view_name
- API: api:v1:dailystat:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'stats', views_api.DailyAttendanceStatViewSet, basename='stat')


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
    path('', views_frontend.daily_stats_dashboard, name='dashboard'),
    path('today/', views_frontend.today_stats, name='today_stats'),
    path('date/', views_frontend.date_stats, name='date_stats'),
    path('trends/', views_frontend.attendance_trends, name='trends'),
    path('export/csv/', views_frontend.export_csv, name='export_csv'),
    path('export/pdf/', views_frontend.export_pdf, name='export_pdf'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
