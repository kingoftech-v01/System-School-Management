"""
School Management System - Main URL Configuration.

All apps follow nested namespace pattern:
- Frontend: frontend:app:view_name
- API: api:app:resource-name
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


def _get(module_path, attr='frontend_urlpatterns'):
    """Import specific pattern list from an app's urls module."""
    from importlib import import_module
    return getattr(import_module(module_path), attr)


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Core (root)
    path('', include((_get('core.urls'), 'core'))),

    # Accounts
    path('accounts/', include((_get('accounts.urls'), 'accounts'))),

    # Academic
    path('courses/', include((_get('course.urls'), 'course'))),
    path('filieres/', include((_get('filieres.urls'), 'filieres'))),
    path('quiz/', include((_get('quiz.urls'), 'quiz'))),
    path('results/', include((_get('result.urls'), 'result'))),
    path('grading/', include((_get('grading.urls'), 'grading'))),

    # Student services
    path('enrollment/', include((_get('enrollment.urls'), 'enrollment'))),
    path('admissions/', include((_get('admissions.urls'), 'admissions'))),
    path('library/', include((_get('library.urls'), 'library'))),
    path('notes/', include((_get('notes.urls'), 'notes'))),

    # Attendance & monitoring
    path('attendance/', include((_get('attendance.urls'), 'attendance'))),
    path('monitoring/', include((_get('monitoring.urls'), 'monitoring'))),
    path('dailystat/', include((_get('dailystat.urls'), 'dailystat'))),

    # Communication
    path('forums/', include((_get('forums.urls'), 'forums'))),
    path('events/', include((_get('events.urls'), 'events'))),
    path('notices/', include((_get('notices.urls'), 'notices'))),
    path('articles/', include((_get('articles.urls'), 'articles'))),

    # Student management
    path('discipline/', include((_get('discipline.urls'), 'discipline'))),
    path('certificates/', include((_get('certificates.urls'), 'certificates'))),

    # Analytics
    path('analytics/', include((_get('analytics.urls'), 'analytics'))),

    # Alumni & Payments
    path('alumni/', include((_get('alumni.urls'), 'alumni'))),
    path('payments/', include((_get('payments.urls'), 'payments'))),

    # Search
    path('search/', include((_get('search.urls'), 'search'))),

    # Scheduling & Timetable
    path('scheduling/', include((_get('scheduling.urls'), 'scheduling'))),

    # Anomaly Detection
    path('anomaly/', include((_get('anomaly_detection.urls'), 'anomaly_detection'))),

    # Safeguarding & Reports
    path('safeguarding/', include((_get('safeguarding.urls'), 'safeguarding'))),
    path('reports/', include((_get('reports.urls'), 'reports'))),
]


# ============================================================================
# API V1 URLPATTERNS
# ============================================================================

api_v1_urlpatterns = [
    path('core/', include((_get('core.urls', 'api_urlpatterns'), 'core'))),
    path('accounts/', include((_get('accounts.urls', 'api_urlpatterns'), 'accounts'))),
    path('courses/', include((_get('course.urls', 'api_urlpatterns'), 'course'))),
    path('filieres/', include((_get('filieres.urls', 'api_urlpatterns'), 'filieres'))),
    path('quiz/', include((_get('quiz.urls', 'api_urlpatterns'), 'quiz'))),
    path('results/', include((_get('result.urls', 'api_urlpatterns'), 'result'))),
    path('grading/', include((_get('grading.urls', 'api_urlpatterns'), 'grading'))),
    path('enrollment/', include((_get('enrollment.urls', 'api_urlpatterns'), 'enrollment'))),
    path('admissions/', include((_get('admissions.urls', 'api_urlpatterns'), 'admissions'))),
    path('library/', include((_get('library.urls', 'api_urlpatterns'), 'library'))),
    path('notes/', include((_get('notes.urls', 'api_urlpatterns'), 'notes'))),
    path('attendance/', include((_get('attendance.urls', 'api_urlpatterns'), 'attendance'))),
    path('monitoring/', include((_get('monitoring.urls', 'api_urlpatterns'), 'monitoring'))),
    path('forums/', include((_get('forums.urls', 'api_urlpatterns'), 'forums'))),
    path('events/', include((_get('events.urls', 'api_urlpatterns'), 'events'))),
    path('notices/', include((_get('notices.urls', 'api_urlpatterns'), 'notices'))),
    path('articles/', include((_get('articles.urls', 'api_urlpatterns'), 'articles'))),
    path('discipline/', include((_get('discipline.urls', 'api_urlpatterns'), 'discipline'))),
    path('certificates/', include((_get('certificates.urls', 'api_urlpatterns'), 'certificates'))),
    path('analytics/', include((_get('analytics.urls', 'api_urlpatterns'), 'analytics'))),
    path('alumni/', include((_get('alumni.urls', 'api_urlpatterns'), 'alumni'))),
    path('payments/', include((_get('payments.urls', 'api_urlpatterns'), 'payments'))),
    path('search/', include((_get('search.urls', 'api_urlpatterns'), 'search'))),
    path('dailystat/', include((_get('dailystat.urls', 'api_urlpatterns'), 'dailystat'))),
    path('scheduling/', include((_get('scheduling.urls', 'api_urlpatterns'), 'scheduling'))),
    path('anomaly/', include((_get('anomaly_detection.urls', 'api_urlpatterns'), 'anomaly_detection'))),

    # Safeguarding & Audit
    path('safeguarding/', include((_get('safeguarding.urls', 'api_urlpatterns'), 'safeguarding'))),
    path('audit/', include((_get('audit.urls', 'api_urlpatterns'), 'audit'))),
    path('reports/', include((_get('reports.urls', 'api_urlpatterns'), 'reports'))),
]


# ============================================================================
# MAIN URL CONFIGURATION
# ============================================================================

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Django Allauth (authentication, 2FA)
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('allauth.mfa.urls')),

    # API v1 (namespace: api:app:resource)
    path('api/v1/', include((api_v1_urlpatterns, 'api'), namespace='api')),

    # JWT Authentication
    path('api/token/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Frontend (namespace: frontend:app:view)
    path('', include((frontend_urlpatterns, 'frontend'))),

    # Internationalization
    path('i18n/', include('django.conf.urls.i18n')),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]


# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

# Debug toolbar - include URLs whenever the module is installed
# (must be outside DEBUG check so tests with DEBUG=False still resolve djdt namespace)
try:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
except ImportError:
    pass

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Error page testing in development
    urlpatterns += [
        path('400/', default_views.bad_request, kwargs={'exception': Exception('Bad Request!')}),
        path('403/', default_views.permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        path('404/', default_views.page_not_found, kwargs={'exception': Exception('Page not Found')}),
        path('500/', default_views.server_error),
    ]


# ============================================================================
# CUSTOM ERROR HANDLERS
# ============================================================================

handler403 = 'accounts.views_frontend.custom_403_view'
handler404 = 'accounts.views_frontend.custom_404_view'
handler500 = 'accounts.views_frontend.custom_500_view'
