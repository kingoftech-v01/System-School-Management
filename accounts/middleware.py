"""
Middleware for accounts app.
Handles tenant context, role checking, 2FA enforcement, and audit logging.
"""

import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.conf import settings
try:
    from django_tenants.utils import get_tenant_model
except ImportError:
    get_tenant_model = None
from core.models import ActivityLog

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Ensures tenant context is properly set for all requests.
    django-tenants TenantMainMiddleware handles schema switching,
    this middleware adds additional tenant context to request.
    In development mode (no django-tenants), sets a default tenant.
    """

    _default_tenant = None

    def process_request(self, request):
        if hasattr(request, 'tenant') and request.tenant:
            # Production: django-tenants already set the tenant
            request.current_tenant = request.tenant

            logger.info(
                f"Request from tenant: {request.tenant.name} (schema: {request.tenant.schema_name})"
            )
        elif 'django_tenants' not in settings.INSTALLED_APPS:
            # Development mode: set a default tenant from the School table
            request.tenant = self._get_default_tenant()
            request.current_tenant = request.tenant
        return None

    @classmethod
    def _get_default_tenant(cls):
        """Get or create a default School for development mode."""
        if cls._default_tenant is not None:
            # Verify it still exists in the DB
            try:
                cls._default_tenant.refresh_from_db()
                return cls._default_tenant
            except Exception:
                cls._default_tenant = None

        from core.models import School
        tenant = School.objects.first()
        if tenant is None:
            from datetime import date, timedelta
            tenant = School.objects.create(
                name='Development School',
                slug='dev-school',
                email='dev@school.local',
                phone='0000000000',
                address='Dev Address',
                city='Dev City',
                postal_code='00000',
                license_key='DEV-0000',
                subscription_start=date.today(),
                subscription_end=date.today() + timedelta(days=365),
            )
            logger.info(f"Created default development tenant: {tenant.name}")
        cls._default_tenant = tenant
        return tenant


class RoleMiddleware(MiddlewareMixin):
    """
    Adds user role information to request object for easy access in views and templates.
    """

    def process_request(self, request):
        if request.user.is_authenticated:
            # Get user role from the User model
            role = self.get_user_role(request.user)
            request.user_role = role

            # Add role to user object for template access
            request.user.current_role = role
        else:
            request.user_role = None
        return None

    @staticmethod
    def get_user_role(user):
        """Determine user's role based on User model fields."""
        # Check for custom role field first (if it exists)
        if hasattr(user, 'role') and user.role:
            return user.role

        # Fallback to boolean flags for backward compatibility
        if user.is_superuser:
            return 'admin'
        if hasattr(user, 'is_student') and user.is_student:
            return 'student'
        if hasattr(user, 'is_lecturer') and user.is_lecturer:
            return 'professor'
        if hasattr(user, 'is_parent') and user.is_parent:
            return 'parent'
        if hasattr(user, 'is_dep_head') and user.is_dep_head:
            return 'direction'

        # Default to student if no role identified
        return 'student'


class Enforce2FAMiddleware(MiddlewareMixin):
    """
    Enforces 2FA for users in roles that require it (professor, direction, admin).
    Redirects to 2FA setup page if not configured.
    """

    EXEMPT_PATHS = [
        '/accounts/logout/',
        '/accounts/login/',
        '/accounts/2fa/',
        '/accounts/mfa/',
        '/accounts/totp/',
        '/accounts/reauthenticate/',
        '/accounts/authenticate/',
        '/admin/logout/',
        '/static/',
        '/media/',
    ]

    ROLES_REQUIRING_2FA = getattr(settings, 'ROLES_REQUIRING_2FA', ['professor', 'prefet', 'secretary', 'direction', 'admin'])

    def process_request(self, request):
        # Skip if user not authenticated
        if not request.user.is_authenticated:
            return None

        # Skip for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None

        # Get user role
        user_role = getattr(request, 'user_role', None)
        if not user_role:
            # Role middleware hasn't run yet or no role set
            user_role = RoleMiddleware.get_user_role(request.user)

        # Check if role requires 2FA
        if user_role not in self.ROLES_REQUIRING_2FA:
            return None

        # Check if user has 2FA enabled (django-allauth MFA)
        if hasattr(request.user, 'mfa') and request.user.mfa.exists():
            # User has MFA configured
            return None

        # Also check django-otp devices
        if hasattr(request.user, 'totpdevice_set') and request.user.totpdevice_set.filter(confirmed=True).exists():
            return None

        # User requires 2FA but doesn't have it set up
        if request.path != reverse('mfa_activate_totp'):
            messages.warning(
                request,
                "Two-Factor Authentication is required for your role. Please set it up to continue."
            )
            logger.warning(
                f"User {request.user.username} ({user_role}) attempting to access system without 2FA"
            )
            return redirect('mfa_activate_totp')

        return None


