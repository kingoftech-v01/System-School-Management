from django.urls import path
from . import views

app_name = 'alumni'

urlpatterns = [
    path('', views.alumni_directory, name='directory'),
    path('profile/<int:pk>/', views.alumni_profile, name='profile'),
    path('events/', views.alumni_event_list, name='event_list'),
    path('events/<int:pk>/', views.alumni_event_detail, name='event_detail'),
    path('donate/', views.donation_create, name='donate'),
]
