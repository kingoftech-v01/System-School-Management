"""
Decorators for role-based access control and security checks.
Use these to protect views based on user role and tenant access.
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django_ratelimit.decorators import ratelimit


def get_user_role(user):
    """Helper to get user role from User object."""
    if hasattr(user, 'role') and user.role:
        return user.role
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
    return None


def role_required(*allowed_roles, redirect_to='/dashboard/'):
    """
    Decorator to restrict view access to specific roles.

    Usage:
        @role_required('direction', 'admin')
        def my_view(request):
            ...

    Args:
        *allowed_roles: Variable number of role names (e.g., 'student', 'professor', 'direction', 'admin')
        redirect_to: URL to redirect to if access denied (default: '/dashboard/')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user_role = get_user_role(request.user)

            # Superusers bypass all checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Check if user has required role
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)

            # Access denied
            messages.error(
                request,
                f"Access denied. This page is only available to: {', '.join(allowed_roles)}"
            )
            return redirect(redirect_to)

        return wrapper
    return decorator


def tenant_required(view_func):
    """
    Decorator to ensure user belongs to the current tenant.
    Prevents cross-tenant data access.

    Usage:
        @tenant_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Skip check for superusers
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Check if request has tenant
        if not hasattr(request, 'tenant'):
            messages.error(request, "Tenant context not found.")
            return redirect('/')

        # Check if user belongs to tenant
        if hasattr(request.user, 'tenant'):
            if request.user.tenant != request.tenant:
                messages.error(request, "Access denied. You do not belong to this school.")
                return HttpResponseForbidden("Access denied to this tenant.")

        return view_func(request, *args, **kwargs)

    return wrapper


def rate_limit_by_role(group='default', key='user', rate='100/h', method='ALL'):
    """
    Rate limiting decorator that varies by user role.

    Usage:
        @rate_limit_by_role(group='search', rate='50/h')
        def search_view(request):
            ...

    Rate limits are defined in settings.RATE_LIMITS
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Get user-specific rate limit from settings
            from django.conf import settings
            user_role = get_user_role(request.user)

            # Get rate limit for user role
            rate_limits = getattr(settings, 'RATE_LIMITS', {})
            user_rate = rate_limits.get(user_role, rate)

            # Apply rate limit
            limited_view = ratelimit(
                group=group,
                key=key,
                rate=user_rate,
                method=method
            )(view_func)

            return limited_view(request, *args, **kwargs)

        return wrapper
    return decorator


def direction_only(view_func):
    """
    Shortcut decorator for direction-only views.

    Usage:
        @direction_only
        def monitoring_view(request):
            ...
    """
    return role_required('direction', 'admin')(view_func)


def professor_only(view_func):
    """
    Shortcut decorator for professor-only views.

    Usage:
        @professor_only
        def grade_entry_view(request):
            ...
    """
    return role_required('professor', 'direction', 'admin')(view_func)


def student_only(view_func):
    """
    Shortcut decorator for student-only views.

    Usage:
        @student_only
        def my_results_view(request):
            ...
    """
    return role_required('student')(view_func)


def parent_only(view_func):
    """
    Shortcut decorator for parent-only views.

    Usage:
        @parent_only
        def child_results_view(request):
            ...
    """
    return role_required('parent')(view_func)


# Backward compatibility aliases
def admin_required(function=None, redirect_to="/"):
    """Legacy decorator - use role_required('admin') instead."""
    if function:
        return role_required('admin', redirect_to=redirect_to)(function)
    return role_required('admin', redirect_to=redirect_to)


def lecturer_required(function=None, redirect_to="/"):
    """Legacy decorator - use role_required('professor') instead."""
    if function:
        return role_required('professor', redirect_to=redirect_to)(function)
    return role_required('professor', redirect_to=redirect_to)


def student_required(function=None, redirect_to="/"):
    """Legacy decorator - use role_required('student') instead."""
    if function:
        return role_required('student', redirect_to=redirect_to)(function)
    return role_required('student', redirect_to=redirect_to)


def require_2fa(view_func):
    """
    Decorator to enforce 2FA for specific views.

    Usage:
        @require_2fa
        def sensitive_view(request):
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check if user has 2FA enabled
        has_2fa = False

        if hasattr(request.user, 'totpdevice_set'):
            has_2fa = request.user.totpdevice_set.filter(confirmed=True).exists()

        if hasattr(request.user, 'mfa') and not has_2fa:
            has_2fa = request.user.mfa.exists()

        if not has_2fa:
            messages.warning(request, "Two-Factor Authentication is required for this action.")
            return redirect('mfa_activate_totp')

        return view_func(request, *args, **kwargs)

    return wrapper
