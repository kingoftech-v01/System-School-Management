from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from accounts.decorators import direction_only, tenant_required
from django_ratelimit.decorators import ratelimit
from django.db.models import Count, Sum, Avg, Q
from accounts.models import User
from enrollment.models import RegistrationForm


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def monitoring_dashboard(request):
    """Main analytics dashboard for direction."""

    # Student statistics
    total_students = User.objects.filter(
        tenant=request.tenant,
        role='student'
    ).count()

    total_professors = User.objects.filter(
        tenant=request.tenant,
        role='professor'
    ).count()

    total_parents = User.objects.filter(
        tenant=request.tenant,
        role='parent'
    ).count()

    # Enrollment statistics
    enrollment_stats = RegistrationForm.objects.filter(
        tenant=request.tenant
    ).values('status').annotate(count=Count('id'))

    # Gender distribution
    gender_stats = User.objects.filter(
        tenant=request.tenant,
        role='student'
    ).values('gender').annotate(count=Count('id'))

    # Library statistics (if library app is installed)
    library_stats = {}
    try:
        from library.models import Book, BorrowRecord
        library_stats = {
            'total_books': Book.objects.filter(tenant=request.tenant).count(),
            'borrowed': BorrowRecord.objects.filter(
                tenant=request.tenant,
                status='borrowed'
            ).count(),
            'overdue': BorrowRecord.objects.filter(
                tenant=request.tenant,
                status='overdue'
            ).count(),
        }
    except ImportError:
        pass

    # Discipline statistics
    discipline_stats = {}
    try:
        from discipline.models import DisciplinaryAction
        discipline_stats = {
            'total': DisciplinaryAction.objects.filter(tenant=request.tenant).count(),
            'unresolved': DisciplinaryAction.objects.filter(
                tenant=request.tenant,
                is_resolved=False
            ).count(),
        }
    except ImportError:
        pass

    context = {
        'total_students': total_students,
        'total_professors': total_professors,
        'total_parents': total_parents,
        'enrollment_stats': enrollment_stats,
        'gender_stats': gender_stats,
        'library_stats': library_stats,
        'discipline_stats': discipline_stats,
        'title': _('Monitoring Dashboard')
    }

    return render(request, 'monitoring/dashboard.html', context)


@login_required
@direction_only
@tenant_required
def enrollment_statistics(request):
    """Detailed enrollment statistics."""
    stats = RegistrationForm.objects.filter(
        tenant=request.tenant
    ).values('status', 'level').annotate(count=Count('id'))

    return render(request, 'monitoring/enrollment_stats.html', {
        'stats': stats,
        'title': _('Enrollment Statistics')
    })


@login_required
@direction_only
@tenant_required
def library_statistics(request):
    """Detailed library statistics."""
    try:
        from library.models import Book, BorrowRecord

        books_by_category = Book.objects.filter(
            tenant=request.tenant
        ).values('category').annotate(count=Count('id'))

        borrow_stats = BorrowRecord.objects.filter(
            tenant=request.tenant
        ).values('status').annotate(count=Count('id'))

        context = {
            'books_by_category': books_by_category,
            'borrow_stats': borrow_stats,
            'title': _('Library Statistics')
        }

        return render(request, 'monitoring/library_stats.html', context)
    except ImportError:
        return render(request, 'monitoring/not_available.html', {
            'message': _('Library app is not installed')
        })


@login_required
@direction_only
@tenant_required
def export_dashboard_csv(request):
    """Export dashboard data to CSV."""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dashboard_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])

    # Add statistics
    total_students = User.objects.filter(tenant=request.tenant, role='student').count()
    total_professors = User.objects.filter(tenant=request.tenant, role='professor').count()
    total_parents = User.objects.filter(tenant=request.tenant, role='parent').count()

    writer.writerow(['Total Students', total_students])
    writer.writerow(['Total Professors', total_professors])
    writer.writerow(['Total Parents', total_parents])

    return response
