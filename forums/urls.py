"""
Forums URLs - API-only routing.

URL Namespaces:
- API: api:v1:forums:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'categories', views_api.ForumCategoryViewSet, basename='category')
api_router.register(r'threads', views_api.ThreadViewSet, basename='thread')
api_router.register(r'posts', views_api.PostViewSet, basename='post')
api_router.register(r'tags', views_api.TagViewSet, basename='tag')
api_router.register(r'subscriptions', views_api.ThreadSubscriptionViewSet, basename='subscription')
api_router.register(r'reports', views_api.ReportViewSet, basename='report')


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
