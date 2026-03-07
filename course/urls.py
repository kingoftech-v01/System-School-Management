"""
Course URLs - API-only routing.

URL Namespaces:
- API: api:v1:course:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'programs', views_api.ProgramViewSet, basename='program')
api_router.register(r'courses', views_api.CourseViewSet, basename='course')
api_router.register(r'allocations', views_api.CourseAllocationViewSet, basename='allocation')
api_router.register(r'uploads', views_api.UploadViewSet, basename='upload')
api_router.register(r'videos', views_api.UploadVideoViewSet, basename='video')
api_router.register(r'registration', views_api.CourseRegistrationViewSet, basename='registration')


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
