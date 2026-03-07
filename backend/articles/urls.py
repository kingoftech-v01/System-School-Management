"""
Articles URLs - API-only routing.

URL Namespaces:
- API: api:v1:articles:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

api_router = DefaultRouter()
api_router.register(r'articles', views_api.ArticleViewSet, basename='article')
api_router.register(r'categories', views_api.CategoryViewSet, basename='category')

api_urlpatterns = [path('', include(api_router.urls))]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
