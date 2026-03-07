"""
Filieres URLs - API-only routing.

URL Namespaces:
- API: api:v1:filieres:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'filieres', views_api.FiliereViewSet, basename='filiere')
api_router.register(r'subjects', views_api.FiliereSubjectViewSet, basename='subject')
api_router.register(r'requirements', views_api.FiliereRequirementViewSet, basename='requirement')


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
