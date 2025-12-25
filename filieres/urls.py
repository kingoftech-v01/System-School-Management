"""
URL configuration for filieres app.
"""

from django.urls import path
from . import views

app_name = 'filieres'

urlpatterns = [
    # Filiere CRUD
    path('', views.filiere_list, name='filiere_list'),
    path('<int:pk>/', views.filiere_detail, name='filiere_detail'),
    path('create/', views.filiere_create, name='filiere_create'),
    path('<int:pk>/edit/', views.filiere_edit, name='filiere_edit'),
    path('<int:pk>/delete/', views.filiere_delete, name='filiere_delete'),

    # Subject management
    path('<int:filiere_pk>/subjects/add/', views.add_subject, name='add_subject'),
    path('<int:filiere_pk>/subjects/<int:subject_pk>/remove/', views.remove_subject, name='remove_subject'),

    # Requirement management
    path('<int:filiere_pk>/requirements/add/', views.add_requirement, name='add_requirement'),
]
