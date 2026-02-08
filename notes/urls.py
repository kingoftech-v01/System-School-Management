"""
Notes URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:notes:view_name
- API: api:v1:notes:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'notes', views_api.ProfessorNoteViewSet, basename='note')
api_router.register(r'history', views_api.NoteHistoryViewSet, basename='history')


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
    path('', views_frontend.note_list, name='note_list'),
    path('all/', views_frontend.note_list_all, name='note_list_all'),
    path('create/', views_frontend.note_create, name='note_create'),
    path('<int:pk>/', views_frontend.note_detail, name='note_detail'),
    path('<int:pk>/edit/', views_frontend.note_edit, name='note_edit'),
    path('<int:pk>/delete/', views_frontend.note_delete, name='note_delete'),
    path('<int:pk>/comment/', views_frontend.note_comment_create, name='note_comment_create'),
    path('pending/', views_frontend.notes_pending_approval, name='notes_pending'),
    path('<int:pk>/approve/', views_frontend.note_approve, name='note_approve'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
