from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'books', views_api.BookViewSet, basename='book')
api_router.register(r'borrow-records', views_api.BorrowRecordViewSet, basename='borrow-record')

api_urlpatterns = [path('', include(api_router.urls))]
frontend_urlpatterns = [
    path('', views_frontend.book_list, name='book_list'),
    path('my-borrowed/', views_frontend.my_borrowed_books, name='my_borrowed_books'),
    path('borrow/<int:book_id>/', views_frontend.borrow_book, name='borrow_book'),
    path('return/<int:record_id>/', views_frontend.return_book, name='return_book'),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
