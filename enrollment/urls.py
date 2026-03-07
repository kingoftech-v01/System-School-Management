"""
Enrollment URLs - API-only routing.

URL Namespaces:
- API: api:v1:enrollment:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'registrations', views_api.RegistrationFormViewSet, basename='registration')
api_router.register(r'documents', views_api.EnrollmentDocumentViewSet, basename='document')
api_router.register(r'history', views_api.EnrollmentStatusHistoryViewSet, basename='history')


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
