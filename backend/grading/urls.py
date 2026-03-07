"""
Grading URLs - API-only routing.

URL Namespaces:
- API: api:v1:grading:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

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
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
