from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('category/<slug:slug>/', views.category_articles, name='category_articles'),
    path('<slug:slug>/', views.article_detail, name='article_detail'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
]
