from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from accounts.decorators import direction_only, professor_only, tenant_required
from django_ratelimit.decorators import ratelimit
from .models import DisciplinaryAction


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def disciplinary_action_list(request):
    """List all disciplinary actions (direction only)."""
    actions = DisciplinaryAction.objects.filter(
        tenant=request.tenant
    ).select_related('student', 'reported_by').order_by('-incident_date')

    return render(request, 'discipline/action_list.html', {
        'actions': actions,
        'title': _('Disciplinary Actions')
    })


@login_required
@direction_only
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
            return redirect('discipline:action_list')
    else:
        form = DisciplinaryActionForm()

    return render(request, 'discipline/action_form.html', {
        'form': form,
        'title': _('Create Disciplinary Action')
    })


@login_required
@direction_only
@tenant_required
def disciplinary_action_detail(request, pk):
    """View disciplinary action details."""
    action = get_object_or_404(DisciplinaryAction, pk=pk, tenant=request.tenant)

    return render(request, 'discipline/action_detail.html', {
        'action': action,
        'title': _('Disciplinary Action Details')
    })
