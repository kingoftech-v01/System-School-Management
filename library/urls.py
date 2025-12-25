from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('book/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('my-books/', views.my_borrowed_books, name='my_borrowed_books'),
    path('return/<int:record_id>/', views.return_book, name='return_book'),
]
