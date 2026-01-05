"""
Views for grading app.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import (
    GradingRubric, RubricCriterion, RubricGrade, CriterionGrade,
    PeerReview, GradeCurve
)
from .serializers import (
    GradingRubricSerializer, RubricCriterionSerializer,
    RubricGradeSerializer, CriterionGradeSerializer,
    PeerReviewSerializer, GradeCurveSerializer,
    RubricCreateSerializer, RubricGradeCreateSerializer,
    PeerReviewSubmitSerializer
)
from .permissions import (
    CanCreateRubrics, CanGradeSubmissions, CanApplyCurves,
    IsReviewerOrReadOnly, CanViewGrades, CanManageRubric
)


class GradingRubricViewSet(viewsets.ModelViewSet):
    """
    ViewSet for grading rubrics.
    """
    queryset = GradingRubric.objects.select_related('assignment', 'course').prefetch_related('criteria').all()
    permission_classes = [IsAuthenticated, CanCreateRubrics, CanManageRubric]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assignment', 'course', 'is_active']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'max_points']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create' or self.action == 'update':
            return RubricCreateSerializer
        return GradingRubricSerializer

    def perform_create(self, serializer):
        """Set created_by to current user."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a rubric for reuse."""
        original_rubric = self.get_object()

        # Create new rubric
        new_rubric = GradingRubric.objects.create(
            title=f"{original_rubric.title} (Copy)",
            description=original_rubric.description,
            assignment=None,  # Will be set by user
            course=original_rubric.course,
            max_points=original_rubric.max_points,
            created_by=request.user,
            is_active=False  # Start as inactive
        )

        # Duplicate criteria
        for criterion in original_rubric.criteria.all():
            RubricCriterion.objects.create(
                rubric=new_rubric,
                name=criterion.name,
                description=criterion.description,
                max_points=criterion.max_points,
                order=criterion.order
            )

        serializer = self.get_serializer(new_rubric)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get grading statistics for this rubric."""
        rubric = self.get_object()

        grades = RubricGrade.objects.filter(rubric=rubric)

        stats = {
            'total_graded': grades.count(),
            'average_score': grades.aggregate(Avg('total_points'))['total_points__avg'] or 0,
            'average_percentage': grades.aggregate(Avg('percentage'))['percentage__avg'] or 0,
            'grade_distribution': {
                'A': grades.filter(percentage__gte=90).count(),
                'B': grades.filter(percentage__gte=80, percentage__lt=90).count(),
                'C': grades.filter(percentage__gte=70, percentage__lt=80).count(),
                'D': grades.filter(percentage__gte=60, percentage__lt=70).count(),
                'F': grades.filter(percentage__lt=60).count(),
            }
        }

        return Response(stats)


class RubricCriterionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for rubric criteria.
    """
    queryset = RubricCriterion.objects.select_related('rubric').all()
    serializer_class = RubricCriterionSerializer
    permission_classes = [IsAuthenticated, CanCreateRubrics]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rubric']
    ordering_fields = ['order', 'max_points']
    ordering = ['order']

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder criteria."""
        criteria_order = request.data.get('criteria_order', [])

        if not criteria_order:
            return Response(
                {'detail': 'criteria_order is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for item in criteria_order:
            criterion_id = item.get('id')
            new_order = item.get('order')

            try:
                criterion = RubricCriterion.objects.get(pk=criterion_id)
                criterion.order = new_order
                criterion.save()
            except RubricCriterion.DoesNotExist:
                continue

        return Response({'detail': 'Criteria reordered successfully.'})


class RubricGradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for rubric grades.
    """
    queryset = RubricGrade.objects.select_related(
        'rubric', 'student', 'graded_by'
    ).prefetch_related('criterion_grades').all()
    permission_classes = [IsAuthenticated, CanGradeSubmissions, CanViewGrades]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rubric', 'student', 'graded_by']
    search_fields = ['student__student__first_name', 'student__student__last_name', 'feedback']
    ordering_fields = ['graded_at', 'total_points', 'percentage']
    ordering = ['-graded_at']

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create' or self.action == 'update':
            return RubricGradeCreateSerializer
        return RubricGradeSerializer

    def get_queryset(self):
        """Filter grades based on user role."""
        user = self.request.user

        # Staff and teachers can see all grades
        if user.is_staff or user.is_teacher:
            return self.queryset

        # Students can only see their own grades
        return self.queryset.filter(student__student=user)

    def perform_create(self, serializer):
        """Set graded_by to current user."""
        serializer.save(graded_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanGradeSubmissions])
    def finalize(self, request, pk=None):
        """Mark grade as finalized (no more edits)."""
        grade = self.get_object()

        if grade.is_finalized:
            return Response(
                {'detail': 'Grade is already finalized.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        grade.is_finalized = True
        grade.save()

        return Response({'detail': 'Grade finalized successfully.'})

    @action(detail=True, methods=['get'])
    def breakdown(self, request, pk=None):
        """Get detailed breakdown of criterion grades."""
        grade = self.get_object()

        criterion_grades = grade.criterion_grades.select_related('criterion').all()

        breakdown = []
        for cg in criterion_grades:
            breakdown.append({
                'criterion_name': cg.criterion.name,
                'criterion_max_points': cg.criterion.max_points,
                'points_awarded': cg.points_awarded,
                'percentage': (cg.points_awarded / cg.criterion.max_points * 100) if cg.criterion.max_points > 0 else 0,
                'feedback': cg.feedback
            })

        return Response({
            'total_points': grade.total_points,
            'max_points': grade.rubric.max_points,
            'percentage': grade.percentage,
            'general_feedback': grade.feedback,
            'criterion_breakdown': breakdown
        })


class CriterionGradeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for criterion grades (read-only).
    """
    queryset = CriterionGrade.objects.select_related('rubric_grade', 'criterion').all()
    serializer_class = CriterionGradeSerializer
    permission_classes = [IsAuthenticated, CanViewGrades]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rubric_grade', 'criterion']
    ordering_fields = ['points_awarded']
    ordering = ['criterion__order']


class PeerReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for peer reviews.
    """
    queryset = PeerReview.objects.select_related(
        'assignment', 'reviewer', 'reviewee'
    ).all()
    permission_classes = [IsAuthenticated, IsReviewerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['assignment', 'reviewer', 'reviewee', 'status']
    ordering_fields = ['created_at', 'submitted_at', 'score']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'submit':
            return PeerReviewSubmitSerializer
        return PeerReviewSerializer

    def get_queryset(self):
        """Filter reviews based on user role."""
        user = self.request.user

        # Staff and teachers can see all reviews
        if user.is_staff or user.is_teacher:
            return self.queryset

        # Students can see reviews they wrote or received
        return self.queryset.filter(
            Q(reviewer__student=user) | Q(reviewee__student=user)
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit a peer review."""
        review = self.get_object()

        if review.status != 'pending':
            return Response(
                {'detail': 'Review has already been submitted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            status='submitted',
            submitted_at=timezone.now()
        )

        return Response({'detail': 'Review submitted successfully.'})

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get reviews assigned to current user."""
        user = request.user

        reviews = self.queryset.filter(reviewer__student=user)

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def received_reviews(self, request):
        """Get reviews received by current user."""
        user = request.user

        reviews = self.queryset.filter(
            reviewee__student=user,
            status='submitted'
        )

        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)


class GradeCurveViewSet(viewsets.ModelViewSet):
    """
    ViewSet for grade curves.
    """
    queryset = GradeCurve.objects.select_related('course', 'applied_by').all()
    serializer_class = GradeCurveSerializer
    permission_classes = [IsAuthenticated, CanApplyCurves]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'curve_type']
    ordering_fields = ['applied_at']
    ordering = ['-applied_at']

    def perform_create(self, serializer):
        """Apply curve and set applied_by to current user."""
        serializer.save(applied_by=self.request.user)

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Preview curve application without saving."""
        curve = self.get_object()

        # Get affected grades (logic depends on curve scope)
        # This is a simplified preview
        affected_count = 0

        if curve.course:
            # Count grades that would be affected
            from result.models import Result
            affected_count = Result.objects.filter(course=curve.course).count()

        return Response({
            'curve_type': curve.curve_type,
            'adjustment_value': curve.adjustment_value,
            'affected_students': affected_count,
            'description': curve.description
        })
