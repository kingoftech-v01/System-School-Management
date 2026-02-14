from django.urls import path

from . import views_api

api_urlpatterns = [
    path(
        'students/<int:student_id>/timeline/',
        views_api.StudentTimelineAPIView.as_view(),
        name='student_timeline',
    ),
]

urlpatterns = api_urlpatterns
