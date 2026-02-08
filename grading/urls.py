"""
Grading URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:grading:view_name
- API: api:v1:grading:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'rubrics', views_api.GradingRubricViewSet, basename='rubric')
api_router.register(r'criteria', views_api.RubricCriterionViewSet, basename='criterion')
api_router.register(r'grades', views_api.RubricGradeViewSet, basename='grade')
api_router.register(r'criterion-grades', views_api.CriterionGradeViewSet, basename='criterion-grade')
api_router.register(r'peer-reviews', views_api.PeerReviewViewSet, basename='peer-review')
api_router.register(r'curves', views_api.GradeCurveViewSet, basename='curve')


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
    path('', views_frontend.grading_dashboard, name='dashboard'),

    # Rubric management
    path('rubrics/', views_frontend.rubric_list, name='rubric_list'),
    path('rubrics/create/', views_frontend.rubric_create, name='rubric_create'),
    path('rubrics/<int:pk>/', views_frontend.rubric_detail, name='rubric_detail'),
    path('rubrics/<int:pk>/edit/', views_frontend.rubric_update, name='rubric_update'),
    path('rubrics/<int:pk>/delete/', views_frontend.rubric_delete, name='rubric_delete'),

    # Rubric criteria
    path('rubrics/<int:rubric_pk>/criteria/create/', views_frontend.criterion_create, name='criterion_create'),
    path('criteria/<int:pk>/edit/', views_frontend.criterion_update, name='criterion_update'),
    path('criteria/<int:pk>/delete/', views_frontend.criterion_delete, name='criterion_delete'),

    # Grade entry
    path('grades/', views_frontend.grade_entry_list, name='grade_entry_list'),
    path('grades/create/', views_frontend.grade_entry_create, name='grade_entry_create'),
    path('grades/create/<int:rubric_pk>/', views_frontend.grade_entry_create, name='grade_entry_create_with_rubric'),
    path('grades/create/<int:rubric_pk>/<int:student_id>/', views_frontend.grade_entry_create, name='grade_entry_create_full'),
    path('grades/<int:pk>/', views_frontend.grade_entry_detail, name='grade_entry_detail'),
    path('grades/<int:pk>/edit/', views_frontend.grade_entry_edit, name='grade_entry_edit'),
    path('grades/<int:pk>/delete/', views_frontend.grade_entry_delete, name='grade_entry_delete'),

    # Student gradebook
    path('gradebook/', views_frontend.student_gradebook, name='student_gradebook'),
    path('gradebook/<int:student_id>/', views_frontend.student_gradebook, name='student_gradebook_detail'),

    # Peer reviews
    path('peer-reviews/', views_frontend.peer_review_list, name='peer_review_list'),
    path('peer-reviews/<int:pk>/submit/', views_frontend.peer_review_submit, name='peer_review_submit'),

    # Grade curves
    path('curves/', views_frontend.grade_curve_list, name='grade_curve_list'),
    path('curves/create/', views_frontend.grade_curve_create, name='grade_curve_create'),
    path('curves/<int:pk>/', views_frontend.grade_curve_detail, name='grade_curve_detail'),
    path('curves/<int:pk>/edit/', views_frontend.grade_curve_edit, name='grade_curve_edit'),
    path('curves/<int:pk>/delete/', views_frontend.grade_curve_delete, name='grade_curve_delete'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
