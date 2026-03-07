"""
Result URLs - API-only routing.

URL Namespaces:
- API: api:v1:result:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

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
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
