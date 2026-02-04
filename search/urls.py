"""
Search URLs - Frontend and API routing.

This module configures URL patterns for:
- Frontend HTML views (views_frontend.py)
- REST API endpoints (views_api.py)

URL Namespaces:
- Frontend: frontend:search:view_name
- API: api:v1:search:resource-name
"""

from django.urls import path, include

from . import views_frontend
from . import views_api


# ============================================================================
# API URLPATTERNS (Non-ViewSet API views)
# ============================================================================

api_urlpatterns = [
    # Unified search endpoint
    path('query/', views_api.SearchAPIView.as_view(), name='query'),

    # Search suggestions/autocomplete
    path('suggestions/', views_api.SearchSuggestionsAPIView.as_view(), name='suggestions'),
]


# ============================================================================
# FRONTEND URLPATTERNS (HTML Template Views)
# ============================================================================

frontend_urlpatterns = [
    # Basic search view
    path('', views_frontend.SearchView.as_view(), name='query'),

    # Advanced search (optional - for future implementation)
    # path('advanced/', views_frontend.AdvancedSearchView.as_view(), name='advanced'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    # API URLs: /api/v1/search/
    path('api/', include((api_urlpatterns, 'api'))),

    # Frontend URLs: /search/
    path('', include((frontend_urlpatterns, 'frontend'))),
]
