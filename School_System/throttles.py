"""
Custom throttle classes for API rate limiting.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    High rate limit for short bursts of requests.
    Allows 60 requests per minute for authenticated users.
    """
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    """
    Lower rate limit for sustained API usage.
    Allows 1000 requests per hour for authenticated users.
    """
    scope = 'sustained'


class AnonymousBurstRateThrottle(AnonRateThrottle):
    """
    Rate limit for anonymous users (short bursts).
    Allows 20 requests per minute for unauthenticated users.
    """
    scope = 'anon_burst'


class AnonymousSustainedRateThrottle(AnonRateThrottle):
    """
    Rate limit for anonymous users (sustained).
    Allows 100 requests per hour for unauthenticated users.
    """
    scope = 'anon_sustained'


class VerificationRateThrottle(AnonRateThrottle):
    """
    Special rate limit for certificate verification endpoint.
    Allows higher volume for public verification.
    """
    scope = 'verification'


class UploadRateThrottle(UserRateThrottle):
    """
    Rate limit for file upload endpoints.
    Allows 30 uploads per hour.
    """
    scope = 'uploads'


class ExportRateThrottle(UserRateThrottle):
    """
    Rate limit for data export endpoints.
    Allows 10 exports per hour.
    """
    scope = 'exports'
