from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views_api, views_frontend

# API Router
api_router = DefaultRouter()
api_router.register(r'incidents', views_api.IncidentViewSet, basename='incident')
api_router.register(r'visitors', views_api.VisitorLogViewSet, basename='visitor')
api_router.register(
    r'case-notes', views_api.StudentCaseNoteViewSet, basename='case-note'
)

api_urlpatterns = [
    path('', include(api_router.urls)),
]

frontend_urlpatterns = [
    # Incidents
    path('incidents/', views_frontend.incident_list, name='incident_list'),
    path(
        'incidents/create/',
        views_frontend.incident_create,
        name='incident_create',
    ),
    path(
        'incidents/<int:pk>/',
        views_frontend.incident_detail,
        name='incident_detail',
    ),
    path(
        'incidents/<int:pk>/edit/',
        views_frontend.incident_edit,
        name='incident_edit',
    ),

    # Visitors
    path('visitors/', views_frontend.visitor_list, name='visitor_list'),
    path(
        'visitors/sign-in/',
        views_frontend.visitor_sign_in,
        name='visitor_sign_in',
    ),
    path(
        'visitors/<int:pk>/',
        views_frontend.visitor_detail,
        name='visitor_detail',
    ),
    path(
        'visitors/<int:pk>/sign-out/',
        views_frontend.visitor_sign_out,
        name='visitor_sign_out',
    ),

    # Case Notes
    path('case-notes/', views_frontend.case_note_list, name='case_note_list'),
    path(
        'case-notes/create/',
        views_frontend.case_note_create,
        name='case_note_create',
    ),
    path(
        'case-notes/<int:pk>/',
        views_frontend.case_note_detail,
        name='case_note_detail',
    ),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
