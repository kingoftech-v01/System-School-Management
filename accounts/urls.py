"""
Accounts URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:accounts:view_name
- API: api:v1:accounts:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_parent
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
    path('parents/', views_frontend.parent_list, name='parent_list'),
    path('parents/add/', views_frontend.ParentAdd.as_view(), name='add_parent'),
    path('parents/<int:pk>/', views_frontend.parent_detail, name='parent_detail'),
    path('parents/<int:pk>/edit/', views_frontend.parent_edit, name='parent_edit'),
    path('parents/<int:pk>/delete/', views_frontend.parent_delete, name='parent_delete'),

    # Registration (legacy)
    path('register/', views_frontend.register, name='register'),

    # Signup flow (role-based)
    path('signup/', views_frontend.signup_hub, name='signup_hub'),
    path('signup/student/', views_frontend.student_activate, name='student_activate'),
    path('signup/student/verify/', views_frontend.student_verify_parent, name='student_verify_parent'),
    path('signup/student/password/', views_frontend.student_set_password, name='student_set_password'),
    path('signup/parent/', views_frontend.parent_invitation_step1, name='parent_invitation_step1'),
    path('signup/parent/complete/', views_frontend.parent_invitation_step2, name='parent_invitation_step2'),
    path('signup/parent/new/', views_frontend.parent_self_signup, name='parent_self_signup'),
    path('signup/staff/', views_frontend.staff_invitation_step1, name='staff_invitation_step1'),
    path('signup/staff/complete/', views_frontend.staff_invitation_step2, name='staff_invitation_step2'),
    path('password/force-reset/', views_frontend.force_password_reset, name='force_password_reset'),

    # AJAX endpoints
    path('ajax/validate-username/', views_frontend.validate_username, name='validate_username'),

    # PDF generation
    path('create_lecturers_pdf_list/', views_frontend.render_lecturer_pdf_list, name='lecturer_list_pdf'),
    path('create_students_pdf_list/', views_frontend.render_student_pdf_list, name='student_list_pdf'),

    # Two-Factor Authentication
    path('2fa/setup/', views_frontend.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views_frontend.disable_2fa, name='disable_2fa'),
    path('2fa/manage/', views_frontend.manage_2fa, name='manage_2fa'),

    # Parent Portal
    path('parent/dashboard/', views_parent.parent_dashboard, name='parent_dashboard'),
    path('parent/select-child/<int:student_id>/', views_parent.parent_select_child, name='parent_select_child'),
    path('parent/grades/', views_parent.parent_child_grades, name='parent_child_grades'),
    path('parent/attendance/', views_parent.parent_child_attendance, name='parent_child_attendance'),
    path('parent/timetable/', views_parent.parent_child_timetable, name='parent_child_timetable'),
    path('parent/invoices/', views_parent.parent_child_invoices, name='parent_child_invoices'),
    path('parent/payments/', views_parent.parent_child_payment_history, name='parent_child_payment_history'),
    path('parent/pay/<int:invoice_id>/', views_parent.parent_make_payment, name='parent_make_payment'),
    path('parent/messages/', views_parent.parent_messages_inbox, name='parent_messages_inbox'),
    path('parent/messages/compose/', views_parent.parent_messages_compose, name='parent_messages_compose'),
    path('parent/messages/<int:message_id>/', views_parent.parent_messages_thread, name='parent_messages_thread'),
    path('parent/appointments/', views_parent.parent_appointments, name='parent_appointments'),
    path('parent/appointments/request/', views_parent.parent_appointment_request, name='parent_appointment_request'),
    path('parent/discipline/', views_parent.parent_disciplinary_records, name='parent_disciplinary_records'),
    path('parent/discipline/<int:action_id>/acknowledge/', views_parent.parent_acknowledge_discipline, name='parent_acknowledge_discipline'),
    path('parent/permission-slips/', views_parent.parent_permission_slips, name='parent_permission_slips'),
    path('parent/permission-slips/<int:slip_id>/sign/', views_parent.parent_sign_permission_slip, name='parent_sign_permission_slip'),
    path('parent/events/', views_parent.parent_events, name='parent_events'),
    path('parent/events/<int:event_id>/', views_parent.parent_event_detail, name='parent_event_detail'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
