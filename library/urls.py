from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'books', views_api.BookViewSet, basename='book')
api_router.register(r'borrow-records', views_api.BorrowRecordViewSet, basename='borrow-record')

api_urlpatterns = [path('', include(api_router.urls))]
frontend_urlpatterns = [
    path('', views_frontend.book_list, name='book_list'),
    path('create/', views_frontend.book_create, name='book_create'),
    path('overdue/', views_frontend.overdue_books, name='overdue_books'),
    path('<int:pk>/', views_frontend.book_detail, name='book_detail'),
    path('<int:pk>/edit/', views_frontend.book_edit, name='book_edit'),
    path('<int:pk>/delete/', views_frontend.book_delete, name='book_delete'),
    path('my-borrowed/', views_frontend.my_borrowed_books, name='my_borrowed_books'),
    path('borrow/<int:book_id>/', views_frontend.borrow_book, name='borrow_book'),
    path('return/<int:record_id>/', views_frontend.return_book, name='return_book'),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
