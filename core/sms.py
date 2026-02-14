"""
SMS utility module using Twilio.
Provides send_sms() function used by notification tasks across the system.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone_number, message):
    """
    Send an SMS via Twilio.
    Returns True on success, False on failure or if Twilio is not configured.
    """
    if not getattr(settings, 'SMS_ENABLED', False):
        logger.debug("SMS disabled (SMS_ENABLED=False), skipping SMS to %s", phone_number)
        return False

    if not getattr(settings, 'TWILIO_ACCOUNT_SID', ''):
        logger.warning("Twilio not configured (missing TWILIO_ACCOUNT_SID), skipping SMS")
        return False

    if not phone_number:
        logger.debug("No phone number provided, skipping SMS")
        return False

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        logger.info("SMS sent to %s", phone_number)
        return True
    except ImportError:
        logger.warning("twilio package not installed, skipping SMS")
        return False
    except Exception:
        logger.exception("Failed to send SMS to %s", phone_number)
        return False


def send_sms_to_parent(student, message):
    """
    Send SMS to a student's parent(s).
    Looks up parent phone numbers and sends the message to each.
    Returns the count of successfully sent messages.
    """
    sent = 0
    try:
        from accounts.models import Parent
        parents = Parent.objects.filter(student=student).select_related('user')
        for parent in parents:
            phone = getattr(parent.user, 'phone', '')
            if phone and send_sms(phone, message):
                sent += 1
    except Exception:
        logger.exception("Failed to send SMS to parent of student %s", student)
    return sent
