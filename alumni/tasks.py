"""
Celery tasks for alumni app.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_alumni_newsletter():
    """Send newsletter to subscribed alumni."""
    from .models import Alumni

    subscribers = Alumni.objects.filter(
        newsletter_subscribed=True,
        is_active=True
    ).exclude(personal_email='').select_related('student__student')

    if not subscribers.exists():
        logger.info("No newsletter subscribers found")
        return "No subscribers"

    # In a real implementation, you'd fetch newsletter content from somewhere
    # For now, this is a placeholder
    sent_count = 0
    for alumni in subscribers:
        if alumni.personal_email:
            try:
                send_mail(
                    subject="Alumni Newsletter - Latest Updates",
                    message=f"""Dear {alumni.student.student.get_full_name},

Here are the latest updates from our alumni network:

- Recent Events
- Career Opportunities
- Success Stories

Stay connected!

Best regards,
Alumni Relations Office""",
                    from_email="alumni@school.com",
                    recipient_list=[alumni.personal_email],
                    fail_silently=True
                )
                sent_count += 1
            except Exception as exc:
                logger.error(f"Error sending newsletter to {alumni.personal_email}: {exc}")

    logger.info(f"Sent newsletter to {sent_count} alumni")
    return f"Sent to {sent_count} alumni"


@shared_task
def send_event_reminders(event_id):
    """Send reminders to registered attendees before an event."""
    from .models import AlumniEvent

    try:
        event = AlumniEvent.objects.get(id=event_id)

        if not event.is_active:
            return "Event is not active"

        attendees = event.attendees.filter(
            is_active=True
        ).exclude(personal_email='').select_related('student__student')

        sent_count = 0
        for alumni in attendees:
            if alumni.personal_email:
                send_mail(
                    subject=f"Event Reminder: {event.title}",
                    message=f"""Dear {alumni.student.student.get_full_name},

This is a reminder about the upcoming alumni event:

Event: {event.title}
Date: {event.event_date.strftime('%B %d, %Y at %I:%M %p')}
Location: {event.location}
{event.venue_details if event.venue_details else ''}

Description:
{event.description}

We look forward to seeing you there!

Best regards,
Alumni Relations Office""",
                    from_email="alumni@school.com",
                    recipient_list=[alumni.personal_email],
                    fail_silently=True
                )
                sent_count += 1

        logger.info(f"Sent event reminders to {sent_count} attendees for event {event.id}")
        return f"Sent to {sent_count} attendees"

    except Exception as exc:
        logger.error(f"Error sending event reminders: {exc}")
        raise


@shared_task
def send_donation_thank_you(donation_id):
    """Send thank you email for donation."""
    from .models import AlumniDonation

    try:
        donation = AlumniDonation.objects.get(id=donation_id)

        if donation.thank_you_sent or not donation.alumni.personal_email:
            return "Thank you already sent or no email"

        recipient_name = donation.alumni.student.student.get_full_name

        # Don't include name in email if anonymous donation
        if donation.is_anonymous:
            salutation = "Dear Alumnus/Alumna"
        else:
            salutation = f"Dear {recipient_name}"

        send_mail(
            subject="Thank You for Your Generous Donation",
            message=f"""{salutation},

Thank you for your generous donation of {donation.currency} {donation.amount} to support {donation.get_purpose_display()}.

Your contribution makes a significant difference in our mission to provide quality education and opportunities for our students.

Transaction ID: {donation.transaction_id}
Donation Date: {donation.donated_at.strftime('%B %d, %Y')}
Purpose: {donation.get_purpose_display()}
{f'Note: {donation.purpose_details}' if donation.purpose_details else ''}

{f'Tax Receipt Number: {donation.tax_receipt_number}' if donation.tax_receipt_number else 'A tax receipt will be sent separately.'}

With sincere gratitude,
Alumni Relations Office""",
            from_email="alumni@school.com",
            recipient_list=[donation.alumni.personal_email],
            fail_silently=True
        )

        # Mark as sent
        donation.thank_you_sent = True
        donation.thank_you_sent_at = timezone.now()
        donation.save()

        logger.info(f"Sent donation thank you for donation {donation.id}")
        return f"Thank you sent for donation {donation.id}"

    except Exception as exc:
        logger.error(f"Error sending donation thank you: {exc}")
        raise


@shared_task
def send_upcoming_event_notifications():
    """Notify alumni about upcoming events (7 days before)."""
    from .models import AlumniEvent, Alumni

    now = timezone.now()
    week_from_now = now + timedelta(days=7)

    upcoming_events = AlumniEvent.objects.filter(
        is_active=True,
        event_date__gte=now,
        event_date__lte=week_from_now
    ).prefetch_related('attendees')

    if not upcoming_events.exists():
        logger.info("No upcoming events in the next 7 days")
        return "No upcoming events"

    # Get all active alumni who haven't registered yet
    active_alumni = Alumni.objects.filter(
        is_active=True,
        newsletter_subscribed=True
    ).exclude(personal_email='').select_related('student__student')

    notification_count = 0
    for event in upcoming_events:
        # Get alumni who haven't registered for this event
        registered_ids = event.attendees.values_list('id', flat=True)
        unregistered = active_alumni.exclude(id__in=registered_ids)

        for alumni in unregistered[:100]:  # Limit to 100 per event to avoid spam
            if alumni.personal_email:
                try:
                    send_mail(
                        subject=f"Upcoming Alumni Event: {event.title}",
                        message=f"""Dear {alumni.student.student.get_full_name},

