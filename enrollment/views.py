"""
Views for student enrollment and registration management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from accounts.decorators import direction_only, tenant_required, role_required
from .models import RegistrationForm, EnrollmentDocument, EnrollmentStatusHistory
from .forms import (
    RegistrationFormStep1, RegistrationFormStep2, RegistrationFormStep3,
    RegistrationFormStep4, DocumentUploadForm, RegistrationReviewForm,
    EnrollmentSearchForm, DocumentVerificationForm
)
from .tasks import send_enrollment_status_email
import csv
from datetime import datetime


# ########################################################
# Public Registration Views (No Authentication Required)
# ########################################################

@ratelimit(key='ip', rate='10/h', method='POST')
def register_step1(request):
    """Step 1 of student registration (public)."""
    if request.method == 'POST':
        form = RegistrationFormStep1(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            # Tenant will be set based on domain
            if hasattr(request, 'tenant'):
                registration.tenant = request.tenant
            registration.save()

            # Store registration ID in session
            request.session['registration_id'] = registration.id
            messages.success(request, _('Step 1 completed. Please provide parent information.'))
            return redirect('enrollment:register_step2')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = RegistrationFormStep1()

    return render(request, 'enrollment/register_step1.html', {
        'form': form,
        'step': 1,
        'title': _('Student Registration - Step 1')
    })


@ratelimit(key='ip', rate='10/h', method='POST')
def register_step2(request):
    """Step 2 of student registration (public)."""
    registration_id = request.session.get('registration_id')
    if not registration_id:
        messages.error(request, _('Please start from step 1.'))
        return redirect('enrollment:register_step1')

    registration = get_object_or_404(RegistrationForm, id=registration_id)

    if request.method == 'POST':
        form = RegistrationFormStep2(request.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(request, _('Step 2 completed. Please provide academic information.'))
            return redirect('enrollment:register_step3')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = RegistrationFormStep2(instance=registration)

    return render(request, 'enrollment/register_step2.html', {
        'form': form,
        'step': 2,
        'registration': registration,
        'title': _('Student Registration - Step 2')
    })


@ratelimit(key='ip', rate='10/h', method='POST')
def register_step3(request):
    """Step 3 of student registration (public)."""
    registration_id = request.session.get('registration_id')
    if not registration_id:
        messages.error(request, _('Please start from step 1.'))
        return redirect('enrollment:register_step1')

    registration = get_object_or_404(RegistrationForm, id=registration_id)
    tenant = registration.tenant if registration.tenant else getattr(request, 'tenant', None)

    if request.method == 'POST':
        form = RegistrationFormStep3(request.POST, instance=registration, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _('Step 3 completed. Please provide additional information.'))
            return redirect('enrollment:register_step4')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = RegistrationFormStep3(instance=registration, tenant=tenant)

    return render(request, 'enrollment/register_step3.html', {
        'form': form,
        'step': 3,
        'registration': registration,
        'title': _('Student Registration - Step 3')
    })


@ratelimit(key='ip', rate='10/h', method='POST')
def register_step4(request):
    """Step 4 of student registration (public) - Final step."""
    registration_id = request.session.get('registration_id')
    if not registration_id:
        messages.error(request, _('Please start from step 1.'))
        return redirect('enrollment:register_step1')

    registration = get_object_or_404(RegistrationForm, id=registration_id)

    if request.method == 'POST':
        form = RegistrationFormStep4(request.POST, instance=registration)
        if form.is_valid():
            form.save()

            # Clear session
            del request.session['registration_id']

            # Send notification email
            send_enrollment_status_email.delay(
                registration.id,
                'submitted'
            )

            messages.success(request, _(
                'Registration submitted successfully! '
                'You will receive an email confirmation shortly. '
                'Our admissions team will review your application.'
            ))
            return redirect('enrollment:register_complete', registration_id=registration.id)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = RegistrationFormStep4(instance=registration)

    return render(request, 'enrollment/register_step4.html', {
        'form': form,
        'step': 4,
        'registration': registration,
        'title': _('Student Registration - Step 4')
    })


def register_complete(request, registration_id):
    """Registration completion page."""
    registration = get_object_or_404(RegistrationForm, id=registration_id)

    return render(request, 'enrollment/register_complete.html', {
        'registration': registration,
        'title': _('Registration Complete')
    })


@ratelimit(key='ip', rate='20/h', method='POST')
def upload_document(request, registration_id):
    """Upload enrollment documents (public or authenticated)."""
    registration = get_object_or_404(RegistrationForm, id=registration_id)

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.registration = registration
            document.save()
            messages.success(request, _('Document uploaded successfully.'))
            return redirect('enrollment:upload_document', registration_id=registration_id)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = DocumentUploadForm()

    documents = EnrollmentDocument.objects.filter(registration=registration).order_by('-uploaded_at')

    return render(request, 'enrollment/upload_document.html', {
        'form': form,
        'registration': registration,
        'documents': documents,
        'title': _('Upload Documents')
    })


# ########################################################
# Direction/Admin Views (Authentication Required)
# ########################################################

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def enrollment_list(request):
    """List all enrollment applications with filtering."""
    form = EnrollmentSearchForm(request.GET, tenant=request.tenant)
    registrations = RegistrationForm.objects.filter(tenant=request.tenant).order_by('-submitted_at')

    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('student_name'):
            registrations = registrations.filter(
                student_name__icontains=form.cleaned_data['student_name']
            )
        if form.cleaned_data.get('email'):
            registrations = registrations.filter(
                Q(email__icontains=form.cleaned_data['email']) |
                Q(parent_email__icontains=form.cleaned_data['email'])
            )
        if form.cleaned_data.get('status'):
            registrations = registrations.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('enrollment_type'):
            registrations = registrations.filter(enrollment_type=form.cleaned_data['enrollment_type'])
        if form.cleaned_data.get('academic_year'):
            registrations = registrations.filter(academic_year=form.cleaned_data['academic_year'])
        if form.cleaned_data.get('filiere'):
            registrations = registrations.filter(filiere=form.cleaned_data['filiere'])
        if form.cleaned_data.get('date_from'):
            registrations = registrations.filter(submitted_at__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            registrations = registrations.filter(submitted_at__lte=form.cleaned_data['date_to'])

    # Statistics
    stats = {
        'total': registrations.count(),
        'pending': registrations.filter(status='pending').count(),
        'approved': registrations.filter(status='approved').count(),
        'rejected': registrations.filter(status='rejected').count(),
        'enrolled': registrations.filter(status='enrolled').count(),
    }

    # Pagination
    paginator = Paginator(registrations, 50)
    page = request.GET.get('page')
    try:
        registrations = paginator.page(page)
    except PageNotAnInteger:
        registrations = paginator.page(1)
    except EmptyPage:
        registrations = paginator.page(paginator.num_pages)

    return render(request, 'enrollment/enrollment_list.html', {
        'registrations': registrations,
        'form': form,
        'stats': stats,
        'title': _('Enrollment Applications')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def enrollment_detail(request, registration_id):
    """View detailed information about a registration."""
    registration = get_object_or_404(
        RegistrationForm,
        id=registration_id,
        tenant=request.tenant
    )

    documents = EnrollmentDocument.objects.filter(registration=registration).order_by('-uploaded_at')
    history = EnrollmentStatusHistory.objects.filter(registration=registration).order_by('-changed_at')

    return render(request, 'enrollment/enrollment_detail.html', {
        'registration': registration,
        'documents': documents,
        'history': history,
        'title': f'{registration.student_name} - Registration Detail'
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def enrollment_review(request, registration_id):
    """Review and approve/reject a registration."""
    registration = get_object_or_404(
        RegistrationForm,
        id=registration_id,
        tenant=request.tenant
    )

    if request.method == 'POST':
        form = RegistrationReviewForm(request.POST, instance=registration)
        if form.is_valid():
            old_status = registration.status
            registration = form.save(commit=False)
            registration.reviewed_by = request.user
            registration.reviewed_at = timezone.now()
            registration.save()

            # Create status history
            EnrollmentStatusHistory.objects.create(
                registration=registration,
                old_status=old_status,
                new_status=registration.status,
                changed_by=request.user,
                notes=registration.review_notes
            )

            # Send notification email
            send_enrollment_status_email.delay(
                registration.id,
                registration.status
            )

            messages.success(request, _(f'Registration {registration.get_status_display().lower()} successfully.'))
            return redirect('enrollment:enrollment_detail', registration_id=registration.id)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = RegistrationReviewForm(instance=registration)

    return render(request, 'enrollment/enrollment_review.html', {
        'form': form,
        'registration': registration,
        'title': _('Review Registration')
    })


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def verify_document(request, document_id):
    """Verify an uploaded document."""
    document = get_object_or_404(
        EnrollmentDocument,
        id=document_id,
        registration__tenant=request.tenant
    )

    if request.method == 'POST':
        form = DocumentVerificationForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
            document.verified_by = request.user
            document.save()
            messages.success(request, _('Document verification status updated.'))
            return redirect('enrollment:enrollment_detail', registration_id=document.registration.id)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='20/h')
def export_enrollments_csv(request):
    """Export enrollment data to CSV."""
    registrations = RegistrationForm.objects.filter(tenant=request.tenant).order_by('-submitted_at')

    # Apply filters from GET parameters
    form = EnrollmentSearchForm(request.GET, tenant=request.tenant)
    if form.is_valid():
        # Apply same filters as enrollment_list
        if form.cleaned_data.get('student_name'):
            registrations = registrations.filter(student_name__icontains=form.cleaned_data['student_name'])
        if form.cleaned_data.get('status'):
            registrations = registrations.filter(status=form.cleaned_data['status'])
        # ... (apply other filters)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="enrollments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 'Email', 'Phone', 'Gender', 'Date of Birth',
        'Parent Name', 'Parent Email', 'Parent Phone',
        'Filiere', 'Academic Year', 'Level', 'Enrollment Type',
        'Status', 'Submitted At', 'Reviewed By', 'Reviewed At'
    ])

    for reg in registrations:
        writer.writerow([
            reg.student_name,
            reg.email,
            reg.phone,
            reg.get_gender_display(),
            reg.date_of_birth,
            reg.parent_name,
            reg.parent_email,
            reg.parent_phone,
            reg.filiere.name if reg.filiere else '',
            reg.academic_year,
            reg.get_level_display(),
            reg.get_enrollment_type_display(),
            reg.get_status_display(),
            reg.submitted_at.strftime('%Y-%m-%d %H:%M'),
            reg.reviewed_by.get_full_name if reg.reviewed_by else '',
            reg.reviewed_at.strftime('%Y-%m-%d %H:%M') if reg.reviewed_at else ''
        ])

    return response


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h')
def enrollment_statistics(request):
    """Display enrollment statistics and analytics."""
    registrations = RegistrationForm.objects.filter(tenant=request.tenant)

    # Overall statistics
    total = registrations.count()
    by_status = registrations.values('status').annotate(count=Count('id'))
    by_type = registrations.values('enrollment_type').annotate(count=Count('id'))
    by_filiere = registrations.values('filiere__name').annotate(count=Count('id'))
    by_level = registrations.values('level').annotate(count=Count('id'))
    by_gender = registrations.values('gender').annotate(count=Count('id'))

    # Monthly trend (last 12 months)
    from datetime import timedelta
    from django.db.models.functions import TruncMonth
    twelve_months_ago = timezone.now() - timedelta(days=365)
    monthly_trend = registrations.filter(
        submitted_at__gte=twelve_months_ago
    ).annotate(
        month=TruncMonth('submitted_at')
    ).values('month').annotate(count=Count('id')).order_by('month')

    context = {
        'total': total,
        'by_status': by_status,
        'by_type': by_type,
        'by_filiere': by_filiere,
        'by_level': by_level,
        'by_gender': by_gender,
        'monthly_trend': monthly_trend,
        'title': _('Enrollment Statistics')
    }

    return render(request, 'enrollment/enrollment_statistics.html', context)
