"""
Filieres URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:filieres:view_name
- API: api:v1:filieres:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'filieres', views_api.FiliereViewSet, basename='filiere')
api_router.register(r'subjects', views_api.FiliereSubjectViewSet, basename='subject')
api_router.register(r'requirements', views_api.FiliereRequirementViewSet, basename='requirement')


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
    # Filiere CRUD
    path('', views_frontend.filiere_list, name='filiere_list'),
    path('<int:pk>/', views_frontend.filiere_detail, name='filiere_detail'),
    path('create/', views_frontend.filiere_create, name='filiere_create'),
    path('<int:pk>/edit/', views_frontend.filiere_edit, name='filiere_edit'),
    path('<int:pk>/delete/', views_frontend.filiere_delete, name='filiere_delete'),

    # Subject management
    path('<int:filiere_pk>/subjects/add/', views_frontend.add_subject, name='add_subject'),
    path('<int:filiere_pk>/subjects/<int:subject_pk>/remove/', views_frontend.remove_subject, name='remove_subject'),

    # Requirement management
    path('<int:filiere_pk>/requirements/add/', views_frontend.add_requirement, name='add_requirement'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

app_name = 'filieres'

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
