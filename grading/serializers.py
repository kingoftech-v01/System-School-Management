"""
Serializers for grading app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import GradingRubric, RubricCriterion, RubricGrade, CriterionGrade, PeerReview, GradeCurve

User = get_user_model()


class RubricCriterionSerializer(serializers.ModelSerializer):
    """Serializer for rubric criteria."""
    class Meta:
        model = RubricCriterion
        fields = ['id', 'rubric', 'name', 'description', 'max_points', 'weight',
                 'order', 'is_required', 'excellent_description', 'good_description',
                 'satisfactory_description', 'needs_improvement_description']
        read_only_fields = []

    def validate_weight(self, value):
        """Ensure weight is between 0 and 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Weight must be between 0 and 100.")
        return value


class GradingRubricSerializer(serializers.ModelSerializer):
    """Serializer for grading rubrics."""
    criteria = RubricCriterionSerializer(many=True, read_only=True)
    criteria_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    total_weight = serializers.SerializerMethodField()

    class Meta:
        model = GradingRubric
        fields = ['id', 'name', 'description', 'course', 'course_name',
                 'assignment_type', 'max_score', 'passing_score',
                 'allow_partial_credit', 'is_active', 'created_by',
                 'created_by_name', 'criteria', 'criteria_count', 'total_weight',
                 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_criteria_count(self, obj):
        return obj.criteria.count()

    def get_total_weight(self, obj):
        """Calculate total weight of all criteria."""
        total = sum(criterion.weight for criterion in obj.criteria.all())
        return float(total)

    def create(self, validated_data):
        """Create rubric with creator."""
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        return GradingRubric.objects.create(**validated_data)

    def validate(self, data):
        """Ensure passing score doesn't exceed max score."""
        max_score = data.get('max_score', Decimal('100.00'))
        passing_score = data.get('passing_score', Decimal('70.00'))

        if passing_score > max_score:
            raise serializers.ValidationError(
                "Passing score cannot exceed maximum score."
            )
        return data


class RubricCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating rubrics with nested criteria."""
    criteria = RubricCriterionSerializer(many=True, write_only=True)

    class Meta:
        model = GradingRubric
        fields = ['name', 'description', 'course', 'assignment_type',
                 'max_score', 'passing_score', 'allow_partial_credit',
                 'is_active', 'criteria']

    def create(self, validated_data):
        criteria_data = validated_data.pop('criteria', [])
        request = self.context.get('request')
        validated_data['created_by'] = request.user

        rubric = GradingRubric.objects.create(**validated_data)

        # Create criteria
        for criterion_data in criteria_data:
            RubricCriterion.objects.create(rubric=rubric, **criterion_data)

        return rubric


class CriterionGradeSerializer(serializers.ModelSerializer):
    """Serializer for criterion grades."""
    criterion_name = serializers.CharField(source='criterion.name', read_only=True)
    max_points = serializers.DecimalField(source='criterion.max_points', max_digits=5, decimal_places=2, read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = CriterionGrade
        fields = ['id', 'rubric_grade', 'criterion', 'criterion_name',
                 'score', 'max_points', 'percentage', 'feedback']
        read_only_fields = []

    def get_percentage(self, obj):
        if obj.criterion.max_points > 0:
            return round((obj.score / obj.criterion.max_points) * 100, 2)
        return 0


class RubricGradeSerializer(serializers.ModelSerializer):
    """Serializer for rubric grades."""
    student_name = serializers.CharField(source='student.student.get_full_name', read_only=True)
    rubric_name = serializers.CharField(source='rubric.name', read_only=True)
    graded_by_name = serializers.CharField(source='graded_by.get_full_name', read_only=True)
    criterion_grades = CriterionGradeSerializer(many=True, read_only=True)
    letter_grade = serializers.SerializerMethodField()

    class Meta:
        model = RubricGrade
        fields = ['id', 'student', 'student_name', 'rubric', 'rubric_name',
                 'assignment_name', 'graded_by', 'graded_by_name', 'total_score',
                 'percentage', 'letter_grade', 'overall_feedback',
                 'criterion_grades', 'graded_at']
        read_only_fields = ['graded_by', 'total_score', 'percentage', 'graded_at']

    def get_letter_grade(self, obj):
        """Convert percentage to letter grade."""
        percentage = float(obj.percentage)
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'

    def create(self, validated_data):
        """Create grade with grader."""
        request = self.context.get('request')
        validated_data['graded_by'] = request.user
        return RubricGrade.objects.create(**validated_data)


class RubricGradeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating grades with criterion grades."""
    criterion_grades = CriterionGradeSerializer(many=True, write_only=True)

    class Meta:
        model = RubricGrade
        fields = ['student', 'rubric', 'assignment_name', 'overall_feedback', 'criterion_grades']

    def create(self, validated_data):
        criterion_grades_data = validated_data.pop('criterion_grades', [])
        request = self.context.get('request')
        validated_data['graded_by'] = request.user

        # Create rubric grade
        rubric_grade = RubricGrade.objects.create(**validated_data)

        # Create criterion grades
        for criterion_grade_data in criterion_grades_data:
            CriterionGrade.objects.create(
                rubric_grade=rubric_grade,
                **criterion_grade_data
            )

        # Calculate total score
        rubric_grade.calculate_grade()

        return rubric_grade


class PeerReviewSerializer(serializers.ModelSerializer):
    """Serializer for peer reviews."""
    reviewer_name = serializers.SerializerMethodField()
    reviewee_name = serializers.CharField(source='reviewee.student.get_full_name', read_only=True)

    class Meta:
        model = PeerReview
        fields = ['id', 'assignment_name', 'assignment_description', 'reviewer',
                 'reviewer_name', 'reviewee', 'reviewee_name', 'is_anonymous',
                 'deadline', 'status', 'score', 'feedback', 'submitted_at']
        read_only_fields = ['submitted_at']

    def get_reviewer_name(self, obj):
        """Return anonymous if review is anonymous, otherwise return name."""
        if obj.is_anonymous:
            return 'Anonymous'
        return obj.reviewer.student.get_full_name


class PeerReviewSubmitSerializer(serializers.Serializer):
    """Serializer for submitting peer reviews."""
    score = serializers.DecimalField(max_digits=5, decimal_places=2, required=True)
    feedback = serializers.CharField(required=True)

    def validate_score(self, value):
        """Ensure score is within valid range."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value


class GradeCurveSerializer(serializers.ModelSerializer):
    """Serializer for grade curves."""
    course_name = serializers.CharField(source='course.name', read_only=True)
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    students_affected_count = serializers.SerializerMethodField()
    mean_improvement = serializers.SerializerMethodField()

    class Meta:
        model = GradeCurve
        fields = ['id', 'course', 'course_name', 'assignment_name', 'curve_type',
                 'applied_by', 'applied_by_name', 'custom_parameters',
                 'mean_before', 'median_before', 'std_dev_before',
                 'mean_after', 'median_after', 'std_dev_after',
                 'students_affected_count', 'mean_improvement', 'applied_at']
        read_only_fields = ['applied_by', 'mean_before', 'median_before', 'std_dev_before',
                           'mean_after', 'median_after', 'std_dev_after', 'applied_at']

    def get_students_affected_count(self, obj):
        return obj.students_affected.count()

    def get_mean_improvement(self, obj):
        if obj.mean_before and obj.mean_after:
            return round(float(obj.mean_after - obj.mean_before), 2)
        return None

    def create(self, validated_data):
        """Create curve with applier."""
        request = self.context.get('request')
        validated_data['applied_by'] = request.user
        return GradeCurve.objects.create(**validated_data)
