"""
Student Timeline Aggregation Service.

Queries 10+ tables and merges results into a unified, chronological timeline.
"""
from django.contrib.contenttypes.models import ContentType


class StudentTimelineService:
    """
    Aggregates a student's complete history from all systems.

    Usage:
        service = StudentTimelineService(student)
        result = service.get_timeline(event_types=['discipline', 'attendance'])
    """

    def __init__(self, student, user=None, tenant=None):
        self.student = student
        self.user = user or student.student
        self.tenant = tenant

    def get_timeline(
        self, event_types=None, date_from=None, date_to=None,
        severity=None, page=1, page_size=50,
    ):
        all_entries = []

        fetchers = {
            'enrollment': self._fetch_enrollment_events,
            'attendance': self._fetch_attendance_events,
            'discipline': self._fetch_discipline_events,
            'grade_change': self._fetch_grade_events,
            'guardian_change': self._fetch_guardian_events,
            'certificate': self._fetch_certificate_events,
            'payment': self._fetch_payment_events,
            'incident': self._fetch_incident_events,
            'visitor': self._fetch_visitor_events,
            'profile_change': self._fetch_profile_change_events,
        }

        active = fetchers
        if event_types:
            active = {k: v for k, v in fetchers.items() if k in event_types}

        for event_type, fetcher in active.items():
            try:
                entries = fetcher(date_from=date_from, date_to=date_to)
                all_entries.extend(entries)
            except Exception:
                pass

        if severity:
            all_entries = [e for e in all_entries if e['severity'] == severity]

        all_entries.sort(key=lambda x: x['timestamp'], reverse=True)

        total = len(all_entries)
        start = (page - 1) * page_size
        end = start + page_size
        page_entries = all_entries[start:end]

        return {
            'results': page_entries,
            'count': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size if total else 0,
        }

    def _fetch_enrollment_events(self, date_from=None, date_to=None):
        from enrollment.models import EnrollmentStatusHistory, RegistrationForm

        entries = []
        registrations = RegistrationForm.objects.filter(
            enrolled_user=self.user
        ).values_list('id', flat=True)

        qs = EnrollmentStatusHistory.objects.filter(
            registration_id__in=registrations
        ).select_related('changed_by')

        if date_from:
            qs = qs.filter(changed_at__gte=date_from)
        if date_to:
            qs = qs.filter(changed_at__lte=date_to)

        for record in qs:
            entries.append({
                'id': f'enrollment_{record.pk}',
                'timestamp': record.changed_at,
                'event_type': 'enrollment',
                'severity': 'info',
                'title': f'Enrollment: {record.old_status} \u2192 {record.new_status}',
                'description': record.notes or '',
                'actor': str(record.changed_by) if record.changed_by else None,
                'metadata': {
                    'old_status': record.old_status,
                    'new_status': record.new_status,
                },
                'source_model': 'EnrollmentStatusHistory',
                'source_id': record.pk,
            })
        return entries

    def _fetch_attendance_events(self, date_from=None, date_to=None):
        from attendance.models import AttendanceReport, Student as AttStudent

        entries = []
        # Bridge to attendance.Student via email
        try:
            att_student = AttStudent.objects.get(email=self.user.email)
        except AttStudent.DoesNotExist:
            return entries

        qs = AttendanceReport.objects.filter(
            student=att_student
        ).select_related('attendance', 'attendance__subject')

        if date_from:
            qs = qs.filter(attendance__date__gte=date_from)
        if date_to:
            qs = qs.filter(attendance__date__lte=date_to)

        # Only include absences and late arrivals (not routine present)
        qs = qs.exclude(status='present')

        for record in qs:
            severity = 'warning' if record.status == 'absent' else 'info'
            reason = ''
            if hasattr(record, 'absence_reason') and record.absence_reason:
                reason = f' ({record.get_absence_reason_display()})'
            entries.append({
                'id': f'attendance_{record.pk}',
                'timestamp': record.created_at,
                'event_type': 'attendance',
                'severity': severity,
                'title': f'{record.status.capitalize()}: {record.attendance.subject.name}{reason}',
                'description': getattr(record, 'absence_notes', '') or '',
                'actor': None,
                'metadata': {
                    'subject': record.attendance.subject.name,
                    'date': str(record.attendance.date),
                    'status': record.status,
                },
                'source_model': 'AttendanceReport',
                'source_id': record.pk,
            })
        return entries

    def _fetch_discipline_events(self, date_from=None, date_to=None):
        from discipline.models import DisciplinaryAction

        entries = []
        qs = DisciplinaryAction.objects.filter(
            student=self.user
        ).select_related('reported_by')

        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        severity_map = {
            'minor': 'info', 'moderate': 'warning',
            'serious': 'critical', 'critical': 'critical',
        }

        for record in qs:
            entries.append({
                'id': f'discipline_{record.pk}',
                'timestamp': record.created_at,
                'event_type': 'discipline',
                'severity': severity_map.get(record.severity, 'info'),
                'title': f'Discipline: {record.incident_type} ({record.get_severity_display()})',
                'description': record.description[:200],
                'actor': str(record.reported_by) if record.reported_by else None,
                'metadata': {
                    'severity': record.severity,
                    'is_resolved': record.is_resolved,
                },
                'source_model': 'DisciplinaryAction',
                'source_id': record.pk,
            })
        return entries

    def _fetch_grade_events(self, date_from=None, date_to=None):
        from result.models import GradeHistory

        entries = []
        qs = GradeHistory.objects.filter(
            taken_course__student=self.student
        ).select_related('changed_by', 'taken_course__course')

        if date_from:
            qs = qs.filter(changed_at__gte=date_from)
        if date_to:
            qs = qs.filter(changed_at__lte=date_to)

        for record in qs:
            course_name = record.taken_course.course.title if record.taken_course else 'Unknown'
            entries.append({
                'id': f'grade_{record.pk}',
                'timestamp': record.changed_at,
                'event_type': 'grade_change',
                'severity': 'info',
                'title': f'Grade changed: {course_name}',
                'description': record.change_reason or '',
                'actor': str(record.changed_by) if record.changed_by else None,
                'metadata': {
                    'course': course_name,
                },
                'source_model': 'GradeHistory',
                'source_id': record.pk,
            })
        return entries

    def _fetch_guardian_events(self, date_from=None, date_to=None):
        from audit.models import FieldChangeRecord
        from accounts.models import Parent

        entries = []
        ct = ContentType.objects.get_for_model(Parent)
        parent_ids = Parent.objects.filter(
            student=self.student
        ).values_list('id', flat=True)

        qs = FieldChangeRecord.objects.filter(
            content_type=ct, object_id__in=parent_ids
        ).select_related('changed_by')

        if date_from:
            qs = qs.filter(changed_at__gte=date_from)
        if date_to:
            qs = qs.filter(changed_at__lte=date_to)

        # Group by batch_id to show one entry per save
        batches = {}
        for record in qs:
            bid = str(record.batch_id)
            if bid not in batches:
                batches[bid] = {
                    'record': record,
                    'fields': [],
                }
            batches[bid]['fields'].append(record.field_name)

        for bid, data in batches.items():
            record = data['record']
            fields = ', '.join(data['fields'])
            entries.append({
                'id': f'guardian_{record.pk}',
                'timestamp': record.changed_at,
                'event_type': 'guardian_change',
                'severity': 'warning',
                'title': f'Guardian info changed: {fields}',
                'description': record.change_reason or '',
                'actor': str(record.changed_by) if record.changed_by else None,
                'metadata': {'fields_changed': data['fields']},
                'source_model': 'FieldChangeRecord',
                'source_id': record.pk,
            })
        return entries

    def _fetch_certificate_events(self, date_from=None, date_to=None):
        from certificates.models import Certificate

        entries = []
        qs = Certificate.objects.filter(
            student=self.student
        ).select_related('course', 'issued_by')

        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        for record in qs:
            entries.append({
                'id': f'certificate_{record.pk}',
                'timestamp': record.created_at,
                'event_type': 'certificate',
                'severity': 'info',
                'title': f'Certificate: {record.title}',
                'description': f'Status: {record.get_status_display()}',
                'actor': str(record.issued_by) if record.issued_by else None,
                'metadata': {'status': record.status},
                'source_model': 'Certificate',
                'source_id': record.pk,
            })
        return entries

    def _fetch_payment_events(self, date_from=None, date_to=None):
        from payments.models import Payment

        entries = []
        qs = Payment.objects.filter(student=self.student)

        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        for record in qs:
            entries.append({
                'id': f'payment_{record.pk}',
                'timestamp': record.created_at,
                'event_type': 'payment',
                'severity': 'info',
                'title': f'Payment: {record.amount}',
                'description': f'Status: {record.get_status_display()}',
                'actor': None,
                'metadata': {
                    'amount': str(record.amount),
                    'status': record.status,
                },
                'source_model': 'Payment',
                'source_id': record.pk,
            })
        return entries

    def _fetch_incident_events(self, date_from=None, date_to=None):
        from safeguarding.models import Incident

        entries = []
        qs = Incident.objects.filter(
            students_involved=self.student
        ).select_related('reported_by')

        if date_from:
            qs = qs.filter(created_at__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        severity_map = {
            'low': 'info', 'medium': 'warning',
            'high': 'critical', 'critical': 'critical',
        }

        for record in qs:
            entries.append({
                'id': f'incident_{record.pk}',
                'timestamp': record.created_at,
                'event_type': 'incident',
                'severity': severity_map.get(record.severity, 'info'),
                'title': f'Incident: {record.title}',
                'description': record.description[:200],
                'actor': str(record.reported_by) if record.reported_by else None,
                'metadata': {
                    'type': record.incident_type,
                    'severity': record.severity,
                    'status': record.status,
                },
                'source_model': 'Incident',
                'source_id': record.pk,
            })
        return entries

    def _fetch_visitor_events(self, date_from=None, date_to=None):
        from safeguarding.models import VisitorLog

        entries = []
        qs = VisitorLog.objects.filter(
            students_involved=self.student
        ).select_related('logged_by', 'host_staff')

        if date_from:
            qs = qs.filter(time_in__gte=date_from)
        if date_to:
            qs = qs.filter(time_in__lte=date_to)

        for record in qs:
            entries.append({
                'id': f'visitor_{record.pk}',
                'timestamp': record.time_in,
                'event_type': 'visitor',
                'severity': 'info',
                'title': f'Visitor: {record.visitor_name} ({record.get_visitor_type_display()})',
                'description': record.purpose[:200],
                'actor': str(record.logged_by) if record.logged_by else None,
                'metadata': {
                    'visitor_type': record.visitor_type,
                    'organization': record.organization,
                },
                'source_model': 'VisitorLog',
                'source_id': record.pk,
            })
        return entries

    def _fetch_profile_change_events(self, date_from=None, date_to=None):
        from audit.models import FieldChangeRecord
        from accounts.models import Student as StudentModel

        entries = []

        # User changes
        user_ct = ContentType.objects.get_for_model(self.user)
        student_ct = ContentType.objects.get_for_model(StudentModel)

        qs = FieldChangeRecord.objects.filter(
            content_type__in=[user_ct, student_ct],
            object_id__in=[self.user.pk, self.student.pk],
            action='update',
        ).select_related('changed_by')

        if date_from:
            qs = qs.filter(changed_at__gte=date_from)
        if date_to:
            qs = qs.filter(changed_at__lte=date_to)

        # Group by batch
        batches = {}
        for record in qs:
            bid = str(record.batch_id)
            if bid not in batches:
                batches[bid] = {'record': record, 'fields': []}
            batches[bid]['fields'].append(record.field_name)

        for bid, data in batches.items():
            record = data['record']
            fields = ', '.join(data['fields'])
            entries.append({
                'id': f'profile_{record.pk}',
                'timestamp': record.changed_at,
                'event_type': 'profile_change',
                'severity': 'info',
                'title': f'Profile updated: {fields}',
                'description': record.change_reason or '',
                'actor': str(record.changed_by) if record.changed_by else None,
                'metadata': {'fields_changed': data['fields']},
                'source_model': 'FieldChangeRecord',
                'source_id': record.pk,
            })
        return entries
