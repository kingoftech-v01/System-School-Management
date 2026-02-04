"""
Events URLs - Frontend and API routing.

This module configures URL patterns for:
- Frontend HTML views (views_frontend.py)
- REST API endpoints (views_api.py with DRF)

URL Namespaces:
- Frontend: frontend:events:view_name
- API: api:v1:events:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(
    r'events',
    views_api.EventViewSet,
    basename='event'
)


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    # Include router URLs
    path('', include(api_router.urls)),
]


# ============================================================================
# FRONTEND URLPATTERNS (HTML Template Views)
# ============================================================================

frontend_urlpatterns = [
    # List view
    path(
        '',
        views_frontend.event_list,
        name='event_list'
    ),

    # Create view
    path(
        'create/',
        views_frontend.event_create,
        name='event_create'
    ),

    # Detail view
    path(
        '<int:pk>/',
        views_frontend.event_detail,
        name='event_detail'
    ),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    # API URLs: /api/v1/events/
    path('api/', include((api_urlpatterns, 'api'))),

    # Frontend URLs: /events/
    path('', include((frontend_urlpatterns, 'frontend'))),
]
