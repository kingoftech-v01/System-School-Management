from django.urls import path

from . import views_frontend

frontend_urlpatterns = [
    path('', views_frontend.anomaly_dashboard, name='dashboard'),
    path('alerts/', views_frontend.alert_list, name='alert_list'),
    path('alerts/<int:pk>/', views_frontend.alert_detail, name='alert_detail'),
    path('alerts/<int:pk>/acknowledge/', views_frontend.alert_acknowledge, name='alert_acknowledge'),
    path('alerts/<int:pk>/resolve/', views_frontend.alert_resolve, name='alert_resolve'),
]

api_urlpatterns = []
