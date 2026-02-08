"""
Result URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:result:view_name
- API: api:v1:result:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'taken-courses', views_api.TakenCourseViewSet, basename='taken-course')
api_router.register(r'results', views_api.ResultViewSet, basename='result')
api_router.register(r'grade-weights', views_api.GradeComponentWeightViewSet, basename='grade-weight')
api_router.register(r'appeals', views_api.GradeAppealViewSet, basename='appeal')
api_router.register(r'grade-history', views_api.GradeHistoryViewSet, basename='grade-history')
api_router.register(r'transcripts', views_api.TranscriptViewSet, basename='transcript')


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
    # Score management
    path('manage-score/', views_frontend.add_score, name='add_score'),
    path('manage-score/<int:id>/', views_frontend.add_score_for, name='add_score_for'),

    # Results views
    path('grade/', views_frontend.grade_result, name='grade_results'),
    path('assessment/', views_frontend.assessment_result, name='ass_results'),

    # PDF generation
    path('result/print/<int:id>/', views_frontend.result_sheet_pdf_view, name='result_sheet_pdf_view'),

    # Registration form
    path('registration/form/', views_frontend.course_registration_form, name='course_registration_form'),

    # Grade Appeals
    path('appeals/', views_frontend.grade_appeal_list, name='grade_appeal_list'),
    path('appeals/<int:pk>/', views_frontend.grade_appeal_detail, name='grade_appeal_detail'),
    path('appeals/create/<int:taken_course_id>/', views_frontend.grade_appeal_create, name='grade_appeal_create'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
