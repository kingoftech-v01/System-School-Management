from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from accounts.decorators import professor_only, direction_only, tenant_required
from django_ratelimit.decorators import ratelimit
from .models import ProfessorNote, NoteHistory
from .forms import ProfessorNoteForm, NoteApprovalForm


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def note_list(request):
    """List professor's notes."""
    notes = ProfessorNote.objects.filter(
        professor=request.user,
        tenant=request.tenant,
        is_deleted=False
    ).select_related('student', 'subject').order_by('-created_at')

    return render(request, 'notes/note_list.html', {
        'notes': notes,
        'title': _('My Notes')
    })


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def note_create(request):
    """Create a new professor note."""
    if request.method == 'POST':
        form = ProfessorNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.professor = request.user
            note.tenant = request.tenant
            note.save()

            # Create history record
            NoteHistory.objects.create(
                note=note,
                action='created',
                changed_by=request.user,
                new_values={'score': str(note.score), 'comment': note.comment}
            )

            messages.success(request, _('Note created successfully.'))
            return redirect('notes:note_list')
    else:
        form = ProfessorNoteForm()

    return render(request, 'notes/note_form.html', {
        'form': form,
        'title': _('Create Note')
    })


@login_required
@professor_only
@tenant_required
def note_detail(request, pk):
    """View note details."""
    note = get_object_or_404(
        ProfessorNote,
        pk=pk,
        professor=request.user,
        tenant=request.tenant,
        is_deleted=False
    )

    history = NoteHistory.objects.filter(note=note).order_by('-changed_at')

    return render(request, 'notes/note_detail.html', {
        'note': note,
        'history': history,
        'title': _('Note Details')
    })


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def note_edit(request, pk):
    """Edit a note (only if not approved)."""
    note = get_object_or_404(
        ProfessorNote,
        pk=pk,
        professor=request.user,
        tenant=request.tenant,
        is_deleted=False
    )

    # Cannot edit approved notes
    if note.status == 'approved':
        messages.error(request, _('Cannot edit an approved note.'))
        return redirect('notes:note_detail', pk=pk)

    if request.method == 'POST':
        old_score = note.score
        old_comment = note.comment

        form = ProfessorNoteForm(request.POST, instance=note)
        if form.is_valid():
            note = form.save()

            # Create history record if score or comment changed
            if old_score != note.score or old_comment != note.comment:
                NoteHistory.objects.create(
                    note=note,
                    action='updated',
                    changed_by=request.user,
                    old_values={'score': str(old_score), 'comment': old_comment},
                    new_values={'score': str(note.score), 'comment': note.comment},
                    change_summary=f'Score changed from {old_score} to {note.score}'
                )

            messages.success(request, _('Note updated successfully.'))
            return redirect('notes:note_detail', pk=pk)
    else:
        form = ProfessorNoteForm(instance=note)

    return render(request, 'notes/note_form.html', {
        'form': form,
        'note': note,
        'title': _('Edit Note')
    })


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='20/h', method='POST')
def note_delete(request, pk):
    """Soft delete a note (only if not approved)."""
    note = get_object_or_404(
        ProfessorNote,
        pk=pk,
        professor=request.user,
        tenant=request.tenant,
        is_deleted=False
    )

    # Cannot delete approved notes
    if note.status == 'approved':
        messages.error(request, _('Cannot delete an approved note.'))
        return redirect('notes:note_detail', pk=pk)

    if request.method == 'POST':
        note.is_deleted = True
        note.save()

        NoteHistory.objects.create(
            note=note,
            action='deleted',
            changed_by=request.user,
            change_summary='Note marked as deleted'
        )

        messages.success(request, _('Note deleted successfully.'))
        return redirect('notes:note_list')

    return render(request, 'notes/note_confirm_delete.html', {
        'note': note,
        'title': _('Delete Note')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def notes_pending_approval(request):
    """List notes pending approval (direction only)."""
    notes = ProfessorNote.objects.filter(
        tenant=request.tenant,
        status='pending',
        is_deleted=False
    ).select_related('student', 'professor', 'subject').order_by('created_at')

    return render(request, 'notes/notes_pending.html', {
        'notes': notes,
        'title': _('Notes Pending Approval')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def note_approve(request, pk):
    """Approve, reject, or request revision for a note."""
    note = get_object_or_404(
        ProfessorNote,
        pk=pk,
        tenant=request.tenant,
        is_deleted=False
    )

    if request.method == 'POST':
        form = NoteApprovalForm(request.POST, instance=note)
        if form.is_valid():
            old_status = note.status

            note = form.save(commit=False)
            note.approved_by = request.user
            note.approved_at = timezone.now()
            note.save()

            # Create history record
            NoteHistory.objects.create(
                note=note,
                action='status_changed',
                changed_by=request.user,
                old_values={'status': old_status},
                new_values={'status': note.status},
                change_summary=f'Status changed from {old_status} to {note.status}'
            )

            # Send notification via Celery
            from .tasks import notify_note_status_change
            notify_note_status_change.delay(note.id, note.status)

            messages.success(request, _('Note status updated successfully.'))
            return redirect('notes:notes_pending')
    else:
        form = NoteApprovalForm(instance=note)

    return render(request, 'notes/note_approve.html', {
        'form': form,
        'note': note,
        'title': _('Review Note')
    })
