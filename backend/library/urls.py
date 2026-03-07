"""
Library URLs - API-only routing.

URL Namespaces:
- API: api:v1:library:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

api_router = DefaultRouter()
api_router.register(r'books', views_api.BookViewSet, basename='book')
api_router.register(r'borrow-records', views_api.BorrowRecordViewSet, basename='borrow-record')

api_urlpatterns = [path('', include(api_router.urls))]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
]
