"""
Scheduling URLs - API-only routing.

URL Namespaces:
- API: api:v1:scheduling:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'rooms', views_api.RoomViewSet, basename='room')
api_router.register(r'timeslots', views_api.TimeSlotViewSet, basename='timeslot')
api_router.register(r'entries', views_api.ScheduleEntryViewSet, basename='scheduleentry')
api_router.register(r'exceptions', views_api.ScheduleExceptionViewSet, basename='scheduleexception')
api_router.register(r'substitutions', views_api.SubstitutionRequestViewSet, basename='substitutionrequest')
api_router.register(r'notifications', views_api.ScheduleNotificationViewSet, basename='schedulenotification')
api_router.register(r'generations', views_api.TimetableGenerationViewSet, basename='timetablegeneration')


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
