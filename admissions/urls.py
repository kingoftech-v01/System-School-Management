from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'sessions', views_api.AdmissionSessionViewSet, basename='session')
api_router.register(r'applications', views_api.AdmissionStudentViewSet, basename='application')

api_urlpatterns = [path('', include(api_router.urls))]
frontend_urlpatterns = [
    path('', views_frontend.admission_session_list, name='home'),
    path('apply/', views_frontend.admission_apply, name='apply'),
    path('status/', views_frontend.admission_status, name='check_status'),
    path('comment/<int:student_id>/', views_frontend.counseling_comment_create, name='counseling_comment'),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
