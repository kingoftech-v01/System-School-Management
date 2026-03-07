"""
Admin configuration for grading app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import GradingRubric, RubricCriterion, RubricGrade, CriterionGrade, PeerReview, GradeCurve


class RubricCriterionInline(admin.TabularInline):
    """Inline admin for rubric criteria."""
    model = RubricCriterion
    extra = 1
    fields = ('name', 'description', 'max_points', 'weight', 'order')


@admin.register(GradingRubric)
class GradingRubricAdmin(admin.ModelAdmin):
    """Admin for grading rubrics."""
    list_display = ('name', 'course', 'max_score', 'passing_score',
                    'is_active', 'allow_partial_credit', 'created_at')
    list_filter = ('is_active', 'allow_partial_credit', 'created_at')
    search_fields = ('name', 'description', 'course__name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'get_criteria_count')
    inlines = [RubricCriterionInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Rubric Information', {
            'fields': ('name', 'description', 'course')
        }),
        ('Scoring Configuration', {
            'fields': ('max_score', 'passing_score', 'allow_partial_credit')
        }),
        ('Management', {
            'fields': ('created_by', 'is_active')
        }),
        ('Statistics', {
            'fields': ('get_criteria_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_rubrics', 'deactivate_rubrics', 'duplicate_rubric']

    def activate_rubrics(self, request, queryset):
        queryset.update(is_active=True)
    activate_rubrics.short_description = "Activate selected rubrics"

    def deactivate_rubrics(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_rubrics.short_description = "Deactivate selected rubrics"

    def duplicate_rubric(self, request, queryset):
        for rubric in queryset:
            # Get criteria before duplicating
            criteria = list(rubric.criteria.all())

            # Duplicate rubric
            rubric.pk = None
            rubric.name = f"{rubric.name} (Copy)"
            rubric.is_active = False
            rubric.save()

            # Duplicate criteria
            for criterion in criteria:
                criterion.pk = None
                criterion.rubric = rubric
                criterion.save()

        self.message_user(request, f"Duplicated {queryset.count()} rubric(s)")
    duplicate_rubric.short_description = "Duplicate selected rubrics"

    def get_criteria_count(self, obj):
        return obj.criteria.count()
    get_criteria_count.short_description = 'Criteria Count'


@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    """Admin for rubric criteria."""
    list_display = ('name', 'rubric', 'max_points', 'weight', 'order')
    list_filter = ('rubric__course',)
    search_fields = ('name', 'description', 'rubric__name')
    readonly_fields = ()

    fieldsets = (
        ('Criterion Information', {
            'fields': ('rubric', 'name', 'description', 'order')
        }),
        ('Scoring', {
            'fields': ('max_points', 'weight')
        }),
        ('Achievement Level Descriptions', {
            'fields': ('excellent_description', 'good_description',
                      'satisfactory_description', 'needs_improvement_description'),
            'classes': ('collapse',)
        }),
    )


class CriterionGradeInline(admin.TabularInline):
    """Inline admin for criterion grades."""
    model = CriterionGrade
    extra = 0
    fields = ('criterion', 'score', 'feedback')
    readonly_fields = ()


@admin.register(RubricGrade)
class RubricGradeAdmin(admin.ModelAdmin):
    """Admin for applied rubric grades."""
    list_display = ('student', 'rubric', 'graded_by', 'total_score', 'percentage',
                    'get_grade_display', 'graded_at')
    list_filter = ('rubric__course', 'graded_at')
    search_fields = ('student__student__first_name', 'student__student__last_name',
                    'rubric__name', 'assignment_name')
    readonly_fields = ('total_score', 'percentage', 'graded_at', 'get_criterion_breakdown')
    inlines = [CriterionGradeInline]
    date_hierarchy = 'graded_at'

    fieldsets = (
        ('Grade Information', {
            'fields': ('student', 'rubric', 'assignment_name', 'graded_by')
        }),
        ('Scores', {
            'fields': ('total_score', 'percentage', 'get_criterion_breakdown'),
            'classes': ('collapse',)
        }),
        ('Feedback', {
            'fields': ('overall_feedback',)
        }),
        ('Timestamp', {
            'fields': ('graded_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['recalculate_grades']

    def recalculate_grades(self, request, queryset):
        count = 0
        for grade in queryset:
            grade.calculate_grade()
            count += 1
        self.message_user(request, f"Recalculated {count} grade(s)")
    recalculate_grades.short_description = "Recalculate selected grades"

    def get_grade_display(self, obj):
        percentage = float(obj.percentage)
        if percentage >= 90:
            color, grade = 'green', 'A'
        elif percentage >= 80:
            color, grade = 'lightgreen', 'B'
        elif percentage >= 70:
            color, grade = 'orange', 'C'
        elif percentage >= 60:
            color, grade = 'darkorange', 'D'
        else:
            color, grade = 'red', 'F'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({:.1f}%)</span>',
            color, grade, percentage
        )
    get_grade_display.short_description = 'Grade'

    def get_criterion_breakdown(self, obj):
        breakdown = []
        for criterion_grade in obj.criterion_grades.all():
            breakdown.append(f"{criterion_grade.criterion.name}: {criterion_grade.score}/{criterion_grade.criterion.max_points}")
        return ", ".join(breakdown) if breakdown else "No criteria graded"
    get_criterion_breakdown.short_description = 'Criterion Breakdown'


@admin.register(CriterionGrade)
class CriterionGradeAdmin(admin.ModelAdmin):
    """Admin for individual criterion grades."""
    list_display = ('rubric_grade', 'criterion', 'score', 'get_max_points', 'get_percentage')
    list_filter = ('criterion__rubric__course',)
    search_fields = ('rubric_grade__student__student__first_name', 'rubric_grade__student__student__last_name',
                    'criterion__name', 'feedback')
    readonly_fields = ('get_max_points', 'get_percentage')

    fieldsets = (
        ('Grade Information', {
            'fields': ('rubric_grade', 'criterion', 'score')
        }),
        ('Feedback', {
            'fields': ('feedback',)
        }),
        ('Statistics', {
            'fields': ('get_max_points', 'get_percentage'),
            'classes': ('collapse',)
        }),
    )

    def get_max_points(self, obj):
        return obj.criterion.max_points
    get_max_points.short_description = 'Max Points'

    def get_percentage(self, obj):
        if obj.criterion.max_points > 0:
            percentage = (obj.score / obj.criterion.max_points) * 100
            color = 'green' if percentage >= 80 else 'orange' if percentage >= 60 else 'red'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, percentage)
        return 'N/A'
    get_percentage.short_description = 'Percentage'


@admin.register(PeerReview)
class PeerReviewAdmin(admin.ModelAdmin):
    """Admin for peer reviews."""
    list_display = ('reviewer', 'reviewee', 'assignment_name', 'status', 'is_anonymous',
                    'score', 'deadline', 'submitted_at')
    list_filter = ('status', 'is_anonymous', 'deadline', 'submitted_at')
    search_fields = ('reviewer__student__first_name', 'reviewee__student__first_name',
                    'assignment_name', 'feedback')
    readonly_fields = ('submitted_at',)
    date_hierarchy = 'deadline'

    fieldsets = (
        ('Review Information', {
            'fields': ('assignment_name', 'reviewer', 'reviewee', 'is_anonymous')
        }),
        ('Assignment Details', {
            'fields': ('assignment_description', 'deadline')
        }),
        ('Review Content', {
            'fields': ('status', 'score', 'feedback', 'submitted_at')
        }),
    )

    actions = ['mark_pending', 'mark_completed']

    def mark_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_pending.short_description = "Mark as pending"

    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='completed', submitted_at=timezone.now())
    mark_completed.short_description = "Mark as completed"


@admin.register(GradeCurve)
class GradeCurveAdmin(admin.ModelAdmin):
    """Admin for grade curves."""
    list_display = ('course', 'assignment_name', 'curve_type', 'get_student_count',
                    'mean_before', 'mean_after', 'applied_at')
    list_filter = ('curve_type', 'applied_at')
    search_fields = ('course__name', 'assignment_name', 'applied_by__username')
    readonly_fields = ('applied_at', 'get_student_count', 'get_improvement')
    date_hierarchy = 'applied_at'

    fieldsets = (
        ('Curve Information', {
            'fields': ('course', 'assignment_name', 'curve_type', 'applied_by')
        }),
        ('Custom Parameters', {
            'fields': ('custom_parameters',),
            'classes': ('collapse',),
            'description': 'JSON parameters for custom curve types'
        }),
        ('Statistics Before', {
            'fields': ('mean_before', 'median_before', 'std_dev_before'),
            'classes': ('collapse',)
        }),
        ('Statistics After', {
            'fields': ('mean_after', 'median_after', 'std_dev_after'),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('get_student_count', 'get_improvement'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('applied_at',),
            'classes': ('collapse',)
        }),
    )

    def get_student_count(self, obj):
        return obj.students_affected.count()
    get_student_count.short_description = 'Students Affected'

    def get_improvement(self, obj):
        if obj.mean_before and obj.mean_after:
            improvement = float(obj.mean_after - obj.mean_before)
            color = 'green' if improvement > 0 else 'red' if improvement < 0 else 'gray'
            return format_html('<span style="color: {};">{:+.2f} points</span>', color, improvement)
        return 'N/A'
    get_improvement.short_description = 'Mean Improvement'
