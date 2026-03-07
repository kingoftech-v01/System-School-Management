"""
Core URLs - API-only routing.

URL Namespaces:
- API: api:v1:core:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'sessions', views_api.SessionViewSet, basename='session')
api_router.register(r'semesters', views_api.SemesterViewSet, basename='semester')
api_router.register(r'news-events', views_api.NewsAndEventsViewSet, basename='news-event')
api_router.register(r'activity-logs', views_api.ActivityLogViewSet, basename='activity-log')


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
