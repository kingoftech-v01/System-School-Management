from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'alumni', views_api.AlumniViewSet, basename='alumni')
api_router.register(r'events', views_api.AlumniEventViewSet, basename='event')

api_urlpatterns = [path('', include(api_router.urls))]
frontend_urlpatterns = [
    path('', views_frontend.alumni_directory, name='directory'),
    path('profile/<int:pk>/', views_frontend.alumni_profile, name='profile'),
    path('create/', views_frontend.alumni_create, name='alumni_create'),
    path('edit/<int:pk>/', views_frontend.alumni_edit, name='alumni_edit'),
    path('events/', views_frontend.alumni_event_list, name='events'),
    path('events/<int:pk>/', views_frontend.alumni_event_detail, name='event_detail'),
    path('achievements/', views_frontend.achievement_list, name='achievements'),
    path('donate/', views_frontend.donation_create, name='donate'),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
