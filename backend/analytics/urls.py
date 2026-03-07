"""
Analytics URLs - API-only routing.

URL Namespaces:
- API: api:v1:analytics:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'engagement', views_api.StudentEngagementViewSet, basename='engagement')
api_router.register(r'completion', views_api.CourseCompletionViewSet, basename='completion')
api_router.register(r'outcomes', views_api.LearningOutcomeViewSet, basename='outcome')
api_router.register(r'measurements', views_api.OutcomeMeasurementViewSet, basename='measurement')
api_router.register(r'activity-logs', views_api.ActivityLogViewSet, basename='activity-log')
api_router.register(r'at-risk', views_api.AtRiskStudentViewSet, basename='at-risk')
api_router.register(r'dashboards', views_api.AnalyticsDashboardViewSet, basename='dashboard')


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
