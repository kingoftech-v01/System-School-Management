"""
Accounts URLs - API routing.

URL Namespaces:
- API: api:v1:accounts:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'users', views_api.UserViewSet, basename='user')
api_router.register(r'students', views_api.StudentViewSet, basename='student')
api_router.register(r'lecturers', views_api.LecturerViewSet, basename='lecturer')
api_router.register(r'staff', views_api.StaffViewSet, basename='staff')


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
    # Auth endpoints
    path('auth/login/', views_api.LoginAPIView.as_view(), name='login'),
    path('auth/logout/', views_api.LogoutAPIView.as_view(), name='logout'),
    # Context endpoints (replaces template context processors)
    path('navigation/', views_api.NavigationAPIView.as_view(), name='navigation'),
    path('permissions/', views_api.PermissionsAPIView.as_view(), name='permissions'),
    # Utility endpoints
    path('validate-username/', views_api.ValidateUsernameAPIView.as_view(), name='validate-username'),
    path('2fa/setup/', views_api.Setup2FAAPIView.as_view(), name='2fa-setup'),
    path('2fa/disable/', views_api.Disable2FAAPIView.as_view(), name='2fa-disable'),
]


# ============================================================================
# APP URL CONFIGURATION (API only)
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
