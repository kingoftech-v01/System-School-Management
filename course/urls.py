"""
Course URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:course:view_name
- API: api:v1:course:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'programs', views_api.ProgramViewSet, basename='program')
api_router.register(r'courses', views_api.CourseViewSet, basename='course')
api_router.register(r'allocations', views_api.CourseAllocationViewSet, basename='allocation')
api_router.register(r'uploads', views_api.UploadViewSet, basename='upload')
api_router.register(r'videos', views_api.UploadVideoViewSet, basename='video')
api_router.register(r'registration', views_api.CourseRegistrationViewSet, basename='registration')


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
    # Program urls
    path('', views_frontend.ProgramFilterView.as_view(), name='programs'),
    path('<int:pk>/detail/', views_frontend.program_detail, name='program_detail'),
    path('add/', views_frontend.program_add, name='add_program'),
    path('<int:pk>/edit/', views_frontend.program_edit, name='edit_program'),
    path('<int:pk>/delete/', views_frontend.program_delete, name='program_delete'),

    # Course urls
    path('course/<slug>/detail/', views_frontend.course_single, name='course_detail'),
    path('<int:pk>/course/add/', views_frontend.course_add, name='course_add'),
    path('course/<slug>/edit/', views_frontend.course_edit, name='edit_course'),
    path('course/delete/<slug>/', views_frontend.course_delete, name='delete_course'),

    # CourseAllocation urls
    path('course/assign/', views_frontend.CourseAllocationFormView.as_view(), name='course_allocation'),
    path('course/allocated/', views_frontend.CourseAllocationFilterView.as_view(), name='course_allocation_view'),
    path('allocated_course/<int:pk>/edit/', views_frontend.edit_allocated_course, name='edit_allocated_course'),
    path('course/<int:pk>/deallocate/', views_frontend.deallocate_course, name='course_deallocate'),

    # File uploads urls
    path('course/<slug>/documentations/upload/', views_frontend.handle_file_upload, name='upload_file_view'),
    path('course/<slug>/documentations/<int:file_id>/edit/', views_frontend.handle_file_edit, name='upload_file_edit'),
    path('course/<slug>/documentations/<int:file_id>/delete/', views_frontend.handle_file_delete, name='upload_file_delete'),

    # Video uploads urls
    path('course/<slug>/video_tutorials/upload/', views_frontend.handle_video_upload, name='upload_video'),
    path('course/<slug>/video_tutorials/<video_slug>/detail/', views_frontend.handle_video_single, name='video_single'),
    path('course/<slug>/video_tutorials/<video_slug>/edit/', views_frontend.handle_video_edit, name='upload_video_edit'),
    path('course/<slug>/video_tutorials/<video_slug>/delete/', views_frontend.handle_video_delete, name='upload_video_delete'),

    # Course listing and search
    path('courses/all/', views_frontend.course_list_all, name='course_list_all'),
    path('programs/search/', views_frontend.program_search, name='program_search'),

    # Course registration
    path('course/registration/', views_frontend.course_registration, name='course_registration'),
    path('course/drop/', views_frontend.course_drop, name='course_drop'),
    path('my_courses/', views_frontend.user_course_list, name='user_course_list'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
