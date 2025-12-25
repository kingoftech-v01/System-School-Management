from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('', views.monitoring_dashboard, name='dashboard'),
    path('enrollment-stats/', views.enrollment_statistics, name='enrollment_stats'),
    path('library-stats/', views.library_statistics, name='library_stats'),
    path('export/csv/', views.export_dashboard_csv, name='export_csv'),
]
