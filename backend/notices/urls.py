"""
Notices URLs - API-only routing.

URL Namespaces:
- API: api:v1:notices:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

# API ROUTER
api_router = DefaultRouter()
api_router.register(r'notices', views_api.NoticeViewSet, basename='notice')

# API URLPATTERNS
api_urlpatterns = [
    path('', include(api_router.urls)),
]

# APP URL CONFIGURATION
app_name = 'notices'

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
