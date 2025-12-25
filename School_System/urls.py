"""
Tenant-specific URL configuration for School Management System.
This URLconf is used for tenant schemas (individual schools).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
from django.views import defaults as default_views
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Customize admin
admin.site.site_header = "School Management System"
admin.site.site_title = "School Admin"
admin.site.index_title = "Administration"

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Django Allauth (authentication, 2FA)
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('allauth.mfa.urls')),

    # Custom accounts (profiles, dashboards, role management)
    path('accounts/', include('accounts.urls')),

    # Core functionality
    path('', include('core.urls')),

    # Course management
    path('courses/', include('course.urls')),

    # Attendance
    path('attendance/', include('attendance.urls')),

    # Payments
    path('payments/', include('payments.urls')),

    # Results
    path('results/', include('result.urls')),

    # Enrollment
    path('enrollment/', include('enrollment.urls')),

    # Search (Direction only)
    path('search/', include('search.urls')),

    # Notes
    path('notes/', include('notes.urls')),

    # Filieres (Academic tracks)
    path('filieres/', include('filieres.urls')),

    # Library
    path('library/', include('library.urls')),

    # Events
    path('events/', include('events.urls')),

    # Discipline
    path('discipline/', include('discipline.urls')),

    # Monitoring (Direction dashboards)
    path('monitoring/', include('monitoring.urls')),

    # Quiz (if applicable)
    path('quiz/', include('quiz.urls')),

    # API endpoints
    path('api/token/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Internationalization
    path('i18n/', include('django.conf.urls.i18n')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

    # Error page testing in development
    urlpatterns += [
        path('400/', default_views.bad_request, kwargs={'exception': Exception('Bad Request!')}),
        path('403/', default_views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        path('404/', default_views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        path('500/', default_views.server_error),
    ]
