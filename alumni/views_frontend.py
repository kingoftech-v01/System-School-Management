"""
Frontend views for the alumni app.
"""

import uuid

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.decorators import direction_only
from .models import Alumni, AlumniEvent, AlumniDonation, AlumniAchievement
from .forms import AlumniForm, DonationForm


@login_required
def alumni_directory(request):
    """List alumni with search by name, graduation year, or occupation."""
    alumni_qs = Alumni.objects.select_related('student', 'student__student').filter(is_active=True)

    query = request.GET.get('q', '').strip()
    if query:
        alumni_qs = alumni_qs.filter(
            Q(student__student__first_name__icontains=query)
            | Q(student__student__last_name__icontains=query)
            | Q(graduation_year__icontains=query)
            | Q(current_occupation__icontains=query)
            | Q(current_employer__icontains=query)
        )

    paginator = Paginator(alumni_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'alumni/directory.html', {
        'page_obj': page_obj,
        'query': query,
        'title': _('Alumni Directory'),
    })


@login_required
def alumni_profile(request, pk):
    """Show a single alumni profile with their achievements."""
    alumni = get_object_or_404(
        Alumni.objects.select_related('student', 'student__student'),
        pk=pk,
    )
    achievements = alumni.achievements.filter(is_published=True)

    return render(request, 'alumni/profile.html', {
        'alumni': alumni,
        'achievements': achievements,
        'title': str(alumni),
    })


@login_required
def alumni_event_list(request):
    """List alumni events split into upcoming and past."""
    now = timezone.now()
    upcoming_events = AlumniEvent.objects.filter(
        is_active=True, event_date__gte=now,
    ).order_by('event_date')
    past_events = AlumniEvent.objects.filter(
        is_active=True, event_date__lt=now,
    ).order_by('-event_date')

    return render(request, 'alumni/event_list.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'title': _('Alumni Events'),
    })


@login_required
def alumni_event_detail(request, pk):
    """Show a single event with its attendees."""
    event = get_object_or_404(AlumniEvent, pk=pk, is_active=True)
    attendees = event.attendees.select_related('student', 'student__student').all()

    return render(request, 'alumni/event_detail.html', {
        'event': event,
        'attendees': attendees,
        'title': event.title,
    })


@login_required
def donation_create(request):
    """Allow an alumni to make a donation."""
    # Look up the current user's alumni record
    alumni = None
    if hasattr(request.user, 'student'):
        student_profile = request.user.student
        alumni = getattr(student_profile, 'alumni_record', None)

    if alumni is None:
        messages.error(request, _('You must have an alumni record to make a donation.'))
        return redirect('frontend:alumni:directory')

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.alumni = alumni
            donation.transaction_id = str(uuid.uuid4())
            donation.payment_method = 'bank_transfer'
            donation.save()
            messages.success(request, _('Thank you for your donation!'))
            return redirect('frontend:alumni:directory')
    else:
        form = DonationForm()

    return render(request, 'alumni/donation_form.html', {
        'form': form,
        'title': _('Make a Donation'),
    })


@direction_only
def alumni_create(request):
    """Create a new alumni record (direction only)."""
    if request.method == 'POST':
        form = AlumniForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Alumni record created successfully.'))
            return redirect('frontend:alumni:directory')
    else:
        form = AlumniForm()

    return render(request, 'alumni/alumni_form.html', {
        'form': form,
        'title': _('Create Alumni Record'),
    })


@direction_only
def alumni_edit(request, pk):
    """Edit an existing alumni record (direction only)."""
    alumni = get_object_or_404(Alumni, pk=pk)

    if request.method == 'POST':
        form = AlumniForm(request.POST, instance=alumni)
        if form.is_valid():
            form.save()
            messages.success(request, _('Alumni record updated successfully.'))
            return redirect('frontend:alumni:profile', pk=alumni.pk)
    else:
        form = AlumniForm(instance=alumni)

    return render(request, 'alumni/alumni_form.html', {
        'form': form,
        'alumni': alumni,
        'title': _('Edit Alumni Record'),
    })


@login_required
def achievement_list(request):
    """List all published alumni achievements."""
    achievements = AlumniAchievement.objects.filter(
        is_published=True,
    ).select_related('alumni', 'alumni__student', 'alumni__student__student')

    paginator = Paginator(achievements, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'alumni/achievement_list.html', {
        'page_obj': page_obj,
        'title': _('Alumni Achievements'),
    })
