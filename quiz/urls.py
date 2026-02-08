"""
Quiz URLs - Frontend and API routing.

URL Namespaces:
- Frontend: frontend:quiz:view_name
- API: api:v1:quiz:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_frontend
from . import views_api


# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()
api_router.register(r'quizzes', views_api.QuizViewSet, basename='quiz')
api_router.register(r'mc-questions', views_api.MCQuestionViewSet, basename='mc-question')
api_router.register(r'essay-questions', views_api.EssayQuestionViewSet, basename='essay-question')
api_router.register(r'sittings', views_api.SittingViewSet, basename='sitting')
api_router.register(r'progress', views_api.ProgressViewSet, basename='progress')


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
    path("<slug>/quizzes/", views_frontend.quiz_list, name="quiz_index"),
    path("progress/", view=views_frontend.QuizUserProgressView.as_view(), name="quiz_progress"),
    path("marking_list/", view=views_frontend.QuizMarkingList.as_view(), name="quiz_marking"),
    path(
        "marking/<int:pk>/",
        view=views_frontend.QuizMarkingDetail.as_view(),
        name="quiz_marking_detail",
    ),
    path("<int:pk>/<slug>/take/", view=views_frontend.QuizTake.as_view(), name="quiz_take"),
    path("<slug>/quiz_add/", views_frontend.QuizCreateView.as_view(), name="quiz_create"),
    path("<slug>/<int:pk>/add/", views_frontend.QuizUpdateView.as_view(), name="quiz_update"),
    path("<slug>/<int:pk>/delete/", views_frontend.quiz_delete, name="quiz_delete"),
    path(
        "mc-question/add/<slug>/<int:quiz_id>/",
        views_frontend.MCQuestionCreate.as_view(),
        name="mc_create",
    ),
    path(
        "mc-question/edit/<slug>/<int:pk>/",
        views_frontend.MCQuestionEdit.as_view(),
        name="mc_edit",
    ),
    path(
        "essay-question/add/<slug>/<int:quiz_id>/",
        views_frontend.EssayQuestionCreate.as_view(),
        name="essay_create",
    ),
    path(
        "tf-question/add/<slug>/<int:quiz_id>/",
        views_frontend.TFQuestionCreate.as_view(),
        name="tf_create",
    ),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================


urlpatterns = [
    path('api/', include((api_urlpatterns, 'api'))),
    path('', include((frontend_urlpatterns, 'frontend'))),
]
