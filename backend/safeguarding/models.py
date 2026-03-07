from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Incident(models.Model):
    """
    General incident log for ANY type of school incident.
    Goes beyond discipline to cover security, medical, legal, and other events.
    """

    INCIDENT_TYPE_CHOICES = (
        ('security', _('Security')),
        ('medical', _('Medical Emergency')),
        ('accident', _('Accident/Injury')),
        ('theft', _('Theft')),
        ('vandalism', _('Vandalism')),
        ('confrontation', _('Confrontation')),
        ('police', _('Police Visit')),
        ('complaint', _('External Complaint')),
        ('safeguarding', _('Safeguarding Concern')),
        ('behavioral', _('Behavioral')),
        ('other', _('Other')),
    )

    SEVERITY_CHOICES = (
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    )

    STATUS_CHOICES = (
        ('open', _('Open')),
        ('investigating', _('Under Investigation')),
        ('action_taken', _('Action Taken')),
        ('closed', _('Closed')),
    )

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE,
        related_name='incidents'
    )

    # Core fields
    incident_type = models.CharField(
        max_length=30, choices=INCIDENT_TYPE_CHOICES,
        verbose_name=_('Incident Type')
    )
    title = models.CharField(
        max_length=200, verbose_name=_('Title'),
        help_text=_('Brief summary of the incident')
    )
    description = models.TextField(verbose_name=_('Description'))
    severity = models.CharField(
        max_length=20, choices=SEVERITY_CHOICES,
        verbose_name=_('Severity')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open',
        verbose_name=_('Status')
    )

    # When and where
    incident_date = models.DateField(verbose_name=_('Incident Date'))
    incident_time = models.TimeField(
        null=True, blank=True, verbose_name=_('Incident Time')
    )
    location = models.CharField(
        max_length=200, blank=True, verbose_name=_('Location'),
        help_text=_('Where the incident occurred (e.g., Room 204, Playground)')
    )

    # People involved
    students_involved = models.ManyToManyField(
        'accounts.Student', blank=True,
        related_name='incidents_involved',
        verbose_name=_('Students Involved')
    )
    staff_involved = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        related_name='incidents_involved_as_staff',
        verbose_name=_('Staff Involved')
    )
    external_parties = models.TextField(
        blank=True, verbose_name=_('External Parties'),
        help_text=_('Names and details of external people involved')
    )
    witnesses = models.TextField(
        blank=True, verbose_name=_('Witnesses'),
        help_text=_('Names and details of witnesses')
    )

    # Response
    actions_taken = models.TextField(
        blank=True, verbose_name=_('Actions Taken')
    )
    follow_up_needed = models.BooleanField(
        default=False, verbose_name=_('Follow-up Needed')
    )
    follow_up_date = models.DateField(
        null=True, blank=True, verbose_name=_('Follow-up Date')
    )
    follow_up_notes = models.TextField(
        blank=True, verbose_name=_('Follow-up Notes')
    )
    resolution = models.TextField(
        blank=True, verbose_name=_('Resolution')
    )

    # Link to existing discipline system
    disciplinary_action = models.ForeignKey(
        'discipline.DisciplinaryAction',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='linked_incidents',
        verbose_name=_('Related Disciplinary Action')
    )

    # Audit trail
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='incidents_reported',
        verbose_name=_('Reported By')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='incidents_updated',
        verbose_name=_('Last Updated By')
    )

    class Meta:
        ordering = ['-incident_date', '-created_at']
        verbose_name = _('Incident')
        verbose_name_plural = _('Incidents')
        indexes = [
            models.Index(
                fields=['tenant', 'status', '-incident_date'],
                name='sg_incident_status_idx',
            ),
            models.Index(
                fields=['tenant', 'incident_type'],
                name='sg_incident_type_idx',
            ),
            models.Index(
                fields=['tenant', 'severity'],
                name='sg_incident_severity_idx',
            ),
        ]
        permissions = [
            ('view_all_incidents', 'Can view all incidents'),
            ('close_incident', 'Can close incidents'),
        ]

    def __str__(self):
        return (
            f"{self.title} ({self.get_incident_type_display()}) "
            f"- {self.incident_date}"
        )


