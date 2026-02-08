"""
Notices Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Viewing and creating notices/announcements
- Filtering notices by priority and date
- Responding to notices with acknowledgment

All views render HTML templates.
Frontend URL namespace: frontend:notices:view_name
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import direction_only, tenant_required
from django_ratelimit.decorators import ratelimit

from .models import Notice, NotifyGroup, NoticeResponse, NoticeDocument
from .forms import NoticeForm


# ============================================================================
# LIST VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def notice_list(request):
    """
    List all notices with filtering and pagination.

    Features:
    - Filter by priority
    - Search by title/content
    - Pagination (20 items per page)
    - Hide expired notices by default, support ?show_expired=true toggle
    """
    # Get query parameters
    search = request.GET.get('search', '').strip()
    priority = request.GET.get('priority')
    show_expired = request.GET.get('show_expired', '').lower() == 'true'
    page_num = request.GET.get('page', 1)

    # Base queryset
    notices = Notice.objects.filter(
        tenant=request.tenant
    ).select_related('uploaded_by').order_by('-created_at')

    # Hide expired notices by default
    if not show_expired:
        from django.utils import timezone as tz
        today = tz.now().date()
        notices = notices.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=today)
        )

    # Apply search
    if search:
        notices = notices.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )

    # Apply priority filter
    if priority:
        notices = notices.filter(priority=priority)

    # Pagination
    paginator = Paginator(notices, 20)
    notices_page = paginator.get_page(page_num)

    context = {
        'notices': notices_page,
        'total_count': paginator.count,
        'search': search,
        'priority': priority,
        'show_expired': show_expired,
        'page_title': _('Notices & Announcements'),
        'meta_description': _('View all school notices and announcements'),
    }

    return render(request, 'notices/notice_list.html', context)


# ============================================================================
# DETAIL VIEWS
# ============================================================================

@login_required
@tenant_required
def notice_detail(request, pk):
    """
    Display detailed information for a single notice.

    Includes:
    - Full notice content
    - Attachments (if any)
    - Posted by and date information
    - Acknowledgment count/percentage and list of acknowledging users (direction only)
    """
    notice = get_object_or_404(
        Notice.objects.select_related('uploaded_by'),
        pk=pk,
        tenant=request.tenant
    )

    # Get attachments
    documents = notice.documents.all()

    # Acknowledgment tracking
    total_responses = NoticeResponse.objects.filter(notice=notice).count()
    acknowledged_responses = NoticeResponse.objects.filter(notice=notice, acknowledged=True)
    acknowledged_count = acknowledged_responses.count()
    acknowledgment_percentage = 0
    acknowledged_users = []

    if total_responses > 0:
        acknowledgment_percentage = round((acknowledged_count / total_responses) * 100, 1)

    # Direction users can see who acknowledged
    user_role = getattr(request.user, 'role', '')
    is_direction = user_role in ('direction', 'admin') or request.user.is_superuser
    if is_direction:
        acknowledged_users = acknowledged_responses.select_related('user').order_by('-acknowledged_at')

    # Check if current user has acknowledged
    user_response = NoticeResponse.objects.filter(notice=notice, user=request.user).first()
    user_acknowledged = user_response.acknowledged if user_response else False

    context = {
        'notice': notice,
        'documents': documents,
        'total_responses': total_responses,
        'acknowledged_count': acknowledged_count,
        'acknowledgment_percentage': acknowledgment_percentage,
        'acknowledged_users': acknowledged_users,
        'is_direction': is_direction,
        'user_acknowledged': user_acknowledged,
        'page_title': notice.title,
        'meta_description': notice.content[:160] if len(notice.content) > 160 else notice.content,
    }

    return render(request, 'notices/notice_detail.html', context)


# ============================================================================
# CREATE/UPDATE VIEWS
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def notice_create(request):
    """
    Create a new notice (direction only).

    GET: Display empty form
    POST: Validate and save new notice, handle file attachments
    """
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.tenant = request.tenant
            notice.uploaded_by = request.user
            notice.save()
            form.save_m2m()  # Save many-to-many relationships

            # Handle file attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                NoticeDocument.objects.create(
                    notice=notice,
                    file=f,
                    filename=f.name,
                    file_size=f.size,
                )

            messages.success(request, _('Notice created successfully'))
            return redirect('frontend:notices:notice_detail', pk=notice.pk)
    else:
        form = NoticeForm()

    context = {
        'form': form,
        'form_title': _('Create Notice'),
        'submit_text': _('Create'),
        'cancel_url': 'frontend:notices:notice_list',
    }

    return render(request, 'notices/notice_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def notice_update(request, pk):
    """
    Update an existing notice (direction only).

    GET: Display pre-filled form
    POST: Validate and save changes, handle file attachments
    """
    notice = get_object_or_404(Notice, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            form.save()

            # Handle new file attachments
            files = request.FILES.getlist('attachments')
            for f in files:
                NoticeDocument.objects.create(
                    notice=notice,
                    file=f,
                    filename=f.name,
                    file_size=f.size,
                )

            # Handle attachment removals
            remove_ids = request.POST.getlist('remove_attachments')
            if remove_ids:
                NoticeDocument.objects.filter(
                    id__in=remove_ids, notice=notice
                ).delete()

            messages.success(request, _('Notice updated successfully'))
            return redirect('frontend:notices:notice_detail', pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)

    # Get existing documents for the form
    existing_documents = notice.documents.all()

    context = {
        'form': form,
        'notice': notice,
        'existing_documents': existing_documents,
        'form_title': _('Edit Notice'),
        'submit_text': _('Save Changes'),
        'cancel_url': 'frontend:notices:notice_detail',
    }

    return render(request, 'notices/notice_form.html', context)


# ============================================================================
# DELETE VIEWS
# ============================================================================

@login_required
@direction_only
@tenant_required
def notice_delete(request, pk):
    """
    Delete a notice (direction only).

    GET: Display confirmation page
    POST: Delete notice and redirect
    """
    notice = get_object_or_404(Notice, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        notice_title = notice.title
        notice.delete()
        messages.success(request, _('Notice "%(title)s" deleted successfully') % {'title': notice_title})
        return redirect('frontend:notices:notice_list')

    context = {
        'notice': notice,
        'page_title': _('Delete Notice'),
    }

    return render(request, 'notices/notice_confirm_delete.html', context)


# ============================================================================
# CUSTOM ACTION VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def notice_respond(request, pk):
    """
    Acknowledge/respond to a notice.

    POST only: Mark notice as read/acknowledged by user
    """
    notice = get_object_or_404(Notice, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        from django.utils import timezone as tz
        response_obj, created = NoticeResponse.objects.get_or_create(
            notice=notice,
            user=request.user,
            defaults={'acknowledged': True, 'acknowledged_at': tz.now()}
        )
        if not created and not response_obj.acknowledged:
            response_obj.acknowledged = True
            response_obj.acknowledged_at = tz.now()
            response_obj.save()
        messages.success(request, _('Notice acknowledged'))

    return redirect('frontend:notices:notice_detail', pk=notice.pk)
