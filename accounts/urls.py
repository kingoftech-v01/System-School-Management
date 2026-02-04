"""
Accounts URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:accounts:view_name
- API: api:v1:accounts:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
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
    # Custom API views
    path('validate-username/', views_api.ValidateUsernameAPIView.as_view(), name='validate-username'),
    path('2fa/setup/', views_api.Setup2FAAPIView.as_view(), name='2fa-setup'),
    path('2fa/disable/', views_api.Disable2FAAPIView.as_view(), name='2fa-disable'),
]


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Django auth URLs (login, logout, password reset)
    path('', include('django.contrib.auth.urls')),

    # Admin panel
    path('admin_panel/', views_frontend.admin_panel, name='admin_panel'),

    # Profile management
    path('profile/', views_frontend.profile, name='profile'),
    path('profile/<int:user_id>/detail/', views_frontend.profile_single, name='profile_single'),
    path('setting/', views_frontend.profile_update, name='edit_profile'),
    path('change_password/', views_frontend.change_password, name='change_password'),

    # Lecturer management
    path('lecturers/', views_frontend.LecturerFilterView.as_view(), name='lecturer_list'),
    path('lecturer/add/', views_frontend.staff_add_view, name='add_lecturer'),
    path('staff/<int:pk>/edit/', views_frontend.edit_staff, name='staff_edit'),
    path('lecturers/<int:pk>/delete/', views_frontend.delete_staff, name='lecturer_delete'),

    # Student management
    path('students/', views_frontend.StudentListView.as_view(), name='student_list'),
    path('student/add/', views_frontend.student_add_view, name='add_student'),
    path('student/<int:pk>/edit/', views_frontend.edit_student, name='student_edit'),
    path('students/<int:pk>/delete/', views_frontend.delete_student, name='student_delete'),
    path('edit_student_program/<int:pk>/', views_frontend.edit_student_program, name='student_program_edit'),

    # Parent management
    path('parents/add/', views_frontend.ParentAdd.as_view(), name='add_parent'),

    # Registration
    path('register/', views_frontend.register, name='register'),

    # AJAX endpoints
    path('ajax/validate-username/', views_frontend.validate_username, name='validate_username'),

    # PDF generation
    path('create_lecturers_pdf_list/', views_frontend.render_lecturer_pdf_list, name='lecturer_list_pdf'),
    path('create_students_pdf_list/', views_frontend.render_student_pdf_list, name='student_list_pdf'),

    # Two-Factor Authentication
    path('2fa/setup/', views_frontend.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views_frontend.disable_2fa, name='disable_2fa'),
    path('2fa/manage/', views_frontend.manage_2fa, name='manage_2fa'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
