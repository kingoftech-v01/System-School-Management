"""
Safeguarding URLs - API-only routing.

URL Namespaces:
- API: api:v1:safeguarding:resource-name
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views_api

# API Router
api_router = DefaultRouter()
api_router.register(r'incidents', views_api.IncidentViewSet, basename='incident')
api_router.register(r'visitors', views_api.VisitorLogViewSet, basename='visitor')
api_router.register(
    r'case-notes', views_api.StudentCaseNoteViewSet, basename='case-note'
)

api_urlpatterns = [
    path('', include(api_router.urls)),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
