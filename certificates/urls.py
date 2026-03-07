"""
Certificates URLs - API-only routing.

URL Namespaces:
- API: api:v1:certificates:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'templates', views_api.CertificateTemplateViewSet, basename='template')
api_router.register(r'certificates', views_api.CertificateViewSet, basename='certificate')
api_router.register(r'verifications', views_api.CertificateVerificationViewSet, basename='verification')
api_router.register(r'batch', views_api.BatchCertificateGenerationViewSet, basename='batch')


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
