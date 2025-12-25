"""
Core models for multi-tenant School Management System.
Includes tenant (School) and domain models for django-tenants.
"""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_tenants.models import TenantMixin, DomainMixin


# ==============================================================================
# TENANT MODELS (django-tenants)
# ==============================================================================

class School(TenantMixin):
    """
    Tenant model representing an individual school.
    Each school gets its own PostgreSQL schema.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='USA')
    postal_code = models.CharField(max_length=20)

    # Branding
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#007bff')  # Hex color

    # License and Subscription
    license_key = models.CharField(max_length=100, unique=True)
    subscription_type = models.CharField(
        max_length=20,
        choices=(
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ),
        default='monthly'
    )
    subscription_start = models.DateField()
    subscription_end = models.DateField()
    is_active = models.BooleanField(default=True)
    max_students = models.IntegerField(default=500)
    max_staff = models.IntegerField(default=50)

    # Audit fields
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    # auto_create_schema and auto_drop_schema are inherited from TenantMixin
    auto_create_schema = True
    auto_drop_schema = False  # Safety: don't auto-delete schemas

    class Meta:
        verbose_name = 'School (Tenant)'
        verbose_name_plural = 'Schools (Tenants)'
        ordering = ['name']

    def __str__(self):
        return self.name

    def is_subscription_valid(self):
        """Check if school subscription is still valid."""
        from django.utils import timezone
        return self.is_active and self.subscription_end >= timezone.now().date()


class Domain(DomainMixin):
    """
    Domain model for routing tenants.
    Each school can have multiple domains/subdomains.
    """
    pass


# ==============================================================================
# SHARED MODELS (available to all tenants)
# ==============================================================================

NEWS = _("News")
EVENTS = _("Event")

POST = (
    (NEWS, _("News")),
    (EVENTS, _("Event")),
)

FIRST = _("First")
SECOND = _("Second")
THIRD = _("Third")

SEMESTER = (
    (FIRST, _("First")),
    (SECOND, _("Second")),
    (THIRD, _("Third")),
)


class NewsAndEventsQuerySet(models.query.QuerySet):
    def search(self, query):
        lookups = (
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(posted_as__icontains=query)
        )
        return self.filter(lookups).distinct()


class NewsAndEventsManager(models.Manager):
    def get_queryset(self):
        return NewsAndEventsQuerySet(self.model, using=self._db)

    def all(self):
        return self.get_queryset()

    def get_by_id(self, id):
        qs = self.get_queryset().filter(
            id=id
        )  # NewsAndEvents.objects == self.get_queryset()
        if qs.count() == 1:
            return qs.first()
        return None

    def search(self, query):
        return self.get_queryset().search(query)


class NewsAndEvents(models.Model):
    title = models.CharField(max_length=200, null=True)
    summary = models.TextField(max_length=200, blank=True, null=True)
    posted_as = models.CharField(choices=POST, max_length=10)
    updated_date = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    upload_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=True)

    objects = NewsAndEventsManager()

    def __str__(self):
        return f"{self.title}"


class Session(models.Model):
    session = models.CharField(max_length=200, unique=True)
    is_current_session = models.BooleanField(default=False, blank=True, null=True)
    next_session_begins = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.session}"


class Semester(models.Model):
    semester = models.CharField(max_length=10, choices=SEMESTER, blank=True)
    is_current_semester = models.BooleanField(default=False, blank=True, null=True)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, blank=True, null=True
    )
    next_semester_begins = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.semester}"


class ActivityLog(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.created_at}]{self.message}"
