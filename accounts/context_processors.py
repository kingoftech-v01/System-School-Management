"""
Context processors for accounts app.
Makes tenant and user role information available in all templates.
"""

from django.conf import settings


def tenant_context(request):
    """
    Add current tenant information to template context.
    Available in templates as {{ tenant }}, {{ tenant_name }}, etc.
    """
    context = {}

    if hasattr(request, 'tenant') and request.tenant:
        tenant = request.tenant

        context['tenant'] = tenant
        context['tenant_name'] = tenant.name
        context['tenant_logo'] = tenant.logo.url if tenant.logo else None
        context['tenant_primary_color'] = tenant.primary_color
        context['school_name'] = tenant.name  # Alias for convenience
        context['school'] = tenant  # Alias for convenience

    return context


def user_role_context(request):
    """
    Add user role information to template context.
    Available in templates as {{ user_role }}, {{ is_student }}, {{ is_professor }}, etc.
    """
    context = {
        'user_role': None,
        'is_student': False,
        'is_professor': False,
        'is_parent': False,
        'is_direction': False,
        'is_admin': False,
    }

    if request.user.is_authenticated:
        # Get role from request (set by RoleMiddleware)
        user_role = getattr(request, 'user_role', None)

        if not user_role:
            # Fallback: determine role from user model
            if hasattr(request.user, 'role') and request.user.role:
                user_role = request.user.role
            elif request.user.is_superuser:
                user_role = 'admin'
            elif hasattr(request.user, 'is_student') and request.user.is_student:
                user_role = 'student'
            elif hasattr(request.user, 'is_lecturer') and request.user.is_lecturer:
                user_role = 'professor'
            elif hasattr(request.user, 'is_parent') and request.user.is_parent:
                user_role = 'parent'
            elif hasattr(request.user, 'is_dep_head') and request.user.is_dep_head:
                user_role = 'direction'

        context['user_role'] = user_role

        # Set boolean flags for easy template conditionals
        if user_role:
            context[f'is_{user_role}'] = True

    return context


def app_settings_context(request):
    """
    Add commonly used settings to template context.
    """
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'School Management System'),
        'CURRENT_ACADEMIC_YEAR': getattr(settings, 'CURRENT_ACADEMIC_YEAR', '2024-2025'),
        'SUPPORT_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@schoolsystem.com'),
        'DEBUG': settings.DEBUG,
    }


def navigation_context(request):
    """
    Build navigation menu based on user role.
    """
    nav_items = []

    if not request.user.is_authenticated:
        return {'navigation': nav_items}

    user_role = getattr(request, 'user_role', 'student')

    # Common items for all roles
    nav_items.append({
        'name': 'Dashboard',
        'url': '/dashboard/',
        'icon': 'fas fa-tachometer-alt'
    })

    # Role-specific navigation
    if user_role == 'student':
        nav_items.extend([
            {'name': 'My Courses', 'url': '/courses/', 'icon': 'fas fa-book'},
            {'name': 'Attendance', 'url': '/attendance/my/', 'icon': 'fas fa-calendar-check'},
            {'name': 'Results', 'url': '/results/my/', 'icon': 'fas fa-chart-line'},
            {'name': 'Payments', 'url': '/payments/my/', 'icon': 'fas fa-credit-card'},
            {'name': 'Library', 'url': '/library/my-books/', 'icon': 'fas fa-book-reader'},
            {'name': 'Events', 'url': '/events/', 'icon': 'fas fa-calendar-alt'},
        ])

    elif user_role == 'parent':
        nav_items.extend([
            {'name': 'My Children', 'url': '/accounts/children/', 'icon': 'fas fa-users'},
            {'name': 'Attendance', 'url': '/attendance/child/', 'icon': 'fas fa-calendar-check'},
            {'name': 'Results', 'url': '/results/child/', 'icon': 'fas fa-chart-line'},
            {'name': 'Payments', 'url': '/payments/child/', 'icon': 'fas fa-credit-card'},
            {'name': 'Events', 'url': '/events/', 'icon': 'fas fa-calendar-alt'},
        ])

    elif user_role == 'professor':
        nav_items.extend([
            {'name': 'My Classes', 'url': '/courses/my-classes/', 'icon': 'fas fa-chalkboard-teacher'},
            {'name': 'Attendance', 'url': '/attendance/record/', 'icon': 'fas fa-calendar-check'},
            {'name': 'Grades', 'url': '/results/grade-entry/', 'icon': 'fas fa-edit'},
            {'name': 'Notes', 'url': '/notes/', 'icon': 'fas fa-sticky-note'},
            {'name': 'Students', 'url': '/search/students/', 'icon': 'fas fa-user-graduate'},
        ])

    elif user_role in ['direction', 'admin']:
        nav_items.extend([
            {'name': 'Monitoring', 'url': '/monitoring/', 'icon': 'fas fa-chart-bar'},
            {'name': 'Search', 'url': '/search/', 'icon': 'fas fa-search'},
            {'name': 'Enrollment', 'url': '/enrollment/', 'icon': 'fas fa-user-plus'},
            {'name': 'Courses', 'url': '/courses/', 'icon': 'fas fa-book'},
            {'name': 'Attendance', 'url': '/attendance/', 'icon': 'fas fa-calendar-check'},
            {'name': 'Results', 'url': '/results/', 'icon': 'fas fa-chart-line'},
            {'name': 'Payments', 'url': '/payments/', 'icon': 'fas fa-credit-card'},
            {'name': 'Library', 'url': '/library/', 'icon': 'fas fa-book-reader'},
            {'name': 'Events', 'url': '/events/', 'icon': 'fas fa-calendar-alt'},
            {'name': 'Discipline', 'url': '/discipline/', 'icon': 'fas fa-gavel'},
            {'name': 'Filieres', 'url': '/filieres/', 'icon': 'fas fa-graduation-cap'},
        ])

    # Admin link for superusers
    if request.user.is_superuser:
        nav_items.append({
            'name': 'Admin',
            'url': '/admin/',
            'icon': 'fas fa-cog'
        })

    return {'navigation': nav_items}


def permissions_context(request):
    """
    Add permission checks to template context for showing/hiding UI elements.
    """
    context = {
        'can_view_all_students': False,
        'can_manage_payments': False,
        'can_manage_enrollment': False,
        'can_view_monitoring': False,
        'can_manage_discipline': False,
        'can_export_data': False,
    }

    if not request.user.is_authenticated:
        return context

    user_role = getattr(request, 'user_role', None)

    if user_role in ['direction', 'admin']:
        # Direction and admin have all permissions
        context = {
            'can_view_all_students': True,
            'can_manage_payments': True,
            'can_manage_enrollment': True,
            'can_view_monitoring': True,
            'can_manage_discipline': True,
            'can_export_data': True,
        }
    elif user_role == 'professor':
        # Professors have limited permissions
        context['can_view_monitoring'] = False  # Can see limited stats
        context['can_manage_discipline'] = True  # Can report incidents

    return context
