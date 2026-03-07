"""
Alumni app models.
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Alumni(models.Model):
    """Alumni record."""
    student = models.OneToOneField(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='alumni_record'
    )
    graduation_year = models.IntegerField()
    graduation_date = models.DateField(null=True, blank=True)

    # Career Information
    current_occupation = models.CharField(max_length=200, blank=True)
    current_employer = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=200, blank=True)

    # Contact Information
    personal_email = models.EmailField(blank=True, help_text="Personal email (not school email)")
    phone = models.CharField(max_length=20, blank=True)
    linkedin_url = models.URLField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Engagement
    is_active = models.BooleanField(default=True, help_text="Active in alumni network")
    willing_to_mentor = models.BooleanField(default=False)
    newsletter_subscribed = models.BooleanField(default=True)

    # Metadata
    notes = models.TextField(blank=True, help_text="Internal notes about alumni")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Alumni'
        ordering = ['-graduation_year', 'student__student__last_name']
        indexes = [
            models.Index(fields=['graduation_year']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.student.student.get_full_name} - Class of {self.graduation_year}"


class AlumniEvent(models.Model):
    """Alumni events."""
    EVENT_TYPE_CHOICES = (
        ('reunion', 'Reunion'),
        ('networking', 'Networking'),
        ('workshop', 'Workshop'),
        ('social', 'Social Gathering'),
        ('fundraiser', 'Fundraiser'),
        ('career_fair', 'Career Fair'),
        ('other', 'Other'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='other')
    event_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200)
    venue_details = models.TextField(blank=True)

    # Registration
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Attendees
    attendees = models.ManyToManyField(Alumni, related_name='events_attended', blank=True)
    organizer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organized_alumni_events'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-event_date']
        indexes = [
            models.Index(fields=['-event_date']),
            models.Index(fields=['event_type', '-event_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.event_date.date()}"

    def get_attendee_count(self):
        return self.attendees.count()

    def is_full(self):
        if self.max_attendees:
            return self.get_attendee_count() >= self.max_attendees
        return False


class AlumniDonation(models.Model):
    """Alumni donations."""
    DONATION_PURPOSE_CHOICES = (
        ('general', 'General Fund'),
        ('scholarship', 'Scholarship Fund'),
        ('infrastructure', 'Infrastructure'),
        ('research', 'Research'),
        ('sports', 'Sports'),
        ('library', 'Library'),
        ('other', 'Other'),
    )

    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='donations')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    purpose = models.CharField(max_length=20, choices=DONATION_PURPOSE_CHOICES, default='general')
    purpose_details = models.TextField(blank=True)

    # Payment Information
    transaction_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=50,
        choices=(
            ('stripe', 'Stripe'),
            ('braintree', 'Braintree'),
            ('bank_transfer', 'Bank Transfer'),
            ('check', 'Check'),
            ('cash', 'Cash'),
        )
    )

    # Recognition
    is_anonymous = models.BooleanField(default=False)
    tax_receipt_sent = models.BooleanField(default=False)
    tax_receipt_number = models.CharField(max_length=100, blank=True)

    # Acknowledgment
    thank_you_sent = models.BooleanField(default=False)
    thank_you_sent_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    donated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donated_at']
        indexes = [
            models.Index(fields=['-donated_at']),
            models.Index(fields=['purpose', '-donated_at']),
        ]

    def __str__(self):
        return f"{self.alumni} - {self.currency} {self.amount} ({self.get_purpose_display()})"


class AlumniAchievement(models.Model):
    """Track notable alumni achievements."""
    ACHIEVEMENT_TYPE_CHOICES = (
        ('award', 'Award/Recognition'),
        ('publication', 'Publication'),
        ('promotion', 'Career Promotion'),
        ('entrepreneurship', 'Started Business'),
        ('community_service', 'Community Service'),
        ('other', 'Other'),
    )

    alumni = models.ForeignKey(Alumni, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=30, choices=ACHIEVEMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    achievement_date = models.DateField()

    # Media
    image = models.ImageField(upload_to='alumni/achievements/%Y/%m/', blank=True)
    url = models.URLField(blank=True, help_text="Link to news article or announcement")

    # Visibility
    is_featured = models.BooleanField(default=False, help_text="Feature on alumni page")
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-achievement_date']
        indexes = [
            models.Index(fields=['-achievement_date']),
            models.Index(fields=['is_featured', '-achievement_date']),
        ]

    def __str__(self):
        return f"{self.alumni} - {self.title}"
