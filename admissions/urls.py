"""
Admissions URLs - API-only routing.

URL Namespaces:
- API: api:v1:admissions:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

api_router = DefaultRouter()
api_router.register(r'sessions', views_api.AdmissionSessionViewSet, basename='session')
api_router.register(r'applications', views_api.AdmissionStudentViewSet, basename='application')

api_urlpatterns = [path('', include(api_router.urls))]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
