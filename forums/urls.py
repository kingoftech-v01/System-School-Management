"""
Forums URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:forums:view_name
- API: api:v1:forums:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'categories', views_api.ForumCategoryViewSet, basename='category')
api_router.register(r'threads', views_api.ThreadViewSet, basename='thread')
api_router.register(r'posts', views_api.PostViewSet, basename='post')
api_router.register(r'tags', views_api.TagViewSet, basename='tag')
api_router.register(r'subscriptions', views_api.ThreadSubscriptionViewSet, basename='subscription')
api_router.register(r'reports', views_api.ReportViewSet, basename='report')


# ============================================================================
# API URLPATTERNS
# ============================================================================

api_urlpatterns = [
    path('', include(api_router.urls)),
]


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Forum home
    path('', views_frontend.forum_home, name='forum_home'),

    # Categories
    path('categories/', views_frontend.category_list, name='category_list'),
    path('categories/<slug:slug>/', views_frontend.category_detail, name='category_detail'),

    # Threads
    path('threads/', views_frontend.thread_list, name='thread_list'),
    path('threads/create/', views_frontend.thread_create, name='thread_create'),
    path('threads/create/<slug:category_slug>/', views_frontend.thread_create, name='thread_create_in_category'),
    path('threads/<slug:slug>/', views_frontend.thread_detail, name='thread_detail'),
    path('threads/<slug:slug>/edit/', views_frontend.thread_update, name='thread_update'),
    path('threads/<slug:slug>/delete/', views_frontend.thread_delete, name='thread_delete'),
    path('threads/<slug:slug>/subscribe/', views_frontend.thread_subscribe, name='thread_subscribe'),
    path('threads/<slug:slug>/unsubscribe/', views_frontend.thread_unsubscribe, name='thread_unsubscribe'),

    # Posts
    path('threads/<slug:thread_slug>/reply/', views_frontend.post_create, name='post_create'),
    path('threads/<slug:thread_slug>/reply/<int:parent_id>/', views_frontend.post_create, name='post_reply'),
    path('posts/<int:pk>/edit/', views_frontend.post_update, name='post_update'),
    path('posts/<int:pk>/delete/', views_frontend.post_delete, name='post_delete'),
    path('posts/<int:pk>/vote/', views_frontend.post_vote, name='post_vote'),

    # Tags
    path('tags/', views_frontend.tag_list, name='tag_list'),
    path('tags/<slug:slug>/', views_frontend.tag_threads, name='tag_threads'),

    # User activity
    path('my-threads/', views_frontend.my_threads, name='my_threads'),
    path('my-posts/', views_frontend.my_posts, name='my_posts'),
    path('my-subscriptions/', views_frontend.my_subscriptions, name='my_subscriptions'),

    # Moderation
    path('report/<int:content_type_id>/<int:object_id>/', views_frontend.report_content, name='report_content'),

    # Search
    path('search/', views_frontend.search, name='search'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
