from django.conf import settings
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
import csv
import json

User = get_user_model()


ABSENCE_REASON_CHOICES = (
    ('unexcused', _('Unexcused')),
    ('medical', _('Medical')),
    ('family_emergency', _('Family Emergency')),
    ('court_date', _('Court Date')),
    ('suspension', _('Suspension')),
    ('school_event', _('School Event')),
    ('other', _('Other')),
)

class Group(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        ordering = ['name']

class Student(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')

    def fetch_attendance(self):
        return Attendance.objects.filter(student=self)
    
    def load_students_from_csv(self, file):
        with open('student.csv', 'r') as f:
            reader = csv.reader(f).decode('utf-8')
            for row in reader:
                group = Group.objects.get_or_create(name=row[3])
                Student.objects.create(first_name=row[0], last_name=row[1], email=row[2], group=group)

    def load_students_from_json(self):
        with open('ajou.json', 'r') as f:
            for i in json.load(f):
                group = Group.objects.get(name=i['group'])
                Student.objects.create(first_name=i['full_name'].split()[1], last_name=i['full_name'].split()[0], email=(str(i['full_id'])+"@ajou.uz"), group=group)

    @property
    def get_attendances(self):
        return self.attendance_reports.all()
    
    @property
    def get_absents_and_lates(self):
        return self.attendance_reports.filter(models.Q(status='absent') | models.Q(status='late'))
    
    @property
    def get_subjects(self):
        return self.group.subjects.all()

    def get_attendance_percentage(self, subject=None):
        """Calculate attendance percentage for a student."""
        reports = self.attendance_reports.all()

        if subject:
            reports = reports.filter(attendance__subject=subject)

        total = reports.count()
        if total == 0:
            return 0

        attended = reports.filter(
            Q(status=Status.PRESENT) | Q(status=Status.LATE)
        ).count()

        return round((attended / total) * 100, 2)

    def has_low_attendance(self, threshold=75, subject=None):
        """Check if student attendance is below threshold."""
        return self.get_attendance_percentage(subject=subject) < threshold

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
        ordering = ['last_name', 'first_name']

    def __str__(self) -> str:
        return self.first_name + ' ' + self.last_name + ' - ' + self.group.name
    

class Subject(models.Model):
    name = models.CharField(max_length=50)
    teacher = models.ForeignKey(User, related_name='subjects', on_delete=models.CASCADE)                
    group = models.ManyToManyField(Group, related_name='subjects')
    slug = models.SlugField(max_length=50)

    def __str__(self) -> str:
        return self.name


class Status(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'


class Attendance(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.subject.name + ' - ' + self.date.strftime('%d-%m-%Y')

    class Meta:
        ordering = ['-date']
    

class AttendanceReport(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='reports')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_reports')
    status = models.CharField(choices=Status.choices, max_length=10, default=Status.ABSENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Absence reason tracking
    absence_reason = models.CharField(
        max_length=30, choices=ABSENCE_REASON_CHOICES,
        blank=True, help_text=_('Reason for absence (when status is absent)')
    )
    absence_notes = models.TextField(
        blank=True, help_text=_('Additional details about the absence')
    )
    excused = models.BooleanField(
        default=False,
        help_text=_('Whether the absence has been excused by administration')
    )
    excused_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='excused_absences'
    )
    excused_at = models.DateTimeField(null=True, blank=True)
    supporting_document = models.FileField(
        upload_to='absence_docs/%Y/%m/%d/',
        blank=True, help_text=_('Medical certificate or supporting document')
    )

    class Meta:
        ordering = ['student__last_name', 'student__first_name']
        unique_together = [['attendance', 'student']]  # Prevent duplicate entries
        indexes = [
            models.Index(fields=['attendance', 'status']),
            models.Index(fields=['student', '-created_at']),
        ]

    def __str__(self) -> str:
        return self.student.first_name + ' ' + self.student.last_name + ' - ' + self.status + ' - ' + self.attendance.subject.name + ' - ' + self.attendance.date.strftime('%d-%m-%Y')


class DailyAttendanceStat(models.Model):
    """Pre-aggregated daily attendance statistics for faster reporting."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='daily_stats')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()

    # Statistics
    total_students = models.PositiveIntegerField(default=0)
    present_count = models.PositiveIntegerField(default=0)
    absent_count = models.PositiveIntegerField(default=0)
    late_count = models.PositiveIntegerField(default=0)

    # Calculated fields
    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_('Percentage of students present (including late)')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Daily Attendance Statistic')
        verbose_name_plural = _('Daily Attendance Statistics')
        ordering = ['-date', 'subject']
        unique_together = [['subject', 'group', 'date']]
        indexes = [
            models.Index(fields=['-date', 'subject']),
            models.Index(fields=['group', '-date']),
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.group.name} - {self.date.strftime('%d-%m-%Y')} ({self.attendance_percentage}%)"

    def calculate_stats(self):
        """Calculate and update statistics from AttendanceReport."""
        attendance = Attendance.objects.filter(
            subject=self.subject,
            date=self.date
        ).first()

        if not attendance:
            return

        # Get status counts
        reports = attendance.reports.filter(student__group=self.group)
        stats = reports.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status=Status.PRESENT)),
            absent=Count('id', filter=Q(status=Status.ABSENT)),
            late=Count('id', filter=Q(status=Status.LATE))
        )

        self.total_students = stats['total'] or 0
        self.present_count = stats['present'] or 0
        self.absent_count = stats['absent'] or 0
        self.late_count = stats['late'] or 0

        # Calculate percentage (present + late)
        if self.total_students > 0:
            self.attendance_percentage = round(
                ((self.present_count + self.late_count) / self.total_students) * 100,
                2
            )
        else:
            self.attendance_percentage = 0

        self.save()

    @classmethod
    def generate_for_date(cls, date=None):
        """Generate stats for all subjects and groups for a given date."""
        if date is None:
            date = timezone.now().date()

        attendances = Attendance.objects.filter(date=date)
        for attendance in attendances:
            groups = attendance.subject.group.all()
            for group in groups:
                stat, created = cls.objects.get_or_create(
                    subject=attendance.subject,
                    group=group,
                    date=date
                )
                stat.calculate_stats()


class AbsenceNotification(models.Model):
    """Track parent notifications about student absences."""

    NOTIFICATION_METHOD_CHOICES = (
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('in_app', _('In-App Notification')),
    )

    attendance_report = models.ForeignKey(
        AttendanceReport, on_delete=models.CASCADE,
        related_name='notifications'
    )
    parent = models.ForeignKey(
        'accounts.Parent', on_delete=models.CASCADE,
        related_name='absence_notifications'
    )
    method = models.CharField(
        max_length=10, choices=NOTIFICATION_METHOD_CHOICES
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    parent_acknowledged = models.BooleanField(default=False)
    parent_response = models.TextField(blank=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = _('Absence Notification')
        verbose_name_plural = _('Absence Notifications')

    def __str__(self):
        return f"Notification to {self.parent} for {self.attendance_report}"