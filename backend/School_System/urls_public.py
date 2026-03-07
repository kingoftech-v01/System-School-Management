"""
Public schema URL configuration for School Management System.
This URLconf is used for the public schema (shared/system-wide URLs).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize admin for public schema
admin.site.site_header = "Multi-Tenant School System Admin"
admin.site.site_title = "System Admin"
admin.site.index_title = "Tenant Management"

urlpatterns = [
    # System admin (for managing tenants)
    path('system/admin/', admin.site.urls),

    # Tenant landing/selection page
    path('', include('core.urls_public')),
]

# Static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
