"""
Quiz URLs - API-only routing.

URL Namespaces:
- API: api:v1:quiz:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'quizzes', views_api.QuizViewSet, basename='quiz')
api_router.register(r'mc-questions', views_api.MCQuestionViewSet, basename='mc-question')
api_router.register(r'essay-questions', views_api.EssayQuestionViewSet, basename='essay-question')
api_router.register(r'sittings', views_api.SittingViewSet, basename='sitting')
api_router.register(r'progress', views_api.ProgressViewSet, basename='progress')


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