class IncidentAttachment(models.Model):
    """File attachments for incidents (photos, police reports, letters, etc.)."""

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='safeguarding/incidents/%Y/%m/%d/',
        validators=[FileExtensionValidator(
            allowed_extensions=[
                'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif',
            ]
        )]
    )
    description = models.CharField(
        max_length=255, blank=True,
        verbose_name=_('Description'),
        help_text=_('Brief description of the attachment')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _('Incident Attachment')
        verbose_name_plural = _('Incident Attachments')

    def __str__(self):
        return f"Attachment for {self.incident.title}: {self.description or self.file.name}"


class VisitorLog(models.Model):
    """Track all visitors entering the school premises."""

    VISITOR_TYPE_CHOICES = (
        ('parent', _('Parent/Guardian')),
        ('police', _('Police Officer')),
        ('social_worker', _('Social Worker')),
        ('inspector', _('School Inspector')),
        ('contractor', _('Contractor/Vendor')),
        ('government', _('Government Official')),
        ('media', _('Media')),
        ('other', _('Other')),
    )

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE,
        related_name='visitor_logs'
    )

    # Visitor information
    visitor_name = models.CharField(
        max_length=200, verbose_name=_('Visitor Name')
    )
    visitor_type = models.CharField(
        max_length=30, choices=VISITOR_TYPE_CHOICES,
        verbose_name=_('Visitor Type')
    )
    organization = models.CharField(
        max_length=200, blank=True,
        verbose_name=_('Organization'),
        help_text=_('Police department, social services agency, etc.')
    )
    badge_number = models.CharField(
        max_length=50, blank=True,
        verbose_name=_('Badge/ID Number'),
        help_text=_('Official badge or ID number for officials')
    )
    id_verified = models.BooleanField(
        default=False, verbose_name=_('ID Verified'),
        help_text=_('Was official identification checked?')
    )
    phone = models.CharField(
        max_length=30, blank=True,
        verbose_name=_('Contact Phone')
    )

    # Visit details
    purpose = models.TextField(verbose_name=_('Purpose of Visit'))
    time_in = models.DateTimeField(verbose_name=_('Time In'))
    time_out = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Time Out')
    )

    # Who they met
    host_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='hosted_visitors',
        verbose_name=_('Staff Member Met'),
        help_text=_('Primary staff member the visitor met with')
    )
    students_involved = models.ManyToManyField(
        'accounts.Student', blank=True,
        related_name='visitor_logs',
        verbose_name=_('Students Involved')
    )

    # Outcome
    notes = models.TextField(
        blank=True, verbose_name=_('Notes/Outcome')
    )

    # Related incident
    related_incident = models.ForeignKey(
        Incident, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitor_logs',
        verbose_name=_('Related Incident')
    )

    # Approval and audit
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_visitors',
        verbose_name=_('Approved By')
    )
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='visitor_logs_created',
        verbose_name=_('Logged By')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-time_in']
        verbose_name = _('Visitor Log')
        verbose_name_plural = _('Visitor Logs')
        indexes = [
            models.Index(
                fields=['tenant', '-time_in'],
                name='sg_visitor_time_idx',
            ),
            models.Index(
                fields=['tenant', 'visitor_type'],
                name='sg_visitor_type_idx',
            ),
        ]

    def __str__(self):
        return (
            f"{self.visitor_name} ({self.get_visitor_type_display()}) "
            f"- {self.time_in:%Y-%m-%d %H:%M}"
        )

    @property
    def is_currently_on_site(self):
        return self.time_out is None

    @property
    def visit_duration(self):
        if self.time_out:
            return self.time_out - self.time_in
        return None


class StudentCaseNote(models.Model):
    """
    Free-form case notes for admin/counselors about students.
    Supports confidentiality levels to restrict who can view.
    """

    CATEGORY_CHOICES = (
        ('academic', _('Academic')),
        ('behavioral', _('Behavioral')),
        ('family', _('Family')),
        ('medical', _('Medical')),
        ('legal', _('Legal')),
        ('counseling', _('Counseling')),
        ('general', _('General')),
    )

    CONFIDENTIALITY_CHOICES = (
        ('standard', _('Standard')),
        ('restricted', _('Restricted')),
        ('highly_restricted', _('Highly Restricted')),
    )

    tenant = models.ForeignKey(
        'core.School', on_delete=models.CASCADE,
        related_name='case_notes'
    )

    student = models.ForeignKey(
        'accounts.Student', on_delete=models.CASCADE,
        related_name='case_notes',
        verbose_name=_('Student')
    )
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES,
        verbose_name=_('Category')
    )
    confidentiality = models.CharField(
        max_length=20, choices=CONFIDENTIALITY_CHOICES,
        default='standard', verbose_name=_('Confidentiality Level')
    )
    title = models.CharField(
        max_length=200, verbose_name=_('Title')
    )
    content = models.TextField(verbose_name=_('Note Content'))

    # Follow-up
    follow_up_date = models.DateField(
        null=True, blank=True, verbose_name=_('Follow-up Date')
    )
    follow_up_completed = models.BooleanField(
        default=False, verbose_name=_('Follow-up Completed')
    )

    # Related incident
    related_incident = models.ForeignKey(
        Incident, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='case_notes',
        verbose_name=_('Related Incident')
    )

    # Audit trail
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='case_notes_created',
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Student Case Note')
        verbose_name_plural = _('Student Case Notes')
        indexes = [
            models.Index(
                fields=['tenant', 'student', '-created_at'],
                name='sg_casenote_student_idx',
            ),
            models.Index(
                fields=['tenant', 'category'],
                name='sg_casenote_category_idx',
            ),
            models.Index(
                fields=['follow_up_date'],
                name='sg_casenote_followup_idx',
            ),
        ]
        permissions = [
            ('view_restricted_notes', 'Can view restricted case notes'),
            ('view_highly_restricted_notes',
             'Can view highly restricted case notes'),
        ]

    def __str__(self):
        return f"{self.student} - {self.title} ({self.get_category_display()})"
