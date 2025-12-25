"""
Views for filieres management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.translation import gettext_lazy as _
from django_ratelimit.decorators import ratelimit
from accounts.decorators import direction_only, tenant_required
from .models import Filiere, FiliereSubject, FiliereRequirement
from .forms import FiliereForm, FiliereSubjectForm, FiliereRequirementForm, FiliereSearchForm


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def filiere_list(request):
    """List all filieres with search and filter."""
    form = FiliereSearchForm(request.GET)
    filieres = Filiere.objects.filter(tenant=request.tenant).annotate(
        subject_count=Count('subjects'),
        enrolled_count=Count('registrations', filter=Q(registrations__status='enrolled'))
    )

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('search'):
            search = form.cleaned_data['search']
            filieres = filieres.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        if form.cleaned_data.get('level'):
            filieres = filieres.filter(level=form.cleaned_data['level'])
        if form.cleaned_data.get('is_active'):
            is_active = form.cleaned_data['is_active'] == 'true'
            filieres = filieres.filter(is_active=is_active)

    # Pagination
    paginator = Paginator(filieres, 20)
    page = request.GET.get('page')
    filieres = paginator.get_page(page)

    return render(request, 'filieres/filiere_list.html', {
        'filieres': filieres,
        'form': form,
        'title': _('Academic Programs')
    })


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def filiere_detail(request, pk):
    """View detailed information about a filiere."""
    filiere = get_object_or_404(
        Filiere.objects.prefetch_related('subjects__subject', 'requirements'),
        pk=pk,
        tenant=request.tenant
    )

    # Group subjects by year and semester
    subjects_by_year = {}
    for subject in filiere.subjects.all():
        key = (subject.year, subject.semester)
        if key not in subjects_by_year:
            subjects_by_year[key] = []
        subjects_by_year[key].append(subject)

    return render(request, 'filieres/filiere_detail.html', {
        'filiere': filiere,
        'subjects_by_year': subjects_by_year,
        'requirements': filiere.requirements.all(),
        'title': filiere.name
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def filiere_create(request):
    """Create a new filiere."""
    if request.method == 'POST':
        form = FiliereForm(request.POST, tenant=request.tenant)
        if form.is_valid():
            filiere = form.save(commit=False)
            filiere.tenant = request.tenant
            filiere.save()
            messages.success(request, _('Filiere created successfully.'))
            return redirect('filieres:filiere_detail', pk=filiere.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = FiliereForm(tenant=request.tenant)

    return render(request, 'filieres/filiere_form.html', {
        'form': form,
        'title': _('Create New Filiere')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def filiere_edit(request, pk):
    """Edit an existing filiere."""
    filiere = get_object_or_404(Filiere, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        form = FiliereForm(request.POST, instance=filiere, tenant=request.tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _('Filiere updated successfully.'))
            return redirect('filieres:filiere_detail', pk=filiere.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = FiliereForm(instance=filiere, tenant=request.tenant)

    return render(request, 'filieres/filiere_form.html', {
        'form': form,
        'filiere': filiere,
        'title': _('Edit Filiere')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def filiere_delete(request, pk):
    """Delete a filiere (with confirmation)."""
    filiere = get_object_or_404(Filiere, pk=pk, tenant=request.tenant)

    # Check if filiere has enrolled students
    if filiere.get_enrolled_students_count() > 0:
        messages.error(request, _('Cannot delete filiere with enrolled students. Mark as inactive instead.'))
        return redirect('filieres:filiere_detail', pk=filiere.pk)

    if request.method == 'POST':
        filiere.delete()
        messages.success(request, _('Filiere deleted successfully.'))
        return redirect('filieres:filiere_list')

    return render(request, 'filieres/filiere_confirm_delete.html', {
        'filiere': filiere,
        'title': _('Delete Filiere')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def add_subject(request, filiere_pk):
    """Add a subject to a filiere."""
    filiere = get_object_or_404(Filiere, pk=filiere_pk, tenant=request.tenant)

    if request.method == 'POST':
        form = FiliereSubjectForm(request.POST, filiere=filiere)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.filiere = filiere
            subject.save()
            messages.success(request, _('Subject added to filiere successfully.'))
            return redirect('filieres:filiere_detail', pk=filiere.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = FiliereSubjectForm(filiere=filiere)

    return render(request, 'filieres/subject_form.html', {
        'form': form,
        'filiere': filiere,
        'title': _('Add Subject to %(filiere)s') % {'filiere': filiere.name}
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def remove_subject(request, filiere_pk, subject_pk):
    """Remove a subject from a filiere."""
    filiere_subject = get_object_or_404(
        FiliereSubject,
        pk=subject_pk,
        filiere__pk=filiere_pk,
        filiere__tenant=request.tenant
    )

    if request.method == 'POST':
        filiere_subject.delete()
        messages.success(request, _('Subject removed from filiere.'))
        return redirect('filieres:filiere_detail', pk=filiere_pk)

    return render(request, 'filieres/subject_confirm_delete.html', {
        'filiere_subject': filiere_subject,
        'title': _('Remove Subject')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def add_requirement(request, filiere_pk):
    """Add a requirement to a filiere."""
    filiere = get_object_or_404(Filiere, pk=filiere_pk, tenant=request.tenant)

    if request.method == 'POST':
        form = FiliereRequirementForm(request.POST)
        if form.is_valid():
            requirement = form.save(commit=False)
            requirement.filiere = filiere
            requirement.save()
            messages.success(request, _('Requirement added successfully.'))
            return redirect('filieres:filiere_detail', pk=filiere.pk)
    else:
        form = FiliereRequirementForm()

    return render(request, 'filieres/requirement_form.html', {
        'form': form,
        'filiere': filiere,
        'title': _('Add Requirement')
    })
