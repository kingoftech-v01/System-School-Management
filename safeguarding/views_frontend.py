from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit

from accounts.decorators import direction_only, prefet_allowed

from .forms import (
    IncidentForm,
    StudentCaseNoteForm,
    VisitorCheckoutForm,
    VisitorLogForm,
)
from .models import Incident, IncidentAttachment, StudentCaseNote, VisitorLog


# ---- Incident Views ----

@login_required
@prefet_allowed
@ratelimit(key='user', rate='100/h')
def incident_list(request):
    incidents = Incident.objects.select_related('reported_by').order_by(
        '-incident_date'
    )
    tenant = getattr(request, 'tenant', None)
    if tenant:
        incidents = incidents.filter(tenant=tenant)

    incident_type = request.GET.get('type', '').strip()
    if incident_type:
        incidents = incidents.filter(incident_type=incident_type)

    severity = request.GET.get('severity', '').strip()
    if severity:
        incidents = incidents.filter(severity=severity)

    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        incidents = incidents.filter(status=status_filter)

    search = request.GET.get('search', '').strip()
    if search:
        incidents = incidents.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    total_count = incidents.count()
    open_count = incidents.filter(status='open').count()

    paginator = Paginator(incidents, 25)
    page = request.GET.get('page')
    incidents = paginator.get_page(page)

    return render(request, 'safeguarding/incident_list.html', {
        'incidents': incidents,
        'total_count': total_count,
        'open_count': open_count,
        'type_choices': Incident.INCIDENT_TYPE_CHOICES,
        'severity_choices': Incident.SEVERITY_CHOICES,
        'status_choices': Incident.STATUS_CHOICES,
        'current_type': incident_type,
        'current_severity': severity,
        'current_status': status_filter,
        'current_search': search,
        'title': _('Incident Log'),
    })


@login_required
@prefet_allowed
@ratelimit(key='user', rate='50/h', method='POST')
def incident_create(request):
    if request.method == 'POST':
        form = IncidentForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            tenant = getattr(request, 'tenant', None)
            if tenant:
                incident.tenant = tenant
            incident.reported_by = request.user
            incident.save()
            form.save_m2m()

            for f in request.FILES.getlist('attachments'):
                IncidentAttachment.objects.create(
                    incident=incident, file=f, uploaded_by=request.user
                )

            messages.success(request, _('Incident logged successfully.'))
            return redirect(
                'frontend:safeguarding:incident_detail', pk=incident.pk
            )
    else:
        form = IncidentForm()

    return render(request, 'safeguarding/incident_form.html', {
        'form': form,
        'title': _('Log New Incident'),
    })


