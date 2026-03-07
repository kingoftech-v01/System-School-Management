"""
Search URLs - API-only routing.

URL Namespaces:
- API: api:v1:search:resource-name
"""

from django.urls import path, include

from . import views_api


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    # Unified search endpoint
    path('query/', views_api.SearchAPIView.as_view(), name='query'),

    # Search suggestions/autocomplete
    path('suggestions/', views_api.SearchSuggestionsAPIView.as_view(), name='suggestions'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
