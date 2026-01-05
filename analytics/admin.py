"""
Admin configuration for analytics app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import StudentEngagement, CourseCompletion, LearningOutcome, OutcomeMeasurement, ActivityLog, AtRiskStudent


@admin.register(StudentEngagement)
class StudentEngagementAdmin(admin.ModelAdmin):
    """Admin for student engagement metrics."""
    list_display = ('student', 'course', 'date', 'engagement_score', 'login_count',
                    'total_time_minutes', 'get_activity_summary', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('student__student__first_name', 'student__student__last_name', 'course__name')
    readonly_fields = ('engagement_score', 'created_at', 'updated_at', 'get_engagement_level')
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('student', 'course', 'date')
        }),
        ('Activity Metrics', {
            'fields': ('login_count', 'total_time_minutes')
        }),
        ('Content Engagement', {
            'fields': ('pages_viewed', 'videos_watched', 'documents_downloaded')
        }),
        ('Interaction Metrics', {
            'fields': ('forum_posts', 'forum_replies', 'questions_asked', 'questions_answered')
        }),
        ('Assessment Activity', {
            'fields': ('quizzes_attempted', 'quizzes_completed', 'assignments_submitted')
        }),
        ('Engagement Score', {
            'fields': ('engagement_score', 'get_engagement_level'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['recalculate_engagement_scores']

    def recalculate_engagement_scores(self, request, queryset):
        count = 0
        for engagement in queryset:
            engagement.calculate_engagement_score()
            count += 1
        self.message_user(request, f"Recalculated engagement scores for {count} record(s)")
    recalculate_engagement_scores.short_description = "Recalculate engagement scores"

    def get_activity_summary(self, obj):
        return format_html(
            'Pages: {} | Videos: {} | Forums: {}',
            obj.pages_viewed, obj.videos_watched, obj.forum_posts + obj.forum_replies
        )
    get_activity_summary.short_description = 'Activity Summary'

    def get_engagement_level(self, obj):
        score = float(obj.engagement_score)
        if score >= 80:
            return format_html('<span style="color: green; font-weight: bold;">🟢 High ({:.1f})</span>', score)
        elif score >= 50:
            return format_html('<span style="color: orange; font-weight: bold;">🟡 Medium ({:.1f})</span>', score)
        else:
            return format_html('<span style="color: red; font-weight: bold;">🔴 Low ({:.1f})</span>', score)
    get_engagement_level.short_description = 'Engagement Level'


@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    """Admin for course completion tracking."""
    list_display = ('student', 'course', 'completion_percentage', 'is_completed',
                    'certificate_issued', 'enrolled_at', 'completed_at')
    list_filter = ('is_completed', 'certificate_issued', 'enrolled_at', 'completed_at')
    search_fields = ('student__student__first_name', 'student__student__last_name', 'course__name')
    readonly_fields = ('completion_percentage', 'enrolled_at', 'last_activity_at', 'get_progress_bar',
                      'get_time_spent_display')
    date_hierarchy = 'enrolled_at'

    fieldsets = (
        ('Student & Course', {
            'fields': ('student', 'course')
        }),
        ('Progress', {
            'fields': ('total_modules', 'completed_modules', 'completion_percentage', 'get_progress_bar')
        }),
        ('Status', {
            'fields': ('is_completed', 'certificate_issued')
        }),
        ('Time Tracking', {
            'fields': ('enrolled_at', 'started_at', 'completed_at', 'last_activity_at',
                      'total_time_spent', 'get_time_spent_display'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_completed', 'issue_certificates', 'update_progress']

    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_completed=True, completed_at=timezone.now())
    mark_completed.short_description = "Mark as completed"

    def issue_certificates(self, request, queryset):
        queryset.filter(is_completed=True).update(certificate_issued=True)
    issue_certificates.short_description = "Issue certificates"

    def update_progress(self, request, queryset):
        count = 0
        for completion in queryset:
            completion.update_progress()
            count += 1
        self.message_user(request, f"Updated progress for {count} completion record(s)")
    update_progress.short_description = "Update completion progress"

    def get_progress_bar(self, obj):
        percentage = float(obj.completion_percentage)
        color = 'green' if percentage == 100 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<div style="width:200px; background-color:#f0f0f0; border-radius:5px; border:1px solid #ccc;">'
            '<div style="width:{}%; background-color:{}; color:white; text-align:center; '
            'padding:5px 0; border-radius:5px; font-weight:bold;">{:.1f}%</div></div>',
            percentage, color, percentage
        )
    get_progress_bar.short_description = 'Progress'

    def get_time_spent_display(self, obj):
        hours = obj.total_time_spent // 60
        minutes = obj.total_time_spent % 60
        return f"{hours}h {minutes}m"
    get_time_spent_display.short_description = 'Total Time Spent'


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    """Admin for learning outcomes."""
    list_display = ('outcome_name', 'course', 'assessment_method', 'target_percentage',
                    'is_active', 'created_at')
    list_filter = ('assessment_method', 'is_active', 'created_at')
    search_fields = ('outcome_name', 'description', 'course__name')
    readonly_fields = ('created_at', 'get_achievement_rate')

    fieldsets = (
        ('Outcome Information', {
            'fields': ('course', 'outcome_name', 'description')
        }),
        ('Assessment Configuration', {
            'fields': ('assessment_method', 'target_percentage')
        }),
        ('Status & Statistics', {
            'fields': ('is_active', 'get_achievement_rate'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_outcomes', 'deactivate_outcomes']

    def activate_outcomes(self, request, queryset):
        queryset.update(is_active=True)
    activate_outcomes.short_description = "Activate selected outcomes"

    def deactivate_outcomes(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_outcomes.short_description = "Deactivate selected outcomes"

    def get_achievement_rate(self, obj):
        total = obj.measurements.count()
        if total == 0:
            return 'No measurements yet'
        achieved = obj.measurements.filter(meets_target=True).count()
        rate = (achieved / total) * 100
        color = 'green' if rate >= 70 else 'orange' if rate >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/{} ({:.1f}%)</span>',
            color, achieved, total, rate
        )
    get_achievement_rate.short_description = 'Achievement Rate'


@admin.register(OutcomeMeasurement)
class OutcomeMeasurementAdmin(admin.ModelAdmin):
    """Admin for outcome measurements."""
    list_display = ('student', 'outcome', 'assessment_name', 'score', 'max_score',
                    'percentage', 'meets_target', 'assessed_at')
    list_filter = ('meets_target', 'assessed_at', 'outcome__assessment_method')
    search_fields = ('student__student__first_name', 'student__student__last_name',
                    'outcome__outcome_name', 'assessment_name')
    readonly_fields = ('percentage', 'meets_target', 'assessed_at', 'get_performance_indicator')
    date_hierarchy = 'assessed_at'

    fieldsets = (
        ('Measurement Information', {
            'fields': ('student', 'outcome', 'assessment_name')
        }),
        ('Scores', {
            'fields': ('score', 'max_score', 'percentage', 'meets_target', 'get_performance_indicator')
        }),
        ('Timestamp', {
            'fields': ('assessed_at',),
            'classes': ('collapse',)
        }),
    )

    def get_performance_indicator(self, obj):
        percentage = float(obj.percentage)
        target = float(obj.outcome.target_percentage)

        if obj.meets_target:
            return format_html(
                '<span style="color: green;">✓ Exceeds Target ({:.1f}% ≥ {:.1f}%)</span>',
                percentage, target
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Below Target ({:.1f}% < {:.1f}%)</span>',
                percentage, target
            )
    get_performance_indicator.short_description = 'Performance'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for activity logs."""
    list_display = ('student', 'activity_type', 'course', 'get_short_description',
                    'duration_seconds', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('student__student__first_name', 'student__student__last_name',
                    'activity_description', 'url')
    readonly_fields = ('created_at', 'get_duration_display')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Activity Information', {
            'fields': ('student', 'course', 'activity_type', 'activity_description')
        }),
        ('Context Details', {
            'fields': ('url', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Duration & Metadata', {
            'fields': ('duration_seconds', 'get_duration_display', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def get_short_description(self, obj):
        if obj.activity_description:
            return obj.activity_description[:50] + '...' if len(obj.activity_description) > 50 else obj.activity_description
        return '-'
    get_short_description.short_description = 'Description'

    def get_duration_display(self, obj):
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        return 'N/A'
    get_duration_display.short_description = 'Duration'


@admin.register(AtRiskStudent)
class AtRiskStudentAdmin(admin.ModelAdmin):
    """Admin for at-risk students."""
    list_display = ('student', 'course', 'risk_level', 'risk_score', 'get_risk_factors',
                    'intervention_needed', 'is_active', 'identified_at')
    list_filter = ('risk_level', 'intervention_needed', 'is_active', 'identified_at')
    search_fields = ('student__student__first_name', 'student__student__last_name',
                    'course__name', 'intervention_notes')
    readonly_fields = ('risk_score', 'risk_level', 'identified_at', 'updated_at', 'get_risk_visual')
    date_hierarchy = 'identified_at'

    fieldsets = (
        ('Student & Course', {
            'fields': ('student', 'course')
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'risk_score', 'get_risk_visual')
        }),
        ('Risk Factors', {
            'fields': ('low_engagement', 'low_attendance', 'failing_grades',
                      'no_recent_activity', 'missing_assignments')
        }),
        ('Intervention', {
            'fields': ('intervention_needed', 'intervention_notes',
                      'contacted_at', 'contacted_by')
        }),
        ('Status', {
            'fields': ('is_active', 'resolved_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('identified_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['recalculate_risk_scores', 'mark_intervention_needed', 'mark_resolved']

    def recalculate_risk_scores(self, request, queryset):
        count = 0
        for at_risk in queryset:
            at_risk.calculate_risk_score()
            count += 1
        self.message_user(request, f"Recalculated risk scores for {count} student(s)")
    recalculate_risk_scores.short_description = "Recalculate risk scores"

    def mark_intervention_needed(self, request, queryset):
        queryset.update(intervention_needed=True)
    mark_intervention_needed.short_description = "Mark intervention needed"

    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_active=False, resolved_at=timezone.now())
    mark_resolved.short_description = "Mark as resolved"

    def get_risk_factors(self, obj):
        factors = []
        if obj.low_engagement:
            factors.append('Low Engagement')
        if obj.low_attendance:
            factors.append('Low Attendance')
        if obj.failing_grades:
            factors.append('Failing Grades')
        if obj.no_recent_activity:
            factors.append('No Activity')
        if obj.missing_assignments > 0:
            factors.append(f'{obj.missing_assignments} Missing')

        if factors:
            return format_html('<span style="color: red;">{}</span>', ', '.join(factors))
        return 'None'
    get_risk_factors.short_description = 'Risk Factors'

    def get_risk_visual(self, obj):
        score = float(obj.risk_score)
        level = obj.risk_level

        # Color coding
        if level == 'critical':
            color, icon = '#d32f2f', '🔴'
        elif level == 'high':
            color, icon = '#f57c00', '🟠'
        elif level == 'medium':
            color, icon = '#fbc02d', '🟡'
        else:
            color, icon = '#689f38', '🟢'

        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<span style="font-size: 24px;">{}</span>'
            '<div style="width:200px; background-color:#f0f0f0; border-radius:5px; border:1px solid #ccc;">'
            '<div style="width:{}%; background-color:{}; color:white; text-align:center; '
            'padding:5px 0; border-radius:5px; font-weight:bold;">{:.1f}</div></div>'
            '<span style="color: {}; font-weight: bold;">{}</span>'
            '</div>',
            icon, score, color, score, color, obj.get_risk_level_display()
        )
    get_risk_visual.short_description = 'Risk Level Visualization'
