"""
URL configuration for enrollment app.
"""

from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    # Public registration URLs
    path('register/step1/', views.register_step1, name='register_step1'),
    path('register/step2/', views.register_step2, name='register_step2'),
    path('register/step3/', views.register_step3, name='register_step3'),
    path('register/step4/', views.register_step4, name='register_step4'),
    path('register/complete/<int:registration_id>/', views.register_complete, name='register_complete'),
    path('register/<int:registration_id>/upload/', views.upload_document, name='upload_document'),

    # Direction/Admin URLs
    path('list/', views.enrollment_list, name='enrollment_list'),
    path('detail/<int:registration_id>/', views.enrollment_detail, name='enrollment_detail'),
    path('review/<int:registration_id>/', views.enrollment_review, name='enrollment_review'),
    path('document/<int:document_id>/verify/', views.verify_document, name='verify_document'),
    path('export/csv/', views.export_enrollments_csv, name='export_enrollments_csv'),
    path('statistics/', views.enrollment_statistics, name='enrollment_statistics'),
]
