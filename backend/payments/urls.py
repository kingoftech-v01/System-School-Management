"""
Payments URLs - API-only routing.

URL Namespaces:
- API: api:v1:payments:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'fee-structures', views_api.FeeStructureViewSet, basename='fee-structure')
api_router.register(r'invoices', views_api.InvoiceViewSet, basename='invoice')
api_router.register(r'payment-plans', views_api.PaymentPlanViewSet, basename='payment-plan')
api_router.register(r'installments', views_api.InstallmentViewSet, basename='installment')
api_router.register(r'payments', views_api.PaymentViewSet, basename='payment')
api_router.register(r'verifications', views_api.PaymentVerificationViewSet, basename='verification')
api_router.register(r'receipts', views_api.ReceiptViewSet, basename='receipt')


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
