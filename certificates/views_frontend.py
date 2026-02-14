"""
Certificates Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Certificate template management
- Certificate generation and issuance
- Certificate viewing and downloading
- Public certificate verification
- Batch certificate generation

All views render HTML templates.
Frontend URL namespace: frontend:certificates:view_name
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from accounts.decorators import registrar_only, lecturer_required, tenant_required

from .models import (
    CertificateTemplate, Certificate, CertificateVerification,
    BatchCertificateGeneration
)
from .forms import (
    CertificateTemplateForm, CertificateForm, CertificateVerificationForm,
    BatchCertificateGenerationForm
)


# ============================================================================
# CERTIFICATE TEMPLATE VIEWS
# ============================================================================

@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def template_list(request):
    """
    List all certificate templates.
    Direction only.
    """
    templates = CertificateTemplate.objects.all()

    # Filtering
    is_active = request.GET.get('is_active')
    if is_active:
        templates = templates.filter(is_active=(is_active == 'true'))

    # Pagination
    paginator = Paginator(templates, 20)
    page_num = request.GET.get('page', 1)
    templates_page = paginator.get_page(page_num)

    context = {
        'templates': templates_page,
        'total_count': paginator.count,
        'title': _('Certificate Templates'),
        'meta_description': _('Manage certificate templates'),
    }

    return render(request, 'certificates/template_list.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def template_detail(request, pk):
    """
    Display template details.
    """
    template = get_object_or_404(CertificateTemplate, pk=pk)

    # Get usage statistics
    total_certificates = template.certificates.count()

    context = {
        'template': template,
        'total_certificates': total_certificates,
        'title': template.name,
    }

    return render(request, 'certificates/template_detail.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def template_create(request):
    """
    Create new certificate template.
    """
    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            messages.success(request, _('Certificate template created successfully.'))
            return redirect('frontend:certificates:template_detail', pk=template.pk)
    else:
        form = CertificateTemplateForm()

    context = {
        'form': form,
        'title': _('Create Certificate Template'),
    }

    return render(request, 'certificates/template_form.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def template_update(request, pk):
    """
    Update certificate template.
    """
    template = get_object_or_404(CertificateTemplate, pk=pk)

    if request.method == 'POST':
        form = CertificateTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, _('Certificate template updated successfully.'))
            return redirect('frontend:certificates:template_detail', pk=template.pk)
    else:
        form = CertificateTemplateForm(instance=template)

    context = {
        'form': form,
        'template': template,
        'title': _('Edit Certificate Template'),
    }

    return render(request, 'certificates/template_form.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def template_delete(request, pk):
    """
    Delete certificate template.
    """
    template = get_object_or_404(CertificateTemplate, pk=pk)

    if request.method == 'POST':
        template.delete()
        messages.success(request, _('Certificate template deleted successfully.'))
        return redirect('frontend:certificates:template_list')

    context = {
        'template': template,
        'title': _('Delete Template'),
    }

    return render(request, 'certificates/template_confirm_delete.html', context)


# ============================================================================
# CERTIFICATE VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_list(request):
    """
    List certificates.
    Students see their own certificates.
    Staff see all certificates.
    """
    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)
        certificates = Certificate.objects.filter(student=student).select_related('course', 'template', 'issued_by')
    else:
        certificates = Certificate.objects.select_related('student', 'course', 'template', 'issued_by').all()

        # Filtering for staff
        course_id = request.GET.get('course')
        if course_id:
            certificates = certificates.filter(course_id=course_id)

        status_filter = request.GET.get('status')
        if status_filter:
            certificates = certificates.filter(status=status_filter)

        is_revoked = request.GET.get('is_revoked')
        if is_revoked:
            certificates = certificates.filter(is_revoked=(is_revoked == 'true'))

    # Pagination
    paginator = Paginator(certificates, 50)
    page_num = request.GET.get('page', 1)
    certificates_page = paginator.get_page(page_num)

    context = {
        'certificates': certificates_page,
        'total_count': paginator.count,
        'title': _('Certificates'),
    }

    return render(request, 'certificates/certificate_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_detail(request, pk):
    """
    Display certificate details.
    Students can view their own certificates.
    Staff can view all certificates.
    """
    certificate = get_object_or_404(
        Certificate.objects.select_related('student', 'course', 'template', 'issued_by'),
        pk=pk
    )

    # Check permissions
    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)
        if certificate.student != student:
            messages.error(request, _('You do not have permission to view this certificate.'))
            return redirect('frontend:certificates:certificate_list')

    # Get verification history
    verifications = certificate.verifications.all()[:10]

    context = {
        'certificate': certificate,
        'verifications': verifications,
        'title': f'Certificate {certificate.certificate_number}',
    }

    return render(request, 'certificates/certificate_detail.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_create(request):
    """
    Issue new certificate.
    Direction only.
    """
    if request.method == 'POST':
        form = CertificateForm(request.POST)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.issued_by = request.user
            certificate.status = 'issued'
            certificate.save()
            messages.success(request, _('Certificate issued successfully.'))
            return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)
    else:
        form = CertificateForm()

    context = {
        'form': form,
        'title': _('Issue Certificate'),
    }

    return render(request, 'certificates/certificate_form.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_edit(request, pk):
    """
    Edit certificate details.
    Direction only.
    """
    certificate = get_object_or_404(Certificate, pk=pk)

    if request.method == 'POST':
        form = CertificateForm(request.POST, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, _('Certificate updated successfully.'))
            return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)
    else:
        form = CertificateForm(instance=certificate)

    context = {
        'form': form,
        'certificate': certificate,
        'title': _('Edit Certificate'),
    }

    return render(request, 'certificates/certificate_form.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_reissue(request, pk):
    """
    Reissue a revoked certificate.
    POST-only: clears revocation status.
    Direction only.
    """
    certificate = get_object_or_404(Certificate, pk=pk)

    if request.method == 'POST':
        if not certificate.is_revoked:
            messages.error(request, _('Certificate is not revoked.'))
        else:
            certificate.is_revoked = False
            certificate.revoked_at = None
            certificate.revoked_by = None
            certificate.revocation_reason = ''
            certificate.status = 'issued'
            certificate.save()
            messages.success(request, _('Certificate has been reissued successfully.'))
        return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)

    # If not POST, redirect back to detail
    return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_revoke(request, pk):
    """
    Revoke certificate.
    Direction only.
    """
    certificate = get_object_or_404(Certificate, pk=pk)

    if certificate.is_revoked:
        messages.error(request, _('Certificate is already revoked.'))
        return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'No reason provided')
        certificate.revoke(user=request.user, reason=reason)
        messages.success(request, _('Certificate revoked successfully.'))
        return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)

    context = {
        'certificate': certificate,
        'title': _('Revoke Certificate'),
    }

    return render(request, 'certificates/certificate_revoke.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificate_download(request, pk):
    """
    Download certificate PDF.
    Students can download their own certificates.
    Staff can download all certificates.
    """
    certificate = get_object_or_404(Certificate, pk=pk)

    # Check permissions
    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)
        if certificate.student != student:
            messages.error(request, _('You do not have permission to download this certificate.'))
            return redirect('frontend:certificates:certificate_list')

    if not certificate.pdf_file:
        messages.error(request, _('Certificate PDF not available.'))
        return redirect('frontend:certificates:certificate_detail', pk=certificate.pk)

    # Return file
    response = FileResponse(
        certificate.pdf_file.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'attachment; filename="{certificate.certificate_number}.pdf"'
    return response


# ============================================================================
# PUBLIC CERTIFICATE VERIFICATION
# ============================================================================

@ratelimit(key='ip', rate='50/h')
def certificate_verify(request):
    """
    Public certificate verification page.
    No login required.
    """
    certificate = None
    verification_result = None

    if request.method == 'POST':
        form = CertificateVerificationForm(request.POST)
        if form.is_valid():
            cert_number = form.cleaned_data['certificate_number']

            try:
                certificate = Certificate.objects.get(certificate_number=cert_number)

                # Record verification
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')

                verification = CertificateVerification.objects.create(
                    certificate=certificate,
                    verification_method='number',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_valid=not certificate.is_revoked,
                    verification_notes='Web verification'
                )

                if certificate.is_revoked:
                    verification_result = {
                        'valid': False,
                        'message': _('This certificate has been revoked.'),
                        'revoked_at': certificate.revoked_at,
                        'revocation_reason': certificate.revocation_reason,
                    }
                else:
                    verification_result = {
                        'valid': True,
                        'message': _('This certificate is valid and authentic.'),
                    }

            except Certificate.DoesNotExist:
                verification_result = {
                    'valid': False,
                    'message': _('Certificate not found. Please check the certificate number.'),
                }
    else:
        form = CertificateVerificationForm()

    context = {
        'form': form,
        'certificate': certificate,
        'verification_result': verification_result,
        'title': _('Verify Certificate'),
    }

    return render(request, 'certificates/verify.html', context)


# ============================================================================
# BATCH GENERATION VIEWS
# ============================================================================

@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def batch_generation_list(request):
    """
    List batch certificate generations.
    Direction only.
    """
    batches = BatchCertificateGeneration.objects.select_related('course', 'template', 'initiated_by').all()

    # Filtering
    status_filter = request.GET.get('status')
    if status_filter:
        batches = batches.filter(status=status_filter)

    course_id = request.GET.get('course')
    if course_id:
        batches = batches.filter(course_id=course_id)

    # Pagination
    paginator = Paginator(batches, 20)
    page_num = request.GET.get('page', 1)
    batches_page = paginator.get_page(page_num)

    context = {
        'batches': batches_page,
        'total_count': paginator.count,
        'title': _('Batch Certificate Generation'),
    }

    return render(request, 'certificates/batch_list.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def batch_generation_create(request):
    """
    Create batch generation job.
    Direction only.
    """
    if request.method == 'POST':
        form = BatchCertificateGenerationForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.initiated_by = request.user

            # Count students that meet criteria
            from accounts.models import Student
            students = Student.objects.filter(program=batch.course.program)

            # Apply filters if specified
            if batch.min_gpa:
                # Filter by GPA if available
                pass

            batch.total_students = students.count()
            batch.save()

            messages.success(request, _('Batch generation created successfully.'))
            return redirect('frontend:certificates:batch_generation_detail', pk=batch.pk)
    else:
        form = BatchCertificateGenerationForm()

    context = {
        'form': form,
        'title': _('Create Batch Generation'),
    }

    return render(request, 'certificates/batch_form.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def batch_generation_detail(request, pk):
    """
    Display batch generation details and progress.
    Direction only.
    """
    batch = get_object_or_404(
        BatchCertificateGeneration.objects.select_related('course', 'template', 'initiated_by'),
        pk=pk
    )

    # Calculate progress
    progress_percentage = 0
    if batch.total_students > 0:
        progress_percentage = (batch.processed_count / batch.total_students) * 100

    context = {
        'batch': batch,
        'progress_percentage': progress_percentage,
        'title': f'Batch Generation - {batch.course.title}',
    }

    return render(request, 'certificates/batch_detail.html', context)


@login_required
@registrar_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def batch_generation_start(request, pk):
    """
    Start batch generation processing.
    Direction only.
    """
    batch = get_object_or_404(BatchCertificateGeneration, pk=pk)

    if batch.status != 'pending':
        messages.error(request, _(f'Batch is already {batch.get_status_display()}.'))
        return redirect('frontend:certificates:batch_generation_detail', pk=batch.pk)

    if request.method == 'POST':
        batch.status = 'processing'
        batch.started_at = timezone.now()
        batch.save()

        # Trigger Celery task (to be implemented)
        # from .tasks import generate_batch_certificates
        # generate_batch_certificates.delay(batch.id)

        messages.success(request, _('Batch generation started.'))
        return redirect('frontend:certificates:batch_generation_detail', pk=batch.pk)

    context = {
        'batch': batch,
        'title': _('Start Batch Generation'),
    }

    return render(request, 'certificates/batch_start_confirm.html', context)


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def certificates_dashboard(request):
    """
    Certificates dashboard.
    Shows different information based on user role.
    """
    context = {
        'title': _('Certificates Dashboard'),
    }

    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)

        # Student's certificates
        my_certificates = Certificate.objects.filter(student=student).select_related('course', 'template')

        context.update({
            'my_certificates': my_certificates,
            'total_certificates': my_certificates.count(),
        })

    else:  # direction or staff
        # System-wide statistics
        total_certificates = Certificate.objects.count()
        issued_certificates = Certificate.objects.filter(status='issued').count()
        revoked_certificates = Certificate.objects.filter(is_revoked=True).count()
        pending_certificates = Certificate.objects.filter(status='pending').count()

        # Recent certificates
        recent_certificates = Certificate.objects.select_related('student', 'course').order_by('-created_at')[:10]

        # Active batch generations
        active_batches = BatchCertificateGeneration.objects.filter(
            status__in=['pending', 'processing']
        ).count()

        context.update({
            'total_certificates': total_certificates,
            'issued_certificates': issued_certificates,
            'revoked_certificates': revoked_certificates,
            'pending_certificates': pending_certificates,
            'recent_certificates': recent_certificates,
            'active_batches': active_batches,
        })

    return render(request, 'certificates/dashboard.html', context)
