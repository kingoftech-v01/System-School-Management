"""
URL configuration for forums app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ForumCategoryViewSet, ThreadViewSet, PostViewSet,
    TagViewSet, ThreadSubscriptionViewSet, ReportViewSet
)

app_name = 'forums'

router = DefaultRouter()
router.register(r'categories', ForumCategoryViewSet, basename='category')
router.register(r'threads', ThreadViewSet, basename='thread')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'subscriptions', ThreadSubscriptionViewSet, basename='subscription')
router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
