"""
Enrollment URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:enrollment:view_name
- API: api:v1:enrollment:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
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
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Public registration URLs
    path('register/step1/', views_frontend.register_step1, name='register_step1'),
    path('register/step2/', views_frontend.register_step2, name='register_step2'),
    path('register/step3/', views_frontend.register_step3, name='register_step3'),
    path('register/step4/', views_frontend.register_step4, name='register_step4'),
    path('register/complete/<str:signed_id>/', views_frontend.register_complete, name='register_complete'),
    path('register/<int:registration_id>/upload/', views_frontend.upload_document, name='upload_document'),

    # Parent-authenticated enrollment (3-step wizard)
    path('parent/enroll/step1/', views_frontend.parent_enroll_step1, name='parent_enroll_step1'),
    path('parent/enroll/step2/', views_frontend.parent_enroll_step2, name='parent_enroll_step2'),
    path('parent/enroll/step3/', views_frontend.parent_enroll_step3, name='parent_enroll_step3'),

    # Direction/Admin URLs
    path('list/', views_frontend.enrollment_list, name='enrollment_list'),
    path('detail/<int:registration_id>/', views_frontend.enrollment_detail, name='enrollment_detail'),
    path('review/<int:registration_id>/', views_frontend.enrollment_review, name='enrollment_review'),
    path('edit/<int:registration_id>/', views_frontend.registration_edit, name='registration_edit'),
    path('delete/<int:registration_id>/', views_frontend.registration_delete, name='registration_delete'),
    path('document/<int:document_id>/verify/', views_frontend.verify_document, name='verify_document'),
    path('document/<int:document_id>/delete/', views_frontend.document_delete, name='document_delete'),
    path('export/csv/', views_frontend.export_enrollments_csv, name='export_enrollments_csv'),
    path('statistics/', views_frontend.enrollment_statistics, name='enrollment_statistics'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
