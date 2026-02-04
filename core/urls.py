"""
Core URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:core:view_name
- API: api:v1:core:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'sessions', views_api.SessionViewSet, basename='session')
api_router.register(r'semesters', views_api.SemesterViewSet, basename='semester')
api_router.register(r'news-events', views_api.NewsAndEventsViewSet, basename='news-event')
api_router.register(r'activity-logs', views_api.ActivityLogViewSet, basename='activity-log')


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
]


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Dashboard
    path('', views_frontend.home_view, name='home'),
    path('dashboard/', views_frontend.unified_dashboard, name='dashboard'),
    path('dashboard/old/', views_frontend.dashboard_view, name='dashboard_old'),

    # News & Events
    path('add_item/', views_frontend.post_add, name='add_item'),
    path('item/<int:pk>/edit/', views_frontend.edit_post, name='edit_post'),
    path('item/<int:pk>/delete/', views_frontend.delete_post, name='delete_post'),

    # Sessions
    path('session/', views_frontend.session_list_view, name='session_list'),
    path('session/add/', views_frontend.session_add_view, name='add_session'),
    path('session/<int:pk>/edit/', views_frontend.session_update_view, name='edit_session'),
    path('session/<int:pk>/delete/', views_frontend.session_delete_view, name='delete_session'),

    # Semesters
    path('semester/', views_frontend.semester_list_view, name='semester_list'),
    path('semester/add/', views_frontend.semester_add_view, name='add_semester'),
    path('semester/<int:pk>/edit/', views_frontend.semester_update_view, name='edit_semester'),
    path('semester/<int:pk>/delete/', views_frontend.semester_delete_view, name='delete_semester'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