class ForcePasswordResetMiddleware(MiddlewareMixin):
    """
    Redirects users with must_change_password=True to the force password reset page.
    This handles accounts created with temporary passwords (e.g., from enrollment approval).
    """

    EXEMPT_PATHS = [
        '/accounts/password/force-reset/',
        '/accounts/logout/',
        '/static/',
        '/media/',
    ]

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        if not getattr(request.user, 'must_change_password', False):
            return None

        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None

        return redirect('frontend:accounts:force_password_reset')


class AuditLogMiddleware(MiddlewareMixin):
    """
    Logs sensitive actions for audit trail.
    Only logs actions that modify data or access sensitive information.
    """

    SENSITIVE_ACTIONS = [
        'create',
        'update',
        'delete',
        'export',
        'download',
        'payment',
        'grade',
        'attendance',
        'discipline',
    ]

    SENSITIVE_PATHS = [
        '/admin/',
        '/payments/',
        '/results/',
        '/grades/',
        '/search/',
        '/discipline/',
        '/monitoring/',
    ]

    def process_response(self, request, response):
        # Only log for authenticated users
        if not request.user.is_authenticated:
            return response

        # Only log POST, PUT, PATCH, DELETE requests
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return response

        # Check if path is sensitive
        is_sensitive_path = any(request.path.startswith(path) for path in self.SENSITIVE_PATHS)

        # Check if action is sensitive (from URL parameters or path)
        is_sensitive_action = any(action in request.path.lower() for action in self.SENSITIVE_ACTIONS)

        if is_sensitive_path or is_sensitive_action:
            # Log the action
            try:
                tenant_name = request.tenant.name if hasattr(request, 'tenant') else 'Unknown'
                user_role = getattr(request, 'user_role', 'unknown')

                message = (
                    f"User: {request.user.username} ({user_role}) | "
                    f"Tenant: {tenant_name} | "
                    f"Action: {request.method} {request.path} | "
                    f"IP: {self.get_client_ip(request)} | "
                    f"Status: {response.status_code}"
                )

                # Log to database
                ActivityLog.objects.create(message=message)

                # Log to file
                logger.info(f"AUDIT: {message}")

            except Exception as e:
                # Don't fail the request if logging fails
                logger.error(f"Audit logging failed: {str(e)}")

        return response

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuthSecurityMiddleware(MiddlewareMixin):
    """
    Additional authentication security checks.
    Handles session timeout, suspicious activity detection, etc.
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        # Check if user account is active
        if not request.user.is_active:
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, "Your account has been deactivated. Please contact support.")
            return redirect('account_login')

        # Check tenant subscription if multi-tenant
        if hasattr(request, 'tenant') and hasattr(request.tenant, 'is_subscription_valid'):
            if not request.tenant.is_subscription_valid():
                # Exempt admin users from subscription check
                if not request.user.is_superuser:
                    messages.error(
                        request,
                        "School subscription has expired. Please contact administration."
                    )
                    return redirect('subscription_expired')

        return None


class Require2FAMiddleware(MiddlewareMixin):
    """
    Alternative 2FA enforcement middleware (simpler version).
    Can be used instead of Enforce2FAMiddleware.
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        # Skip for certain paths
        skip_paths = ['/accounts/2fa/', '/accounts/logout/', '/static/', '/media/']
        if any(request.path.startswith(path) for path in skip_paths):
            return None

        # Check if user needs 2FA
        user_role = getattr(request.user, 'role', None) or RoleMiddleware.get_user_role(request.user)

        if user_role in ['professor', 'prefet', 'secretary', 'direction', 'admin']:
            # Check if 2FA is enabled
            has_2fa = False

            # Check allauth MFA
            if hasattr(request.user, 'emailaddress_set'):
                if request.user.emailaddress_set.filter(verified=True).exists():
                    has_2fa = True

            # Check OTP devices
            if hasattr(request.user, 'totpdevice_set'):
                if request.user.totpdevice_set.filter(confirmed=True).exists():
                    has_2fa = True

            if not has_2fa and request.path != '/accounts/2fa/setup/':
                messages.warning(request, "Please enable Two-Factor Authentication.")
                return redirect('/accounts/2fa/setup/')

        return None
