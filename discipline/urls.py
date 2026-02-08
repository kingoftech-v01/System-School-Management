"""
Discipline URLs - Frontend and API routing.

This module configures URL patterns for:
- Frontend HTML views (views_frontend.py)
- REST API endpoints (views_api.py with DRF)

URL Namespaces:
- Frontend: frontend:discipline:view_name
- API: api:v1:discipline:resource-name
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
    r'actions',
    views_api.DisciplinaryActionViewSet,
    basename='action'
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
        views_frontend.disciplinary_action_list,
        name='action_list'
    ),

    # Create view
    path(
        'create/',
        views_frontend.disciplinary_action_create,
        name='action_create'
    ),

    # Detail view
    path(
        '<int:pk>/',
        views_frontend.disciplinary_action_detail,
        name='action_detail'
    ),

    # Edit view
    path(
        '<int:pk>/edit/',
        views_frontend.disciplinary_action_edit,
        name='action_edit'
    ),

    # Delete view
    path(
        '<int:pk>/delete/',
        views_frontend.disciplinary_action_delete,
        name='action_delete'
    ),

    # Resolve view
    path(
        '<int:pk>/resolve/',
        views_frontend.disciplinary_action_resolve,
        name='action_resolve'
    ),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    # API URLs: /api/v1/discipline/
    path('api/', include((api_urlpatterns, 'api'))),

    # Frontend URLs: /discipline/
    path('', include((frontend_urlpatterns, 'frontend'))),
]
