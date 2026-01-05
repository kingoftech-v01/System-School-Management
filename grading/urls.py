"""
URL configuration for grading app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GradingRubricViewSet, RubricCriterionViewSet,
    RubricGradeViewSet, CriterionGradeViewSet,
    PeerReviewViewSet, GradeCurveViewSet
)

app_name = 'grading'

router = DefaultRouter()
router.register(r'rubrics', GradingRubricViewSet, basename='rubric')
router.register(r'criteria', RubricCriterionViewSet, basename='criterion')
router.register(r'grades', RubricGradeViewSet, basename='grade')
router.register(r'criterion-grades', CriterionGradeViewSet, basename='criterion-grade')
router.register(r'peer-reviews', PeerReviewViewSet, basename='peer-review')
router.register(r'curves', GradeCurveViewSet, basename='curve')

urlpatterns = [
    path('', include(router.urls)),
]
