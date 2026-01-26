"""
Analytics URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:analytics:view_name
- API: api:v1:analytics:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
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
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Dashboard
    path('', views_frontend.analytics_dashboard, name='analytics_dashboard'),

    # Student engagement
    path('engagement/', views_frontend.engagement_list, name='engagement_list'),
    path('engagement/<int:student_id>/', views_frontend.engagement_detail, name='engagement_detail'),

    # Course completion
    path('completions/', views_frontend.completion_list, name='completion_list'),
    path('completions/<int:pk>/', views_frontend.completion_detail, name='completion_detail'),

    # Learning outcomes
    path('outcomes/', views_frontend.learning_outcome_list, name='learning_outcome_list'),
    path('outcomes/create/', views_frontend.learning_outcome_create, name='learning_outcome_create'),
    path('outcomes/<int:pk>/', views_frontend.learning_outcome_detail, name='learning_outcome_detail'),

    # At-risk students
    path('at-risk/', views_frontend.at_risk_list, name='at_risk_list'),
    path('at-risk/<int:pk>/', views_frontend.at_risk_detail, name='at_risk_detail'),
    path('at-risk/<int:pk>/intervene/', views_frontend.at_risk_intervene, name='at_risk_intervene'),

    # Activity logs
    path('activity-logs/', views_frontend.activity_log_list, name='activity_log_list'),

    # Reports
    path('reports/', views_frontend.analytics_reports, name='analytics_reports'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

app_name = 'analytics'

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
