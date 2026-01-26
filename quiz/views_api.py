"""
Quiz API Views - REST API endpoints.

This module provides API endpoints for:
- Quiz CRUD and management
- Question management (MC and Essay)
- Quiz taking and submission
- Progress tracking

All views return JSON responses.
API URL namespace: api:v1:quiz:resource-name
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.db.models import Count
from django.utils import timezone

from .models import Quiz, MCQuestion, EssayQuestion, Sitting, Progress
from .serializers import (
    QuizSerializer,
    QuizListSerializer,
    QuizCreateSerializer,
    MCQuestionSerializer,
    EssayQuestionSerializer,
    SittingSerializer,
    SittingListSerializer,
    ProgressSerializer,
)
from accounts.permissions import IsLecturerUser


# ============================================================================
# QUIZ VIEWSET
# ============================================================================

class QuizViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing quizzes.

    Features:
    - List quizzes (filtered by course)
    - Create quizzes (lecturer only)
    - Update/delete quizzes (lecturer only)
    - Get quiz details with questions

    Filtering: course, category, draft
    Search: title, description
    Ordering: title, timestamp
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['course', 'category', 'draft']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Get quizzes with question count."""
        queryset = Quiz.objects.all().select_related('course').annotate(
            question_count=Count('question')
        )

        # Students can only see non-draft quizzes
        if not hasattr(self.request.user, 'is_lecturer') or not self.request.user.is_lecturer:
            queryset = queryset.filter(draft=False)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return QuizListSerializer
        elif self.action == 'create':
            return QuizCreateSerializer
        return QuizSerializer

    def get_permissions(self):
        """Lecturer only for create/update/delete."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsLecturerUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """Get all questions for a quiz."""
        quiz = self.get_object()
        mc_questions = MCQuestion.objects.filter(quiz=quiz)
        essay_questions = EssayQuestion.objects.filter(quiz=quiz)

        return Response({
            'mc_questions': MCQuestionSerializer(mc_questions, many=True, context={'request': request}).data,
            'essay_questions': EssayQuestionSerializer(essay_questions, many=True, context={'request': request}).data,
        })

    @action(detail=True, methods=['post'])
    def start_quiz(self, request, pk=None):
        """Start a new quiz sitting."""
        quiz = self.get_object()

        # Check if single attempt and user has already taken quiz
        if quiz.single_attempt:
            existing = Sitting.objects.filter(user=request.user, quiz=quiz, complete=True).first()
            if existing:
                return Response(
                    {'error': 'You have already completed this quiz and only one attempt is allowed.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create new sitting
        sitting = Sitting.objects.create(
            user=request.user,
            quiz=quiz,
            question_order=quiz.random_order,
            question_list=quiz.get_questions()
        )

        return Response(SittingSerializer(sitting).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_quizzes(self, request):
        """Get quizzes for courses the user is enrolled in."""
        # Assuming user has enrolled courses
        user_courses = request.user.course_set.all() if hasattr(request.user, 'course_set') else []
        quizzes = self.get_queryset().filter(course__in=user_courses)
        page = self.paginate_queryset(quizzes)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


# ============================================================================
# MCQUESTION VIEWSET
# ============================================================================

class MCQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing multiple choice questions.

    Features:
    - List MC questions
    - Create/update/delete MC questions (lecturer only)

    Filtering: quiz
    Ordering: order
    """
    queryset = MCQuestion.objects.all()
    serializer_class = MCQuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz']
    ordering_fields = ['order']
    ordering = ['order']

    def get_permissions(self):
        """Lecturer only for modifications."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsLecturerUser()]
        return [IsAuthenticated()]


# ============================================================================
# ESSAYQUESTION VIEWSET
# ============================================================================

class EssayQuestionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing essay questions.

    Features:
    - List essay questions
    - Create/update/delete essay questions (lecturer only)

    Filtering: quiz
    Ordering: order
    """
    queryset = EssayQuestion.objects.all()
    serializer_class = EssayQuestionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz']
    ordering_fields = ['order']
    ordering = ['order']

    def get_permissions(self):
        """Lecturer only for modifications."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsLecturerUser()]
        return [IsAuthenticated()]


# ============================================================================
# SITTING VIEWSET
# ============================================================================

class SittingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quiz attempts (sittings).

    Features:
    - List user's quiz attempts
    - Get sitting details
    - Submit answers
    - Mark sitting as complete

    Filtering: quiz, user, complete
    Ordering: start, end
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz', 'user', 'complete']
    ordering_fields = ['start', 'end']
    ordering = ['-start']

    def get_queryset(self):
        """Users can only see their own sittings, lecturers see all."""
        queryset = Sitting.objects.all().select_related('user', 'quiz')

        if not hasattr(self.request.user, 'is_lecturer') or not self.request.user.is_lecturer:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'list':
            return SittingListSerializer
        return SittingSerializer

    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        """Submit answer for a question in the sitting."""
        sitting = self.get_object()

        if sitting.complete:
            return Response(
                {'error': 'This quiz attempt is already complete.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        question_id = request.data.get('question_id')
        answer = request.data.get('answer')

        if not question_id or answer is None:
            return Response(
                {'error': 'question_id and answer are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process answer (implementation depends on your answer processing logic)
        # This is a simplified version
        sitting.add_user_answer(question_id, answer)
        sitting.save()

        return Response({'status': 'Answer submitted successfully'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark sitting as complete and calculate final score."""
        sitting = self.get_object()

        if sitting.complete:
            return Response(
                {'error': 'This quiz attempt is already complete.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        sitting.mark_quiz_complete()
        sitting.end = timezone.now()
        sitting.complete = True
        sitting.save()

        return Response(SittingSerializer(sitting).data)


# ============================================================================
# PROGRESS VIEWSET
# ============================================================================

class ProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for student progress tracking.

    Features:
    - List user's progress
    - Get detailed progress

    Filtering: user
    Ordering: timestamp
    """
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user']
    ordering_fields = ['timestamp', 'score']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Users can only see their own progress, lecturers see all."""
        queryset = Progress.objects.all().select_related('user')

        if not hasattr(self.request.user, 'is_lecturer') or not self.request.user.is_lecturer:
            queryset = queryset.filter(user=self.request.user)

        return queryset
