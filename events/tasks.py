from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, timedelta
from .models import Event


@shared_task
def send_event_reminders():
    """Send reminders for upcoming events."""
    tomorrow = datetime.now() + timedelta(days=1)
    events = Event.objects.filter(
        send_reminder=True,
        reminder_sent=False,
        start_date__date=tomorrow.date()
    )

    for event in events:
        # Get target audience email addresses
        recipients = []

        if event.target_audience == 'all':
            # Send to all users in tenant
            from accounts.models import User
            recipients = list(User.objects.filter(
                tenant=event.tenant
            ).values_list('email', flat=True))
        elif event.target_audience == 'students':
            from accounts.models import User
            recipients = list(User.objects.filter(
                tenant=event.tenant,
                role='student'
            ).values_list('email', flat=True))
        elif event.target_audience == 'parents':
            from accounts.models import User
            recipients = list(User.objects.filter(
                tenant=event.tenant,
                role='parent'
            ).values_list('email', flat=True))
        elif event.target_audience == 'staff':
            from accounts.models import User
            recipients = list(User.objects.filter(
                tenant=event.tenant,
                role__in=['professor', 'direction']
            ).values_list('email', flat=True))

        if recipients:
            send_mail(
                subject=f'[{event.tenant.name}] Upcoming Event: {event.title}',
                message=f'Event: {event.title}\nDate: {event.start_date}\nLocation: {event.location}\n\n{event.description}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True
            )

        event.reminder_sent = True
        event.save()

    return events.count()
