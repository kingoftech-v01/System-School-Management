from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_frontend, views_api

api_router = DefaultRouter()
api_router.register(r'articles', views_api.ArticleViewSet, basename='article')
api_router.register(r'categories', views_api.CategoryViewSet, basename='category')

api_urlpatterns = [path('', include(api_router.urls))]
frontend_urlpatterns = [
    path('', views_frontend.article_list, name='article_list'),
    path('create/', views_frontend.article_create, name='article_create'),
    path('newsletter/', views_frontend.newsletter_subscribe, name='newsletter'),
    path('category/<slug:category_slug>/', views_frontend.category_articles, name='category_articles'),
    path('<slug:slug>/', views_frontend.article_detail, name='article_detail'),
    path('<slug:slug>/edit/', views_frontend.article_edit, name='article_edit'),
    path('<int:pk>/comment/', views_frontend.comment_submit, name='comment_submit'),
    path('<int:pk>/like/', views_frontend.article_like_toggle, name='article_like'),
]

urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
