import logging

from .base import BaseDetector

logger = logging.getLogger(__name__)


class DuplicateEnrollmentDetector(BaseDetector):
    """Detect duplicate enrollment applications (same email + same program + same year)."""

    anomaly_code = 'enrollment_duplicate'

    def check(self, registration):
        from enrollment.models import RegistrationForm

        duplicates = RegistrationForm.objects.filter(
            email=registration.email,
            filiere=registration.filiere,
            academic_year=registration.academic_year,
            status__in=['pending', 'under_review', 'approved', 'enrolled'],
        ).exclude(pk=registration.pk)

        if duplicates.exists():
            self.create_alert(
                title=f"Duplicate enrollment: {registration.student_name} "
                      f"({registration.email}) for {registration.filiere}",
                details={
                    'registration_id': registration.pk,
                    'student_name': registration.student_name,
                    'email': registration.email,
                    'filiere': str(registration.filiere) if registration.filiere else '',
                    'academic_year': registration.academic_year,
                    'duplicate_ids': list(duplicates.values_list('pk', flat=True)),
                    'duplicate_count': duplicates.count(),
                },
                related_obj=registration,
            )


class InvalidStatusTransitionDetector(BaseDetector):
    """Detect invalid enrollment status transitions."""

    anomaly_code = 'enrollment_invalid_transition'

    VALID_TRANSITIONS = {
        'pending': {'under_review', 'rejected'},
        'under_review': {'approved', 'rejected'},
        'approved': {'enrolled', 'rejected'},
        'rejected': {'pending'},  # Allow resubmission
        'enrolled': set(),  # Terminal state
    }

    def check(self, registration):
        from enrollment.models import EnrollmentStatusHistory

        # Get the most recent status change
        last_history = EnrollmentStatusHistory.objects.filter(
            registration=registration
        ).order_by('-changed_at').first()

        if not last_history:
            return

        old_status = last_history.old_status
        new_status = last_history.new_status

        valid_next = self.VALID_TRANSITIONS.get(old_status, set())
        if new_status not in valid_next:
            self.create_alert(
                title=f"Invalid enrollment transition: {old_status} -> {new_status} "
                      f"for {registration.student_name}",
                details={
                    'registration_id': registration.pk,
                    'student_name': registration.student_name,
                    'old_status': old_status,
                    'new_status': new_status,
                    'changed_by': last_history.changed_by.get_full_name() if last_history.changed_by else 'Unknown',
                    'valid_transitions': list(valid_next),
                },
                related_obj=registration,
            )


class UnauthorizedApprovalDetector(BaseDetector):
    """Detect enrollment approvals by users without proper authority."""

    anomaly_code = 'enrollment_unauthorized_approval'

    AUTHORIZED_ROLES = {'direction', 'admin', 'secretary', 'registrar'}

    def check(self, registration):
        if registration.status not in ('approved', 'enrolled'):
            return

        reviewer = registration.reviewed_by
        if not reviewer:
            return

        if reviewer.is_superuser:
            return

        if reviewer.role not in self.AUTHORIZED_ROLES:
            self.create_alert(
                title=f"Unauthorized enrollment approval by {reviewer.get_full_name()} "
                      f"(role: {reviewer.role}) for {registration.student_name}",
                details={
                    'registration_id': registration.pk,
                    'student_name': registration.student_name,
                    'reviewed_by': reviewer.get_full_name(),
                    'reviewer_role': reviewer.role,
                    'status': registration.status,
                    'authorized_roles': list(self.AUTHORIZED_ROLES),
                },
                severity='critical',
                user=reviewer,
                related_obj=registration,
            )
