from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportExportLog(models.Model):
    """
    Immutable audit trail for every report export.
    Every PDF download, CSV export, or Excel export is recorded here.
    """

    REPORT_TYPE_CHOICES = (
        ('student_complete_record', _('Student Complete Record')),
        ('incident_report', _('Incident Report')),
        ('visitor_log', _('Visitor Log Report')),
        ('attendance_report', _('Attendance Report')),
        ('discipline_history', _('Discipline History')),
        ('attendance_csv', _('Attendance CSV Export')),
        ('attendance_xlsx', _('Attendance Excel Export')),
        ('grades_csv', _('Grades CSV Export')),
        ('grades_xlsx', _('Grades Excel Export')),
    )

    FORMAT_CHOICES = (
        ('pdf', _('PDF')),
        ('csv', _('CSV')),
        ('xlsx', _('Excel')),
    )

    report_type = models.CharField(
        max_length=50, choices=REPORT_TYPE_CHOICES
    )
    export_format = models.CharField(
        max_length=10, choices=FORMAT_CHOICES, default='pdf'
    )
    title = models.CharField(
        max_length=300,
        help_text=_('Human-readable description of what was exported')
    )

    exported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='report_exports'
    )
    exported_at = models.DateTimeField(auto_now_add=True)

    export_reason = models.TextField(
        blank=True,
        help_text=_('Reason for export - required for student complete records')
    )

    student_id = models.IntegerField(
        null=True, blank=True,
        help_text=_('Student PK if report is student-related')
    )
    incident_id = models.IntegerField(
        null=True, blank=True,
        help_text=_('Incident PK if incident report')
    )

    filter_params = models.JSONField(
        default=dict, blank=True,
        help_text=_('Filter parameters applied')
    )

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    tenant = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='report_exports'
    )

    class Meta:
        ordering = ['-exported_at']
        verbose_name = _('Report Export Log')
        verbose_name_plural = _('Report Export Logs')
        indexes = [
            models.Index(
                fields=['exported_by', '-exported_at'],
                name='rpt_user_date_idx',
            ),
            models.Index(
                fields=['report_type', '-exported_at'],
                name='rpt_type_date_idx',
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_report_type_display()} by {self.exported_by} "
            f"at {self.exported_at}"
        )
