"""
Certificates URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:certificates:view_name
- API: api:v1:certificates:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
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
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Dashboard
    path('', views_frontend.certificates_dashboard, name='dashboard'),

    # Certificate templates
    path('templates/', views_frontend.template_list, name='template_list'),
    path('templates/create/', views_frontend.template_create, name='template_create'),
    path('templates/<int:pk>/', views_frontend.template_detail, name='template_detail'),
    path('templates/<int:pk>/edit/', views_frontend.template_update, name='template_update'),
    path('templates/<int:pk>/delete/', views_frontend.template_delete, name='template_delete'),

    # Certificates
    path('certificates/', views_frontend.certificate_list, name='certificate_list'),
    path('certificates/create/', views_frontend.certificate_create, name='certificate_create'),
    path('certificates/<int:pk>/', views_frontend.certificate_detail, name='certificate_detail'),
    path('certificates/<int:pk>/download/', views_frontend.certificate_download, name='certificate_download'),
    path('certificates/<int:pk>/revoke/', views_frontend.certificate_revoke, name='certificate_revoke'),

    # Public verification (no login required)
    path('verify/', views_frontend.certificate_verify, name='certificate_verify'),

    # Batch generation
    path('batch/', views_frontend.batch_generation_list, name='batch_generation_list'),
    path('batch/create/', views_frontend.batch_generation_create, name='batch_generation_create'),
    path('batch/<int:pk>/', views_frontend.batch_generation_detail, name='batch_generation_detail'),
    path('batch/<int:pk>/start/', views_frontend.batch_generation_start, name='batch_generation_start'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

app_name = 'certificates'

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
