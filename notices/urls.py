"""
Notices URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:notices:view_name
- API: api:v1:notices:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api

# API ROUTER
api_router = DefaultRouter()
api_router.register(r'notices', views_api.NoticeViewSet, basename='notice')

# API URLPATTERNS
api_urlpatterns = [
    path('', include(api_router.urls)),
]

# FRONTEND URLPATTERNS
frontend_urlpatterns = [
    path('', views_frontend.notice_list, name='notice_list'),
    path('create/', views_frontend.notice_create, name='notice_create'),
    path('<int:pk>/', views_frontend.notice_detail, name='notice_detail'),
    path('<int:pk>/edit/', views_frontend.notice_update, name='notice_update'),
    path('<int:pk>/delete/', views_frontend.notice_delete, name='notice_delete'),
    path('<int:pk>/respond/', views_frontend.notice_respond, name='notice_respond'),
]

# APP URL CONFIGURATION
app_name = 'notices'

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
