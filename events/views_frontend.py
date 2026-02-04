from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from accounts.decorators import direction_only, tenant_required
from django_ratelimit.decorators import ratelimit
from .models import Event
from core.models import School


def get_current_tenant(request):
    """Get current tenant from request or return default for development."""
    if hasattr(request, 'tenant') and request.tenant:
        return request.tenant
    # Development mode: get or create default School
    school, _ = School.objects.get_or_create(
        slug='default',
        defaults={
            'name': 'Default School',
            'email': 'admin@school.local',
        }
    )
    return school


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def event_list(request):
    """List all events for the current tenant."""
    tenant = get_current_tenant(request)
    events = Event.objects.filter(tenant=tenant).order_by('start_date')

    # Filter by target audience based on user role
    if request.user.role == 'student':
        events = events.filter(target_audience__in=['all', 'students'])
    elif request.user.role == 'parent':
        events = events.filter(target_audience__in=['all', 'parents'])
    elif request.user.role == 'professor':
        events = events.filter(target_audience__in=['all', 'staff'])
    # Direction can see all events

    return render(request, 'events/event_list.html', {
        'events': events,
        'title': _('Events Calendar')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def event_create(request):
    """Create a new event (direction only)."""
    from .forms import EventForm

    tenant = get_current_tenant(request)

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.tenant = tenant
            event.created_by = request.user
            event.save()
            messages.success(request, _('Event created successfully.'))
            return redirect('frontend:events:frontend:event_list')
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {
        'form': form,
        'title': _('Create Event')
    })


@login_required
@tenant_required
def event_detail(request, pk):
    """View event details."""
    tenant = get_current_tenant(request)
    event = get_object_or_404(Event, pk=pk, tenant=tenant)

    return render(request, 'events/event_detail.html', {
        'event': event,
        'title': event.title
    })
