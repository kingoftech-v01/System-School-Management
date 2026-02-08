from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from accounts.decorators import direction_only, tenant_required
from django_ratelimit.decorators import ratelimit

from .forms import EventForm
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
    """List all events for the current tenant with filtering and pagination."""
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

    # Filter by event_type
    event_type = request.GET.get('event_type', '').strip()
    if event_type:
        events = events.filter(event_type=event_type)

    # Filter by date range
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        try:
            parsed_from = datetime.strptime(date_from, '%Y-%m-%d')
            events = events.filter(start_date__gte=parsed_from)
        except ValueError:
            pass
    if date_to:
        try:
            parsed_to = datetime.strptime(date_to, '%Y-%m-%d')
            events = events.filter(start_date__lte=parsed_to)
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(events, 20)
    page = request.GET.get('page')
    events = paginator.get_page(page)

    return render(request, 'events/event_list.html', {
        'events': events,
        'event_type_choices': Event.EVENT_TYPE_CHOICES,
        'current_event_type': event_type,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'title': _('Events Calendar'),
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def event_create(request):
    """Create a new event (direction only)."""
    tenant = get_current_tenant(request)

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.tenant = tenant
            event.created_by = request.user
            event.save()
            messages.success(request, _('Event created successfully.'))
            return redirect('frontend:events:event_list')
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


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def event_edit(request, pk):
    """Edit an existing event (direction only)."""
    tenant = get_current_tenant(request)
    event = get_object_or_404(Event, pk=pk, tenant=tenant)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _('Event updated successfully.'))
            return redirect('frontend:events:event_detail', pk=event.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {
        'form': form,
        'event': event,
        'title': _('Edit Event'),
    })


@login_required
@direction_only
@tenant_required
def event_delete(request, pk):
    """Delete an event. GET shows confirm page, POST deletes."""
    tenant = get_current_tenant(request)
    event = get_object_or_404(Event, pk=pk, tenant=tenant)

    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, _(f'Event "{title}" has been deleted.'))
        return redirect('frontend:events:event_list')

    return render(request, 'events/event_confirm_delete.html', {
        'event': event,
        'title': _('Delete Event'),
    })
