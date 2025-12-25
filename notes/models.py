"""
Models for professor notes with approval workflow.
Notes cannot be deleted after approval, only updated with audit trail.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class ProfessorNote(models.Model):
    """
    Professor notes for students with filiere coefficient and approval workflow.
    Cannot be deleted after approval (soft delete with audit trail).
    """

    NOTE_TYPE_CHOICES = (
        ('participation', _('Class Participation')),
        ('homework', _('Homework/Assignment')),
        ('quiz', _('Quiz')),
        ('midterm', _('Midterm Exam')),
        ('final', _('Final Exam')),
        ('project', _('Project')),
        ('presentation', _('Presentation')),
        ('behavior', _('Behavior')),
        ('attendance', _('Attendance')),
        ('other', _('Other')),
    )

    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('revision_requested', _('Revision Requested')),
    )

    # Tenant relationship
    tenant = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        related_name='professor_notes'
    )

    # Core relationships
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes_received',
        limit_choices_to={'role': 'student'},
        verbose_name=_('Student')
    )
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes_created',
        limit_choices_to={'role__in': ['professor', 'direction']},
        verbose_name=_('Professor')
    )
    filiere = models.ForeignKey(
        'filieres.Filiere',
        on_delete=models.CASCADE,
        verbose_name=_('Filiere/Program')
    )
    subject = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        verbose_name=_('Subject/Course')
    )
    session = models.ForeignKey(
        'core.Session',
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('Academic Session')
    )
    semester = models.ForeignKey(
        'core.Semester',
        on_delete=models.CASCADE,
        null=True,
        verbose_name=_('Semester')
    )

    # Note details
    note_type = models.CharField(
        max_length=50,
        choices=NOTE_TYPE_CHOICES,
        verbose_name=_('Note Type')
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
        verbose_name=_('Score'),
        help_text=_('Score out of 100')
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('100'),
        verbose_name=_('Maximum Score')
    )

    # Coefficient from filiere (auto-populated)
    coefficient = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.1')), MaxValueValidator(Decimal('10'))],
        verbose_name=_('Coefficient'),
        help_text=_('Coefficient from filiere configuration')
    )

    # Weighted score (calculated)
    weighted_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
        verbose_name=_('Weighted Score')
    )

    # Comments and feedback
    comment = models.TextField(
        blank=True,
        verbose_name=_('Professor Comment')
    )
    private_note = models.TextField(
        blank=True,
        verbose_name=_('Private Note'),
        help_text=_('Internal note, not visible to student')
    )

    # Approval workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    submitted_for_approval = models.BooleanField(
        default=False,
        verbose_name=_('Submitted for Approval')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_approved',
        verbose_name=_('Approved By')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approved At')
    )
    approval_notes = models.TextField(
        blank=True,
        verbose_name=_('Approval Notes')
    )

    # Audit trail (cannot delete, only soft delete)
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_('Is Deleted')
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Deleted At')
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_deleted'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notes_modified'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Professor Note')
        verbose_name_plural = _('Professor Notes')
        indexes = [
            models.Index(fields=['tenant', 'student', 'status']),
            models.Index(fields=['filiere', 'subject']),
            models.Index(fields=['session', 'semester']),
            models.Index(fields=['created_at']),
        ]
        permissions = [
            ('approve_note', 'Can approve professor notes'),
            ('view_all_notes', 'Can view all notes'),
        ]

    def __str__(self):
        return f"{self.student.get_full_name} - {self.subject} - {self.get_note_type_display()}"

    def save(self, *args, **kwargs):
        """Calculate weighted score before saving."""
        if self.score is not None and self.coefficient is not None:
            # Normalized score * coefficient
            normalized = (self.score / self.max_score) * 100
            self.weighted_score = normalized * self.coefficient

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Soft delete: Mark as deleted instead of actual deletion."""
        if self.status == 'approved':
            # Cannot delete approved notes, only mark as deleted
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save()
        else:
            # Can actually delete draft/pending notes
            super().delete(*args, **kwargs)

    def can_edit(self, user):
        """Check if user can edit this note."""
        if self.status == 'approved':
            # Only direction can edit approved notes
            return user.role == 'direction' or user.is_superuser
        return self.professor == user or user.role == 'direction' or user.is_superuser

    def can_delete(self, user):
        """Check if user can delete this note."""
        if self.status == 'approved':
            return False  # Cannot delete approved notes
        return self.professor == user or user.role == 'direction' or user.is_superuser

    def submit_for_approval(self):
        """Submit note for approval."""
        if self.status == 'draft':
            self.status = 'pending'
            self.submitted_for_approval = True
            self.save()
            return True
        return False

    def approve(self, approved_by, notes=''):
        """Approve the note."""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def reject(self, rejected_by, notes=''):
        """Reject the note."""
        self.status = 'rejected'
        self.approved_by = rejected_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def request_revision(self, requested_by, notes=''):
        """Request revision of the note."""
        self.status = 'revision_requested'
        self.approved_by = requested_by
        self.approval_notes = notes
        self.save()


class NoteHistory(models.Model):
    """
    Audit trail for all changes to professor notes.
    This ensures complete transparency and accountability.
    """

    note = models.ForeignKey(
        ProfessorNote,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(
        max_length=50,
        choices=(
            ('created', _('Created')),
            ('updated', _('Updated')),
            ('submitted', _('Submitted for Approval')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('revision_requested', _('Revision Requested')),
            ('soft_deleted', _('Soft Deleted')),
        ),
        verbose_name=_('Action')
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    # Store old and new values
    old_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Old Values')
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('New Values')
    )
    change_summary = models.TextField(
        blank=True,
        verbose_name=_('Change Summary')
    )

    class Meta:
        ordering = ['-changed_at']
        verbose_name = _('Note History')
        verbose_name_plural = _('Note Histories')

    def __str__(self):
        return f"{self.note} - {self.get_action_display()} by {self.changed_by}"


class NoteComment(models.Model):
    """
    Comments/feedback on professor notes (for communication during approval).
    """

    note = models.ForeignKey(
        ProfessorNote,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    comment = models.TextField(verbose_name=_('Comment'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Note Comment')
        verbose_name_plural = _('Note Comments')

    def __str__(self):
        return f"Comment on {self.note} by {self.author}"
