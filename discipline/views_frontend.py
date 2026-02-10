from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from accounts.decorators import prefet_allowed, tenant_required
from django_ratelimit.decorators import ratelimit
from .models import DisciplinaryAction
from .forms import DisciplinaryActionForm


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='100/h')
def disciplinary_action_list(request):
    """List all disciplinary actions (direction only) with filtering."""
    actions = DisciplinaryAction.objects.filter(
        tenant=request.tenant
    ).select_related('student', 'reported_by').order_by('-incident_date')

    # Filter by severity
    severity = request.GET.get('severity', '').strip()
    if severity:
        actions = actions.filter(severity=severity)

    # Search by student name
    search = request.GET.get('search', '').strip()
    if search:
        actions = actions.filter(
            Q(student__first_name__icontains=search)
            | Q(student__last_name__icontains=search)
        )

    # Filter by resolved status
    resolved = request.GET.get('resolved', '').strip().lower()
    if resolved == 'true':
        actions = actions.filter(is_resolved=True)
    elif resolved == 'false':
        actions = actions.filter(is_resolved=False)

    # Pagination
    paginator = Paginator(actions, 25)
    page = request.GET.get('page')
    actions = paginator.get_page(page)

    return render(request, 'discipline/action_list.html', {
        'actions': actions,
        'severity_choices': DisciplinaryAction.SEVERITY_CHOICES,
        'current_severity': severity,
        'current_search': search,
        'current_resolved': resolved,
        'title': _('Disciplinary Actions'),
    })


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def disciplinary_action_create(request):
    """Create a new disciplinary action (direction only)."""
    from .forms import DisciplinaryActionForm

    if request.method == 'POST':
        form = DisciplinaryActionForm(request.POST)
        if form.is_valid():
            action = form.save(commit=False)
            action.tenant = request.tenant
            action.reported_by = request.user
            action.save()
            messages.success(request, _('Disciplinary action created successfully.'))
            return redirect('frontend:discipline:action_list')
    else:
        form = DisciplinaryActionForm()

    return render(request, 'discipline/action_form.html', {
        'form': form,
        'title': _('Create Disciplinary Action')
    })


@login_required
@prefet_allowed
@tenant_required
def disciplinary_action_detail(request, pk):
    """View disciplinary action details."""
    action = get_object_or_404(DisciplinaryAction, pk=pk, tenant=request.tenant)

    return render(request, 'discipline/action_detail.html', {
        'action': action,
        'title': _('Disciplinary Action Details')
    })


@login_required
@prefet_allowed
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def disciplinary_action_edit(request, pk):
    """Edit an existing disciplinary action (direction only)."""
    action = get_object_or_404(DisciplinaryAction, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        form = DisciplinaryActionForm(request.POST, instance=action)
        if form.is_valid():
            updated_action = form.save(commit=False)
            updated_action.updated_by = request.user
            updated_action.save()
            messages.success(request, _('Disciplinary action updated successfully.'))
            return redirect('frontend:discipline:action_detail', pk=action.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = DisciplinaryActionForm(instance=action)

    return render(request, 'discipline/action_form.html', {
        'form': form,
        'action': action,
        'title': _('Edit Disciplinary Action'),
    })


@login_required
@prefet_allowed
@tenant_required
def disciplinary_action_delete(request, pk):
    """Delete a disciplinary action (direction only). GET shows confirm, POST deletes."""
    action = get_object_or_404(DisciplinaryAction, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        action.delete()
        messages.success(request, _('Disciplinary action deleted successfully.'))
        return redirect('frontend:discipline:action_list')

    return render(request, 'discipline/action_confirm_delete.html', {
        'action': action,
        'title': _('Delete Disciplinary Action'),
    })


@login_required
@prefet_allowed
@tenant_required
def disciplinary_action_resolve(request, pk):
    """Mark a disciplinary action as resolved (POST-only, direction only)."""
    action = get_object_or_404(DisciplinaryAction, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        action.is_resolved = True
        action.resolution_date = timezone.now().date()
        action.updated_by = request.user
        action.save()
        messages.success(request, _('Disciplinary action marked as resolved.'))
        return redirect('frontend:discipline:action_detail', pk=action.pk)

    # If not POST, redirect back to detail
    return redirect('frontend:discipline:action_detail', pk=action.pk)