We'd like to invite you to an upcoming alumni event:

Event: {event.title}
Type: {event.get_event_type_display()}
Date: {event.event_date.strftime('%B %d, %Y at %I:%M %p')}
Location: {event.location}

Description:
{event.description}

{f'Registration Fee: {event.registration_fee} {event.title}' if event.registration_fee > 0 else 'Free Event'}
{f'Registration Deadline: {event.registration_deadline.strftime("%B %d, %Y")}' if event.registration_deadline else ''}

{f'Limited to {event.max_attendees} attendees' if event.max_attendees else ''}

We hope to see you there!

Best regards,
Alumni Relations Office""",
                        from_email="alumni@school.com",
                        recipient_list=[alumni.personal_email],
                        fail_silently=True
                    )
                    notification_count += 1
                except Exception as exc:
                    logger.error(f"Error sending event notification to {alumni.personal_email}: {exc}")

    logger.info(f"Sent {notification_count} event notifications")
    return f"Sent {notification_count} notifications"


@shared_task
def generate_donation_receipts():
    """Generate tax receipts for donations that don't have them."""
    from .models import AlumniDonation

    donations_without_receipts = AlumniDonation.objects.filter(
        tax_receipt_sent=False
    ).select_related('alumni__student__student')

    receipt_count = 0
    for donation in donations_without_receipts:
        # Generate receipt number
        year = donation.donated_at.year
        receipt_number = f"TAX-{year}-{donation.id:06d}"

        donation.tax_receipt_number = receipt_number
        donation.tax_receipt_sent = True
        donation.save()

        # In a real implementation, you'd generate a PDF receipt here
        # and attach it to an email

        if donation.alumni.personal_email and not donation.is_anonymous:
            try:
                send_mail(
                    subject=f"Tax Receipt - Donation {receipt_number}",
                    message=f"""Dear {donation.alumni.student.student.get_full_name},

Please find your tax receipt for your donation:

Receipt Number: {receipt_number}
Donation Amount: {donation.currency} {donation.amount}
Donation Date: {donation.donated_at.strftime('%B %d, %Y')}
Purpose: {donation.get_purpose_display()}

This receipt is for tax purposes. Please keep it for your records.

Thank you for your support!

Best regards,
Alumni Relations Office""",
                    from_email="alumni@school.com",
                    recipient_list=[donation.alumni.personal_email],
                    fail_silently=True
                )
                receipt_count += 1
            except Exception as exc:
                logger.error(f"Error sending receipt to {donation.alumni.personal_email}: {exc}")

    logger.info(f"Generated {receipt_count} donation receipts")
    return f"Generated {receipt_count} receipts"


@shared_task
def update_alumni_career_data():
    """Periodic task to remind alumni to update their career information."""
    from .models import Alumni

    # Find alumni whose data hasn't been updated in over a year
    one_year_ago = timezone.now() - timedelta(days=365)

    stale_profiles = Alumni.objects.filter(
        is_active=True,
        updated_at__lt=one_year_ago
    ).exclude(personal_email='').select_related('student__student')

    reminder_count = 0
    for alumni in stale_profiles[:50]:  # Limit to 50 per run
        if alumni.personal_email:
            try:
                send_mail(
                    subject="Update Your Alumni Profile",
                    message=f"""Dear {alumni.student.student.get_full_name},

It's been a while since you last updated your alumni profile. Please take a moment to update your:

- Current occupation and employer
- Contact information
- Career achievements

Keeping your profile up-to-date helps us:
- Connect you with relevant opportunities
- Showcase alumni success stories
- Build a stronger alumni network

Thank you for staying connected!

Best regards,
Alumni Relations Office""",
                    from_email="alumni@school.com",
                    recipient_list=[alumni.personal_email],
                    fail_silently=True
                )
                reminder_count += 1
            except Exception as exc:
                logger.error(f"Error sending profile update reminder to {alumni.personal_email}: {exc}")

    logger.info(f"Sent {reminder_count} profile update reminders")
    return f"Sent {reminder_count} reminders"
