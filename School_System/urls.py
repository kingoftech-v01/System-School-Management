"""
School Management System - Main URL Configuration.

All apps follow nested namespace pattern:
- Frontend: frontend:app:view_name
- API: api:v1:app:resource-name
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


# ============================================================================
# FRONTEND URLPATTERNS
# ============================================================================

frontend_urlpatterns = [
    # Core (root)
    path('', include(('core.urls', 'core'), namespace='core')),

    # Accounts
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Academic
    path('courses/', include(('course.urls', 'course'), namespace='course')),
    path('filieres/', include(('filieres.urls', 'filieres'), namespace='filieres')),
    path('quiz/', include(('quiz.urls', 'quiz'), namespace='quiz')),
    path('results/', include(('result.urls', 'result'), namespace='result')),
    path('grading/', include(('grading.urls', 'grading'), namespace='grading')),

    # Student services
    path('enrollment/', include(('enrollment.urls', 'enrollment'), namespace='enrollment')),
    path('admissions/', include(('admissions.urls', 'admissions'), namespace='admissions')),
    path('library/', include(('library.urls', 'library'), namespace='library')),
    path('notes/', include(('notes.urls', 'notes'), namespace='notes')),

    # Attendance & monitoring
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('monitoring/', include(('monitoring.urls', 'monitoring'), namespace='monitoring')),

    # Communication
    path('forums/', include(('forums.urls', 'forums'), namespace='forums')),
    path('events/', include(('events.urls', 'events'), namespace='events')),
    path('notices/', include(('notices.urls', 'notices'), namespace='notices')),
    path('articles/', include(('articles.urls', 'articles'), namespace='articles')),

    # Student management
    path('discipline/', include(('discipline.urls', 'discipline'), namespace='discipline')),
    path('certificates/', include(('certificates.urls', 'certificates'), namespace='certificates')),

    # Analytics
    path('analytics/', include(('analytics.urls', 'analytics'), namespace='analytics')),

    # Alumni & Payments
    path('alumni/', include(('alumni.urls', 'alumni'), namespace='alumni')),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),

    # Search
    path('search/', include(('search.urls', 'search'), namespace='search')),
]


# ============================================================================
# API V1 URLPATTERNS
# ============================================================================

api_v1_urlpatterns = [
    path('core/', include(('core.urls', 'core'), namespace='core')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('courses/', include(('course.urls', 'course'), namespace='course')),
    path('filieres/', include(('filieres.urls', 'filieres'), namespace='filieres')),
    path('quiz/', include(('quiz.urls', 'quiz'), namespace='quiz')),
    path('results/', include(('result.urls', 'result'), namespace='result')),
    path('grading/', include(('grading.urls', 'grading'), namespace='grading')),
    path('enrollment/', include(('enrollment.urls', 'enrollment'), namespace='enrollment')),
    path('admissions/', include(('admissions.urls', 'admissions'), namespace='admissions')),
    path('library/', include(('library.urls', 'library'), namespace='library')),
    path('notes/', include(('notes.urls', 'notes'), namespace='notes')),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('monitoring/', include(('monitoring.urls', 'monitoring'), namespace='monitoring')),
    path('forums/', include(('forums.urls', 'forums'), namespace='forums')),
    path('events/', include(('events.urls', 'events'), namespace='events')),
    path('notices/', include(('notices.urls', 'notices'), namespace='notices')),
    path('articles/', include(('articles.urls', 'articles'), namespace='articles')),
    path('discipline/', include(('discipline.urls', 'discipline'), namespace='discipline')),
    path('certificates/', include(('certificates.urls', 'certificates'), namespace='certificates')),
    path('analytics/', include(('analytics.urls', 'analytics'), namespace='analytics')),
    path('alumni/', include(('alumni.urls', 'alumni'), namespace='alumni')),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),
    path('search/', include(('search.urls', 'search'), namespace='search')),
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

    # API v1 (namespace: api:v1:app:resource)
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


# ============================================================================
# CUSTOM ERROR HANDLERS
# ============================================================================

handler403 = 'accounts.views_frontend.custom_403_view'
handler404 = 'accounts.views_frontend.custom_404_view'
handler500 = 'accounts.views_frontend.custom_500_view'
