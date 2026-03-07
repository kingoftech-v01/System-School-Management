"""
School Management System - Main URL Configuration.

API-only backend. All frontend is served by React (web) and React Native (mobile).

Namespaces:
- API: api:app:resource-name
- Admin: Django admin at /admin/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

# Customize admin
admin.site.site_header = "School Management System"
admin.site.site_title = "School Admin"
admin.site.index_title = "Administration"


def _get(module_path, attr='api_urlpatterns'):
    """Import specific pattern list from an app's urls module."""
    from importlib import import_module
    return getattr(import_module(module_path), attr)


# ============================================================================
# API V1 URLPATTERNS
# ============================================================================

api_v1_urlpatterns = [
    path('core/', include((_get('core.urls'), 'core'))),
    path('accounts/', include((_get('accounts.urls'), 'accounts'))),
    path('courses/', include((_get('course.urls'), 'course'))),
    path('filieres/', include((_get('filieres.urls'), 'filieres'))),
    path('quiz/', include((_get('quiz.urls'), 'quiz'))),
    path('results/', include((_get('result.urls'), 'result'))),
    path('grading/', include((_get('grading.urls'), 'grading'))),
    path('enrollment/', include((_get('enrollment.urls'), 'enrollment'))),
    path('admissions/', include((_get('admissions.urls'), 'admissions'))),
    path('library/', include((_get('library.urls'), 'library'))),
    path('notes/', include((_get('notes.urls'), 'notes'))),
    path('attendance/', include((_get('attendance.urls'), 'attendance'))),
    path('monitoring/', include((_get('monitoring.urls'), 'monitoring'))),
    path('forums/', include((_get('forums.urls'), 'forums'))),
    path('events/', include((_get('events.urls'), 'events'))),
    path('notices/', include((_get('notices.urls'), 'notices'))),
    path('articles/', include((_get('articles.urls'), 'articles'))),
    path('discipline/', include((_get('discipline.urls'), 'discipline'))),
    path('certificates/', include((_get('certificates.urls'), 'certificates'))),
    path('analytics/', include((_get('analytics.urls'), 'analytics'))),
    path('alumni/', include((_get('alumni.urls'), 'alumni'))),
    path('payments/', include((_get('payments.urls'), 'payments'))),
    path('search/', include((_get('search.urls'), 'search'))),
    path('dailystat/', include((_get('dailystat.urls'), 'dailystat'))),
    path('scheduling/', include((_get('scheduling.urls'), 'scheduling'))),
    path('anomaly/', include((_get('anomaly_detection.urls'), 'anomaly_detection'))),
    path('safeguarding/', include((_get('safeguarding.urls'), 'safeguarding'))),
    path('audit/', include((_get('audit.urls'), 'audit'))),
    path('reports/', include((_get('reports.urls'), 'reports'))),
]


# ============================================================================
# MAIN URL CONFIGURATION
# ============================================================================

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API v1 (namespace: api:app:resource)
    path('api/v1/', include((api_v1_urlpatterns, 'api'), namespace='api')),

    # JWT Authentication
    path('api/token/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Internationalization
    path('i18n/', include('django.conf.urls.i18n')),
]


# ============================================================================
# DEVELOPMENT SETTINGS
# ============================================================================

# Debug toolbar
try:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
except ImportError:
    pass

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
