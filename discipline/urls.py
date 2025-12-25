from django.urls import path
from . import views

app_name = 'discipline'

urlpatterns = [
    path('', views.disciplinary_action_list, name='action_list'),
    path('create/', views.disciplinary_action_create, name='action_create'),
    path('<int:pk>/', views.disciplinary_action_detail, name='action_detail'),
]
