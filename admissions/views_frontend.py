"""
Admissions Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Listing active admission sessions
- Public admission application submission
- Public application status lookup by email
- Staff-only application list with filtering and pagination
- Staff-only application detail with counseling comments
- Creating counseling comments on applications

Frontend URL namespace: frontend:admissions:view_name
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q

from accounts.decorators import direction_only

from .models import AdmissionSession, AdmissionStudent, CounselingComment
from .forms import AdmissionApplicationForm, CounselingCommentForm, AdmissionStatusForm


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

def admission_apply(request):
    """
    Public admission application form.

    GET: Display empty application form
    POST: Validate and save new application
    """
    if request.method == 'POST':
        form = AdmissionApplicationForm(request.POST)
        if form.is_valid():
            application = form.save()
            messages.success(
                request,
                _('Your application has been submitted successfully. '
                  'You can check your status using your email address.')
            )
            return redirect('frontend:admissions:check_status')
    else:
        form = AdmissionApplicationForm()
        # Only show active sessions in the dropdown
        form.fields['session'].queryset = AdmissionSession.objects.filter(is_active=True)

    context = {
        'form': form,
        'page_title': _('Apply for Admission'),
    }

    return render(request, 'admissions/apply.html', context)


def admission_status(request):
    """
    Public application status check.

    GET: Display email lookup form
    POST: Look up applications by email and display results
    """
    applications = None

    if request.method == 'POST':
        form = AdmissionStatusForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            applications = AdmissionStudent.objects.filter(
                email=email
            ).select_related('session').order_by('-created_at')

            if not applications.exists():
                messages.info(
                    request,
                    _('No applications found for this email address.')
                )
    else:
        form = AdmissionStatusForm()

    context = {
        'form': form,
        'applications': applications,
        'page_title': _('Check Application Status'),
    }

    return render(request, 'admissions/status.html', context)


# ============================================================================
# AUTHENTICATED VIEWS
# ============================================================================

@login_required
def admission_session_list(request):
    """
    List active admission sessions.

    Displays all active admission sessions for logged-in users.
    """
    sessions = AdmissionSession.objects.filter(
        is_active=True
    ).order_by('-start_date')

    context = {
        'sessions': sessions,
        'page_title': _('Admission Sessions'),
    }

    return render(request, 'admissions/session_list.html', context)


# ============================================================================
# DIRECTION-ONLY VIEWS
# ============================================================================

@direction_only
def admission_list(request):
    """
    Paginated list of all admission applications (direction only).

    Features:
    - Filter by status
    - Search by name or email
    - Pagination (20 items per page)
    """
    status_filter = request.GET.get('status', '').strip()
    search = request.GET.get('search', '').strip()
    page_num = request.GET.get('page', 1)

    applications = AdmissionStudent.objects.select_related(
        'session', 'program', 'reviewed_by', 'counselor'
    ).order_by('-created_at')

    # Apply status filter
    if status_filter:
        applications = applications.filter(status=status_filter)

    # Apply search filter
    if search:
        applications = applications.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    # Pagination
    paginator = Paginator(applications, 20)
    applications_page = paginator.get_page(page_num)

    context = {
        'applications': applications_page,
        'total_count': paginator.count,
        'status_filter': status_filter,
        'search': search,
        'status_choices': AdmissionStudent.STATUS_CHOICES,
        'page_title': _('All Applications'),
    }

    return render(request, 'admissions/admission_list.html', context)


@direction_only
def admission_detail(request, pk):
    """
    Detailed view of a single admission application (direction only).

    Includes:
    - Full application information
    - Counseling comments history
    - Payment details (if any)
    """
    application = get_object_or_404(
        AdmissionStudent.objects.select_related(
            'session', 'program', 'reviewed_by', 'counselor'
        ),
        pk=pk
    )

    comments = application.counseling_comments.select_related(
        'counselor'
    ).order_by('-created_at')

    # Check for payment
    payment = None
    try:
        payment = application.payment
    except AdmissionStudent.payment.RelatedObjectDoesNotExist:
        pass

    context = {
        'application': application,
        'comments': comments,
        'payment': payment,
        'page_title': _('Application: %(name)s') % {
            'name': application.get_full_name()
        },
    }

    return render(request, 'admissions/admission_detail.html', context)


@direction_only
def counseling_comment_create(request, student_id):
    """
    Create a counseling comment on an application (direction only).

    GET: Display comment form
    POST: Validate and save comment with counselor set to request.user
    """
    application = get_object_or_404(AdmissionStudent, pk=student_id)

    if request.method == 'POST':
        form = CounselingCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.application = application
            comment.counselor = request.user
            comment.save()

            messages.success(request, _('Counseling comment added successfully.'))
            return redirect('frontend:admissions:admission_detail', pk=application.pk)
    else:
        form = CounselingCommentForm()

    context = {
        'form': form,
        'application': application,
        'page_title': _('Add Counseling Comment'),
    }

    return render(request, 'admissions/counseling_form.html', context)
