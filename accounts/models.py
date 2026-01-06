from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.utils import timezone
from PIL import Image
from django_countries.fields import CountryField

from course.models import Program
from .validators import ASCIIUsernameValidator


# LEVEL_COURSE = "Level course"
BACHELOR_DEGREE = _("Bachelor")
MASTER_DEGREE = _("Master")

LEVEL = (
    # (LEVEL_COURSE, "Level course"),
    (BACHELOR_DEGREE, _("Bachelor Degree")),
    (MASTER_DEGREE, _("Master Degree")),
)

FATHER = _("Father")
MOTHER = _("Mother")
BROTHER = _("Brother")
SISTER = _("Sister")
GRAND_MOTHER = _("Grand mother")
GRAND_FATHER = _("Grand father")
OTHER = _("Other")

RELATION_SHIP = (
    (FATHER, _("Father")),
    (MOTHER, _("Mother")),
    (BROTHER, _("Brother")),
    (SISTER, _("Sister")),
    (GRAND_MOTHER, _("Grand mother")),
    (GRAND_FATHER, _("Grand father")),
    (OTHER, _("Other")),
)

# Role choices for multi-tenant RBAC
ROLE_CHOICES = (
    ('parent', _('Parent')),
    ('student', _('Student')),
    ('professor', _('Professor')),
    ('direction', _('Direction')),
    ('admin', _('Administrator')),
)

# User approval workflow status
APPROVAL_STATUS_CHOICES = (
    ('not_requested', _('Not Requested')),
    ('pending', _('Pending Approval')),
    ('approved', _('Approved')),
    ('declined', _('Declined')),
)


class CustomUserManager(UserManager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query is not None:
            or_lookup = (
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
            )
            queryset = queryset.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return queryset

    def get_student_count(self):
        return self.model.objects.filter(is_student=True).count()

    def get_lecturer_count(self):
        return self.model.objects.filter(is_lecturer=True).count()

    def get_superuser_count(self):
        return self.model.objects.filter(is_superuser=True).count()


GENDERS = ((_("M"), _("Male")), (_("F"), _("Female")))


class User(AbstractUser):
    # Legacy boolean fields (kept for backward compatibility)
    is_student = models.BooleanField(default=False)
    is_lecturer = models.BooleanField(default=False)
    is_parent = models.BooleanField(default=False)
    is_dep_head = models.BooleanField(default=False)

    # NEW: Multi-tenant RBAC fields
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        help_text=_('User role within the tenant')
    )
    tenant = models.ForeignKey(
        'core.School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text=_('School/tenant this user belongs to')
    )

    # Profile fields
    gender = models.CharField(max_length=1, choices=GENDERS, blank=True, null=True)
    phone = models.CharField(max_length=60, blank=True, null=True)
    address = models.CharField(max_length=60, blank=True, null=True)
    picture = models.ImageField(
        upload_to="profile_pictures/%y/%m/%d/", default="default.png", null=True
    )
    email = models.EmailField(blank=True, null=True)

    # Additional contact info
    emergency_contact = models.CharField(max_length=60, blank=True, null=True)
    emergency_phone = models.CharField(max_length=60, blank=True, null=True)

    # NEW: Account approval workflow fields
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='not_requested',
        help_text=_('Account approval status')
    )
    requested_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        blank=True,
        help_text=_('Role requested during registration')
    )
    approval_extra_note = models.TextField(
        blank=True,
        help_text=_('Additional notes for approval/rejection')
    )

    # NEW: Additional profile fields
    employee_or_student_id = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Unique employee or student ID')
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text=_('Date of birth for age verification')
    )
    country = CountryField(
        blank=True,
        null=True,
        help_text=_('Country of residence')
    )

    username_validator = ASCIIUsernameValidator()

    objects = CustomUserManager()

    class Meta:
        ordering = ("-date_joined",)

    @property
    def get_full_name(self):
        full_name = self.username
        if self.first_name and self.last_name:
            full_name = self.first_name + " " + self.last_name
        return full_name

    def __str__(self):
        return "{} ({})".format(self.username, self.get_full_name)

    @property
    def get_user_role(self):
        if self.is_superuser:
            role = _("Admin")
        elif self.is_student:
            role = _("Student")
        elif self.is_lecturer:
            role = _("Lecturer")
        elif self.is_parent:
            role = _("Parent")

        return role

    def get_picture(self):
        try:
            return self.picture.url
        except:
            no_picture = settings.MEDIA_URL + "default.png"
            return no_picture

    def get_absolute_url(self):
        return reverse("profile_single", kwargs={"user_id": self.id})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            img = Image.open(self.picture.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.picture.path)
        except:
            pass

    def delete(self, *args, **kwargs):
        if self.picture.url != settings.MEDIA_URL + "default.png":
            self.picture.delete()
        super().delete(*args, **kwargs)


class StudentManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query is not None:
            or_lookup = Q(level__icontains=query) | Q(program__icontains=query)
            qs = qs.filter(
                or_lookup
            ).distinct()  # distinct() is often necessary with Q lookups
        return qs


class ActiveStudentManager(models.Manager):
    """Manager for active students (not alumni or dropped)."""
    def get_queryset(self):
        return super().get_queryset().filter(
            is_alumni=False,
            is_dropped=False
        )


class AlumniManager(models.Manager):
    """Manager for alumni students."""
    def get_queryset(self):
        return super().get_queryset().filter(is_alumni=True)


class DroppedStudentManager(models.Manager):
    """Manager for dropped students."""
    def get_queryset(self):
        return super().get_queryset().filter(is_dropped=True)


class Student(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    # id_number = models.CharField(max_length=20, unique=True, blank=True)
    level = models.CharField(max_length=25, choices=LEVEL, null=True)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, null=True)

    # NEW: Student lifecycle tracking fields
    is_alumni = models.BooleanField(
        default=False,
        help_text=_('Mark as True when student graduates')
    )
    is_dropped = models.BooleanField(
        default=False,
        help_text=_('Mark as True when student drops out')
    )
    drop_reason = models.TextField(
        blank=True,
        help_text=_('Reason for dropping out')
    )
    graduation_date = models.DateField(
        blank=True,
        null=True,
        help_text=_('Date of graduation')
    )

    # NEW: Auto-generated student registration number (format: YY-BATCH-DEPT-SERIAL)
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text=_('Auto-generated student ID (e.g., 24-CS-001)')
    )

    # Multiple managers
    objects = StudentManager()
    active = ActiveStudentManager()
    alumni_objects = AlumniManager()
    dropped = DroppedStudentManager()

    class Meta:
        ordering = ("-student__date_joined",)

    def __str__(self):
        return self.student.get_full_name

    @classmethod
    def get_gender_count(cls):
        males_count = Student.objects.filter(student__gender="M").count()
        females_count = Student.objects.filter(student__gender="F").count()

        return {"M": males_count, "F": females_count}

    def get_absolute_url(self):
        return reverse("profile_single", kwargs={"user_id": self.id})

    def save(self, *args, **kwargs):
        """Auto-generate registration_number if not set."""
        if not self.registration_number and self.program:
            # Format: YY-DEPT-SERIAL (e.g., 24-CS-001)
            year = timezone.now().year % 100  # Last 2 digits of year
            dept_code = self.program.title[:3].upper() if self.program.title else 'GEN'

            # Get the last student registration number for this department and year
            last_student = Student.objects.filter(
                registration_number__startswith=f"{year:02d}-{dept_code}"
            ).order_by('registration_number').last()

            if last_student and last_student.registration_number:
                # Extract serial number and increment
                try:
                    serial = int(last_student.registration_number.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    serial = 1
            else:
                serial = 1

            self.registration_number = f"{year:02d}-{dept_code}-{serial:03d}"

        super().save(*args, **kwargs)

    def mark_as_alumni(self, graduation_date=None):
        """Mark student as alumni."""
        self.is_alumni = True
        self.graduation_date = graduation_date or timezone.now().date()
        self.save(update_fields=['is_alumni', 'graduation_date'])

    def mark_as_dropped(self, reason=''):
        """Mark student as dropped."""
        self.is_dropped = True
        self.drop_reason = reason
        self.save(update_fields=['is_dropped', 'drop_reason'])

    def delete(self, *args, **kwargs):
        self.student.delete()
        super().delete(*args, **kwargs)


class Parent(models.Model):
    """
    Connect student with their parent, parents can
    only view their connected students information
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student, null=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # What is the relationship between the student and
    # the parent (i.e. father, mother, brother, sister)
    relation_ship = models.TextField(choices=RELATION_SHIP, blank=True)

    class Meta:
        ordering = ("-user__date_joined",)

    def __str__(self):
        return self.user.username


class DepartmentHead(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Program, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ("-user__date_joined",)

    def __str__(self):
        return "{}".format(self.user)
