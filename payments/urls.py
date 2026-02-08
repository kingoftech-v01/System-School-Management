"""
Payments URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:payments:view_name
- API: api:v1:payments:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
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
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    path("", views_frontend.PaymentGetwaysView.as_view(), name="payment_gateways"),
    path("paypal/", views_frontend.payment_paypal, name="paypal"),
    path("stripe/", views_frontend.payment_stripe, name="stripe"),
    path("coinbase/", views_frontend.payment_coinbase, name="coinbase"),
    path("paylike/", views_frontend.payment_paylike, name="paylike"),
    path("stripe-charge/", views_frontend.stripe_charge, name="stripe_charge"),
    path("gopay-charge/", views_frontend.gopay_charge, name="gopay_charge"),
    path("payment-succeed/", views_frontend.payment_succeed, name="payment_succeed"),
    path("complete/", views_frontend.paymentComplete, name="complete"),
    path("completed/", views_frontend.payment_succeed, name="completed"),  # Alias for completed
    path("create-invoice/", views_frontend.create_invoice, name="create_invoice"),
    path("invoice-detail/<int:id>/", views_frontend.invoice_detail, name="invoice_detail"),

    # Fee Structure CRUD
    path("fee-structures/", views_frontend.fee_structure_list, name="fee_structure_list"),
    path("fee-structures/create/", views_frontend.fee_structure_create, name="fee_structure_create"),
    path("fee-structures/<int:pk>/edit/", views_frontend.fee_structure_edit, name="fee_structure_edit"),
    path("fee-structures/<int:pk>/delete/", views_frontend.fee_structure_delete, name="fee_structure_delete"),

    # Student views
    path("my-invoices/", views_frontend.student_invoices, name="student_invoices"),
    path("my-payments/", views_frontend.student_payment_history, name="student_payment_history"),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
