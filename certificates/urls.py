"""
URL configuration for certificates app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CertificateTemplateViewSet, CertificateViewSet,
    CertificateVerificationViewSet, BatchCertificateGenerationViewSet
)

app_name = 'certificates'

router = DefaultRouter()
router.register(r'templates', CertificateTemplateViewSet, basename='template')
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'verifications', CertificateVerificationViewSet, basename='verification')
router.register(r'batch', BatchCertificateGenerationViewSet, basename='batch')

urlpatterns = [
    path('', include(router.urls)),
]
