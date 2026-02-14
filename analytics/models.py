"""
Course Analytics app models.
Student engagement tracking and learning outcomes analysis.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class StudentEngagement(models.Model):
    """Daily student engagement metrics."""
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='engagement_metrics'
    )
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='engagement_metrics',
        null=True,
        blank=True
    )
    date = models.DateField(default=timezone.now)

    # Activity metrics
    login_count = models.PositiveIntegerField(default=0)
    total_time_minutes = models.PositiveIntegerField(default=0)

    # Content engagement
    pages_viewed = models.PositiveIntegerField(default=0)
    videos_watched = models.PositiveIntegerField(default=0)
    documents_downloaded = models.PositiveIntegerField(default=0)

    # Interaction metrics
    forum_posts = models.PositiveIntegerField(default=0)
    forum_replies = models.PositiveIntegerField(default=0)
    questions_asked = models.PositiveIntegerField(default=0)
    questions_answered = models.PositiveIntegerField(default=0)

    # Assessment activity
    quizzes_attempted = models.PositiveIntegerField(default=0)
    quizzes_completed = models.PositiveIntegerField(default=0)
    assignments_submitted = models.PositiveIntegerField(default=0)

    # Engagement score (0-100)
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'course', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['student', '-date']),
            models.Index(fields=['course', '-date']),
            models.Index(fields=['-engagement_score']),
        ]

    def __str__(self):
        return f"{self.student} - {self.date}: {self.engagement_score}"

    def calculate_engagement_score(self):
        """Calculate engagement score based on activities."""
        score = 0

        # Login activity (max 20 points)
        score += min(self.login_count * 5, 20)

        # Time spent (max 20 points)
        score += min(self.total_time_minutes / 3, 20)

        # Content engagement (max 20 points)
        content_score = (self.pages_viewed * 2) + (self.videos_watched * 5) + (self.documents_downloaded * 3)
        score += min(content_score, 20)

        # Interaction (max 20 points)
        interaction_score = (self.forum_posts * 5) + (self.forum_replies * 3) + (self.questions_asked * 4)
        score += min(interaction_score, 20)

        # Assessments (max 20 points)
        assessment_score = (self.quizzes_completed * 7) + (self.assignments_submitted * 10)
        score += min(assessment_score, 20)

        self.engagement_score = min(score, 100)
        self.save()


class CourseCompletion(models.Model):
    """Course completion tracking."""
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='course_completions'
    )
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='completions'
    )

    # Progress
    enrolled_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Completion metrics
    total_modules = models.PositiveIntegerField(default=0)
    completed_modules = models.PositiveIntegerField(default=0)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Time tracking
    total_time_spent = models.PositiveIntegerField(default=0, help_text="Total minutes spent")
    last_activity_at = models.DateTimeField(null=True, blank=True)

    # Status
    is_completed = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)

    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student', 'is_completed']),
            models.Index(fields=['course', '-completion_percentage']),
        ]

    def __str__(self):
        return f"{self.student} - {self.course}: {self.completion_percentage}%"

    def update_progress(self):
        """Update completion percentage."""
        if self.total_modules > 0:
            self.completion_percentage = (self.completed_modules / self.total_modules) * 100
            if self.completion_percentage >= 100 and not self.is_completed:
                self.is_completed = True
                self.completed_at = timezone.now()
            self.save()


class LearningOutcome(models.Model):
    """Learning outcome measurements."""
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='learning_outcomes'
    )

    outcome_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Measurement criteria
    assessment_method = models.CharField(
        max_length=50,
        choices=(
            ('quiz', 'Quiz'),
            ('assignment', 'Assignment'),
            ('project', 'Project'),
            ('exam', 'Exam'),
            ('discussion', 'Discussion Participation'),
        )
    )

    # Target metrics
    target_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=70)

    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course', 'outcome_name']

    def __str__(self):
        return f"{self.course} - {self.outcome_name}"


class OutcomeMeasurement(models.Model):
    """Individual outcome measurements."""
    outcome = models.ForeignKey(
        LearningOutcome,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='outcome_measurements'
    )

    # Measurement data
    score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    # Assessment reference
    assessment_name = models.CharField(max_length=200)
    assessed_at = models.DateTimeField(default=timezone.now)

    # Result
    meets_target = models.BooleanField(default=False)

    class Meta:
        ordering = ['-assessed_at']
        indexes = [
            models.Index(fields=['outcome', 'meets_target']),
            models.Index(fields=['student', '-assessed_at']),
        ]

    def __str__(self):
        return f"{self.student} - {self.outcome}: {self.percentage}%"

    def save(self, *args, **kwargs):
        if self.max_score > 0:
            self.percentage = (self.score / self.max_score) * 100
            self.meets_target = self.percentage >= self.outcome.target_percentage
        super().save(*args, **kwargs)


class ActivityLog(models.Model):
    """Detailed activity tracking."""
    ACTIVITY_TYPE_CHOICES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('page_view', 'Page View'),
        ('video_view', 'Video View'),
        ('download', 'File Download'),
        ('quiz_start', 'Quiz Started'),
        ('quiz_submit', 'Quiz Submitted'),
        ('assignment_submit', 'Assignment Submitted'),
        ('forum_post', 'Forum Post'),
        ('forum_reply', 'Forum Reply'),
        ('search', 'Search'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )

    # Activity details
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    activity_description = models.TextField(blank=True)

    # Context
    url = models.URLField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Duration (for timed activities)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional activity data")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', '-created_at']),
            models.Index(fields=['course', 'activity_type', '-created_at']),
            models.Index(fields=['activity_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.student} - {self.get_activity_type_display()} at {self.created_at}"


class AtRiskStudent(models.Model):
    """Students identified as at-risk."""
    RISK_LEVEL_CHOICES = (
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical'),
    )

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='risk_assessments'
    )
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='at_risk_students'
    )

    # Risk assessment
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="0-100 scale")

    # Risk factors
    low_engagement = models.BooleanField(default=False)
    low_attendance = models.BooleanField(default=False)
    failing_grades = models.BooleanField(default=False)
    no_recent_activity = models.BooleanField(default=False)
    missing_assignments = models.PositiveIntegerField(default=0)

    # Intervention
    intervention_needed = models.BooleanField(default=True)
    intervention_notes = models.TextField(blank=True)
    contacted_at = models.DateTimeField(null=True, blank=True)
    contacted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacted_students'
    )

    # Status
    is_active = models.BooleanField(default=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    identified_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-risk_score', '-identified_at']
        indexes = [
            models.Index(fields=['course', '-risk_score']),
            models.Index(fields=['risk_level', 'is_active']),
        ]

    def __str__(self):
        return f"{self.student} - {self.course}: {self.get_risk_level_display()}"

    def calculate_risk_score(self):
        """Calculate risk score based on factors."""
        score = 0

        if self.low_engagement:
            score += 25
        if self.low_attendance:
            score += 25
        if self.failing_grades:
            score += 30
        if self.no_recent_activity:
            score += 15
        score += min(self.missing_assignments * 5, 20)

        self.risk_score = min(score, 100)

        # Set risk level based on score
        if self.risk_score >= 75:
            self.risk_level = 'critical'
        elif self.risk_score >= 50:
            self.risk_level = 'high'
        elif self.risk_score >= 25:
            self.risk_level = 'medium'
        else:
            self.risk_level = 'low'

        self.save()


class Insight(models.Model):
    """
    Computed insights generated by the analytics engine.
    Provides actionable intelligence for direction/admin users.
    """
    INSIGHT_TYPES = (
        ('attendance_anomaly', 'Attendance Anomaly'),
        ('engagement_drop', 'Engagement Drop'),
        ('payment_shortfall', 'Payment Shortfall'),
        ('risk_cluster', 'At-Risk Cluster'),
        ('grade_trend', 'Grade Trend'),
    )
    SEVERITY_CHOICES = (
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    )

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE,
        null=True, blank=True, related_name='insights'
    )
    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPES)
    title = models.CharField(max_length=300)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    dismissed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='dismissed_insights'
    )
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['insight_type', 'is_active']),
            models.Index(fields=['-generated_at']),
        ]

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"
