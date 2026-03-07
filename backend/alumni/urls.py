"""
Alumni URLs - API-only routing.

URL Namespaces:
- API: api:v1:alumni:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

api_router = DefaultRouter()
api_router.register(r'alumni', views_api.AlumniViewSet, basename='alumni')
api_router.register(r'events', views_api.AlumniEventViewSet, basename='event')

api_urlpatterns = [path('', include(api_router.urls))]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
