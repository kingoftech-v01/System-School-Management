from django.urls import path
from . import views

app_name = 'notices'

urlpatterns = [
    path('', views.notice_list, name='notice_list'),
    path('<int:pk>/', views.notice_detail, name='notice_detail'),
    path('create/', views.notice_create, name='notice_create'),
    path('<int:pk>/respond/', views.notice_respond, name='notice_respond'),
]
