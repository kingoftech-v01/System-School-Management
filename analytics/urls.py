"""
URL configuration for analytics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentEngagementViewSet, CourseCompletionViewSet,
    LearningOutcomeViewSet, OutcomeMeasurementViewSet,
    ActivityLogViewSet, AtRiskStudentViewSet,
    AnalyticsDashboardViewSet
)

app_name = 'analytics'

router = DefaultRouter()
router.register(r'engagement', StudentEngagementViewSet, basename='engagement')
router.register(r'completion', CourseCompletionViewSet, basename='completion')
router.register(r'outcomes', LearningOutcomeViewSet, basename='outcome')
router.register(r'measurements', OutcomeMeasurementViewSet, basename='measurement')
router.register(r'activity-logs', ActivityLogViewSet, basename='activity-log')
router.register(r'at-risk', AtRiskStudentViewSet, basename='at-risk')
router.register(r'dashboards', AnalyticsDashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
