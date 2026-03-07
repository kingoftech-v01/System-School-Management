"""
Public schema URLs for the core app.
Landing page for tenant selection.
"""

from django.urls import path
from django.views.generic import TemplateView

app_name = 'core_public'

urlpatterns = [
    # Landing page
    path('', TemplateView.as_view(template_name='core/landing.html'), name='landing'),
]
