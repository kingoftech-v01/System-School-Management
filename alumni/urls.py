from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'alumni', views_api.AlumniViewSet, basename='alumni')
api_router.register(r'events', views_api.AlumniEventViewSet, basename='event')

api_urlpatterns = [path('', include(api_router.urls))]
frontend_urlpatterns = [
    path('', views_frontend.alumni_directory, name='directory'),
    path('<int:pk>/', views_frontend.alumni_profile, name='profile'),
    path('register/', views_frontend.alumni_register, name='register'),
    path('events/', views_frontend.alumni_events, name='events'),
]

app_name = 'alumni'
urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
