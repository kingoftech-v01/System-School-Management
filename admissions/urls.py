from django.urls import path
from . import views

app_name = 'admissions'

urlpatterns = [
    path('apply/', views.admission_apply, name='apply'),
    path('status/', views.admission_status, name='status'),
    path('sessions/', views.admission_session_list, name='session_list'),
    path('counseling/<int:student_id>/', views.counseling_comment_create, name='counseling_comment'),
]
