"""
Quiz Serializers - DRF serializers for quiz and question API.

This module provides serializers for:
- Quiz model (quiz configuration and management)
- Question models (MCQuestion, EssayQuestion)
- Sitting model (quiz attempts)
- Progress model (student progress tracking)
"""

from rest_framework import serializers
from .models import Quiz, Question, MCQuestion, EssayQuestion, Sitting, Progress


# ============================================================================
# QUIZ SERIALIZERS
# ============================================================================

class QuizSerializer(serializers.ModelSerializer):
    """
    Full serializer for quizzes.
    """
    course_name = serializers.CharField(source='course.title', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    question_count = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'course', 'course_name', 'course_code', 'title', 'slug',
            'description', 'category', 'category_display', 'random_order',
            'answers_at_end', 'exam_paper', 'single_attempt', 'pass_mark',
            'draft', 'time_limit', 'question_count', 'timestamp'
        ]
        read_only_fields = ['slug', 'timestamp']

    def get_question_count(self, obj):
        """Get the number of questions in this quiz."""
        return obj.question_set.count()


class QuizListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing quizzes.
    """
    course_name = serializers.CharField(source='course.title', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'slug', 'course_name', 'category', 'category_display',
            'pass_mark', 'time_limit', 'question_count', 'draft'
        ]

    def get_question_count(self, obj):
        """Get the number of questions in this quiz."""
        return obj.question_set.count()


class QuizCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating quizzes.
    """
    class Meta:
        model = Quiz
        fields = [
            'course', 'title', 'description', 'category', 'random_order',
            'answers_at_end', 'exam_paper', 'single_attempt', 'pass_mark',
            'draft', 'time_limit'
        ]

    def validate_pass_mark(self, value):
        """Ensure pass mark is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError('Pass mark must be between 0 and 100.')
        return value


# ============================================================================
# QUESTION SERIALIZERS
# ============================================================================

class QuestionSerializer(serializers.ModelSerializer):
    """
    Base serializer for questions.
    """
    figure_url = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'quiz', 'figure', 'figure_url', 'content',
            'explanation'
        ]

    def get_figure_url(self, obj):
        """Return figure URL if exists."""
        if obj.figure:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.figure.url)
        return None


class MCQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for multiple choice questions.
    """
    figure_url = serializers.SerializerMethodField()

    class Meta:
        model = MCQuestion
        fields = [
            'id', 'quiz', 'figure', 'figure_url', 'content',
            'explanation', 'choice_order'
        ]

    def get_figure_url(self, obj):
        """Return figure URL if exists."""
        if obj.figure:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.figure.url)
        return None


class EssayQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for essay questions.
    """

    class Meta:
        model = EssayQuestion
        fields = [
            'id', 'quiz', 'content', 'explanation'
        ]


# ============================================================================
# SITTING SERIALIZERS
# ============================================================================

class SittingSerializer(serializers.ModelSerializer):
    """
    Serializer for quiz attempts (sittings).
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Sitting
        fields = [
            'id', 'user', 'user_name', 'quiz', 'quiz_title', 'question_order',
            'question_list', 'incorrect_questions', 'current_score',
            'complete', 'user_answers', 'start', 'end', 'percentage'
        ]
        read_only_fields = [
            'user', 'start', 'end', 'current_score', 'complete'
        ]

    def get_percentage(self, obj):
        """Calculate percentage score."""
        return obj.get_percent_correct


class SittingListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing sittings.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Sitting
        fields = [
            'id', 'user_name', 'quiz_title', 'current_score',
            'complete', 'start', 'end', 'percentage'
        ]

    def get_percentage(self, obj):
        """Calculate percentage score."""
        return obj.get_percent_correct


# ============================================================================
# PROGRESS SERIALIZERS
# ============================================================================

class ProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for student progress tracking.
    """
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Progress
        fields = [
            'id', 'user', 'user_name', 'score'
        ]
        read_only_fields = ['user']