@login_required
@prefet_allowed
def incident_detail(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    return render(request, 'safeguarding/incident_detail.html', {
        'incident': incident,
        'title': _('Incident Details'),
    })


@login_required
@prefet_allowed
@ratelimit(key='user', rate='50/h', method='POST')
def incident_edit(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    if request.method == 'POST':
        form = IncidentForm(request.POST, request.FILES, instance=incident)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.updated_by = request.user
            updated.save()
            form.save_m2m()
            messages.success(request, _('Incident updated successfully.'))
            return redirect(
                'frontend:safeguarding:incident_detail', pk=incident.pk
            )
    else:
        form = IncidentForm(instance=incident)

    return render(request, 'safeguarding/incident_form.html', {
        'form': form,
        'incident': incident,
        'title': _('Edit Incident'),
    })


# ---- Visitor Log Views ----

@login_required
@direction_only
@ratelimit(key='user', rate='100/h')
def visitor_list(request):
    visitors = VisitorLog.objects.select_related(
        'host_staff', 'logged_by'
    ).order_by('-time_in')
    tenant = getattr(request, 'tenant', None)
    if tenant:
        visitors = visitors.filter(tenant=tenant)

    visitor_type = request.GET.get('type', '').strip()
    if visitor_type:
        visitors = visitors.filter(visitor_type=visitor_type)

    on_site_only = request.GET.get('on_site', '').strip().lower()
    if on_site_only == 'true':
        visitors = visitors.filter(time_out__isnull=True)

    search = request.GET.get('search', '').strip()
    if search:
        visitors = visitors.filter(
            Q(visitor_name__icontains=search)
            | Q(organization__icontains=search)
        )

    on_site_count = VisitorLog.objects.filter(time_out__isnull=True).count()

    paginator = Paginator(visitors, 25)
    page = request.GET.get('page')
    visitors = paginator.get_page(page)

    return render(request, 'safeguarding/visitor_list.html', {
        'visitors': visitors,
        'on_site_count': on_site_count,
        'type_choices': VisitorLog.VISITOR_TYPE_CHOICES,
        'current_type': visitor_type,
        'current_search': search,
        'title': _('Visitor Log'),
    })


@login_required
@direction_only
@ratelimit(key='user', rate='50/h', method='POST')
def visitor_sign_in(request):
    if request.method == 'POST':
        form = VisitorLogForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            tenant = getattr(request, 'tenant', None)
            if tenant:
                visitor.tenant = tenant
            visitor.logged_by = request.user
            if not visitor.time_in:
                visitor.time_in = timezone.now()
            visitor.save()
            form.save_m2m()
            messages.success(request, _('Visitor signed in successfully.'))
            return redirect('frontend:safeguarding:visitor_list')
    else:
        form = VisitorLogForm(initial={'time_in': timezone.now()})

    return render(request, 'safeguarding/visitor_form.html', {
        'form': form,
        'title': _('Sign In Visitor'),
    })


@login_required
@direction_only
def visitor_detail(request, pk):
    visitor = get_object_or_404(VisitorLog, pk=pk)
    return render(request, 'safeguarding/visitor_detail.html', {
        'visitor': visitor,
        'title': _('Visitor Details'),
    })


@login_required
@direction_only
def visitor_sign_out(request, pk):
    visitor = get_object_or_404(VisitorLog, pk=pk)
    if request.method == 'POST':
        if visitor.time_out:
            messages.warning(request, _('Visitor already signed out.'))
        else:
            form = VisitorCheckoutForm(request.POST)
            if form.is_valid():
                visitor.time_out = timezone.now()
                notes = form.cleaned_data.get('notes', '')
                if notes:
                    existing = visitor.notes or ''
                    visitor.notes = (existing + '\n' + notes).strip()
                visitor.save(
                    update_fields=['time_out', 'notes', 'updated_at']
                )
                messages.success(request, _('Visitor signed out.'))
    return redirect('frontend:safeguarding:visitor_detail', pk=visitor.pk)


# ---- Case Note Views ----

@login_required
@direction_only
@ratelimit(key='user', rate='100/h')
def case_note_list(request):
    notes = StudentCaseNote.objects.select_related(
        'student__student', 'created_by'
    )
    tenant = getattr(request, 'tenant', None)
    if tenant:
        notes = notes.filter(tenant=tenant)

    user = request.user
    if not (
        user.has_perm('safeguarding.view_highly_restricted_notes')
        or user.is_superuser
    ):
        if user.has_perm('safeguarding.view_restricted_notes'):
            notes = notes.exclude(confidentiality='highly_restricted')
        else:
            notes = notes.filter(confidentiality='standard')

    category = request.GET.get('category', '').strip()
    if category:
        notes = notes.filter(category=category)

    student_id = request.GET.get('student', '').strip()
    if student_id:
        notes = notes.filter(student_id=student_id)

    paginator = Paginator(notes, 25)
    page = request.GET.get('page')
    notes = paginator.get_page(page)

    return render(request, 'safeguarding/case_note_list.html', {
        'notes': notes,
        'category_choices': StudentCaseNote.CATEGORY_CHOICES,
        'current_category': category,
        'title': _('Student Case Notes'),
    })


@login_required
@direction_only
@ratelimit(key='user', rate='50/h', method='POST')
def case_note_create(request):
    if request.method == 'POST':
        form = StudentCaseNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            tenant = getattr(request, 'tenant', None)
            if tenant:
                note.tenant = tenant
            note.created_by = request.user
            note.save()
            messages.success(request, _('Case note created.'))
            return redirect(
                'frontend:safeguarding:case_note_detail', pk=note.pk
            )
    else:
        form = StudentCaseNoteForm()

    return render(request, 'safeguarding/case_note_form.html', {
        'form': form,
        'title': _('Create Case Note'),
    })


@login_required
@direction_only
def case_note_detail(request, pk):
    note = get_object_or_404(StudentCaseNote, pk=pk)

    user = request.user
    if note.confidentiality == 'highly_restricted':
        if not (
            user.has_perm('safeguarding.view_highly_restricted_notes')
            or user.is_superuser
        ):
            messages.error(
                request, _('You do not have permission to view this note.')
            )
            return redirect('frontend:safeguarding:case_note_list')
    elif note.confidentiality == 'restricted':
        if not (
            user.has_perm('safeguarding.view_restricted_notes')
            or user.is_superuser
        ):
            messages.error(
                request, _('You do not have permission to view this note.')
            )
            return redirect('frontend:safeguarding:case_note_list')

    return render(request, 'safeguarding/case_note_detail.html', {
        'note': note,
        'title': _('Case Note Details'),
    })
