from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import professor_only, direction_only, tenant_required
from django_ratelimit.decorators import ratelimit
from .models import ProfessorNote, NoteHistory, NoteComment
from .forms import ProfessorNoteForm, NoteApprovalForm, NoteCommentForm


@login_required
@professor_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def note_list(request):
    """List professor's notes with pagination, status and student filters."""
    notes = ProfessorNote.objects.filter(
        professor=request.user,
        tenant=request.tenant,
        is_deleted=False
    ).select_related('student', 'subject').order_by('-created_at')

    # Filter by status
    status = request.GET.get('status', '').strip()
    if status:
        notes = notes.filter(status=status)

    # Filter by student name
    student_search = request.GET.get('student', '').strip()
    if student_search:
        notes = notes.filter(
            Q(student__first_name__icontains=student_search) |
            Q(student__last_name__icontains=student_search)
        )

    # Pagination
    paginator = Paginator(notes, 20)
    page_num = request.GET.get('page', 1)
    notes_page = paginator.get_page(page_num)

    return render(request, 'notes/note_list.html', {
        'notes': notes_page,
        'total_count': paginator.count,
        'status': status,
        'student_search': student_search,
        'status_choices': ProfessorNote.STATUS_CHOICES,
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

            # Auto-populate filiere from the selected subject/course
            if not note.filiere_id:
                from filieres.models import FiliereSubject, Filiere
                filiere_subject = FiliereSubject.objects.filter(
                    subject=note.subject
                ).select_related('filiere').first()
                if filiere_subject:
                    note.filiere = filiere_subject.filiere
                else:
                    # Fallback: use first filiere for the tenant
                    note.filiere = Filiere.objects.filter(
                        tenant=request.tenant
                    ).first()

            # Auto-populate session and semester if not set
            if not note.session_id:
                from core.models import Session
                note.session = Session.objects.filter(
                    is_current_session=True
                ).first()
            if not note.semester_id:
                from core.models import Semester
                note.semester = Semester.objects.filter(
                    is_current_semester=True
                ).first()

            note.save()

            # Create history record
            NoteHistory.objects.create(
                note=note,
                action='created',
                changed_by=request.user,
                new_values={'score': str(note.score), 'comment': note.comment}
            )

            messages.success(request, _('Note created successfully.'))
            return redirect('frontend:notes:note_list')
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
        return redirect('frontend:notes:note_detail', pk=pk)

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
            return redirect('frontend:notes:note_detail', pk=pk)
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
        return redirect('frontend:notes:note_detail', pk=pk)

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
        return redirect('frontend:notes:note_list')

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
            return redirect('frontend:notes:notes_pending')
    else:
        form = NoteApprovalForm(instance=note)

    return render(request, 'notes/note_approve.html', {
        'form': form,
        'note': note,
        'title': _('Review Note')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def note_list_all(request):
    """List ALL professors' notes (direction view) with status and student filters, pagination."""
    notes = ProfessorNote.objects.filter(
        tenant=request.tenant,
        is_deleted=False
    ).select_related('student', 'professor', 'subject', 'filiere').order_by('-created_at')

    # Filter by status
    status = request.GET.get('status', '').strip()
    if status:
        notes = notes.filter(status=status)

    # Filter by student name
    student_search = request.GET.get('student', '').strip()
    if student_search:
        notes = notes.filter(
            Q(student__first_name__icontains=student_search) |
            Q(student__last_name__icontains=student_search)
        )

    # Filter by professor name
    professor_search = request.GET.get('professor', '').strip()
    if professor_search:
        notes = notes.filter(
            Q(professor__first_name__icontains=professor_search) |
            Q(professor__last_name__icontains=professor_search)
        )

    # Pagination
    paginator = Paginator(notes, 20)
    page_num = request.GET.get('page', 1)
    notes_page = paginator.get_page(page_num)

    return render(request, 'notes/note_list_all.html', {
        'notes': notes_page,
        'total_count': paginator.count,
        'status': status,
        'student_search': student_search,
        'professor_search': professor_search,
        'status_choices': ProfessorNote.STATUS_CHOICES,
        'title': _('All Professor Notes')
    })


@login_required
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def note_comment_create(request, pk):
    """Add a comment to a professor note (for communication during approval)."""
    note = get_object_or_404(
        ProfessorNote,
        pk=pk,
        tenant=request.tenant,
        is_deleted=False
    )

    # Only the professor who owns the note or direction staff can comment
    if note.professor != request.user and not (
        request.user.is_superuser or getattr(request.user, 'role', '') in ('direction', 'admin')
    ):
        messages.error(request, _('You do not have permission to comment on this note.'))
        return redirect('frontend:notes:note_detail', pk=pk)

    if request.method == 'POST':
        form = NoteCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.note = note
            comment.author = request.user
            comment.save()
            messages.success(request, _('Comment added successfully.'))
            return redirect('frontend:notes:note_detail', pk=pk)
    else:
        form = NoteCommentForm()

    return render(request, 'notes/note_comment_form.html', {
        'form': form,
        'note': note,
        'title': _('Add Comment')
    })
