from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from accounts.decorators import direction_only, tenant_required
from django_ratelimit.decorators import ratelimit
from django.db.models import Count, Sum, Avg, Q
from accounts.models import User
from enrollment.models import RegistrationForm
from .forms import DashboardFilterForm


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def monitoring_dashboard(request):
    """Main analytics dashboard for direction with optional date range filtering."""

    # Parse date range filter
    filter_form = DashboardFilterForm(request.GET or None)
    date_from = None
    date_to = None
    if filter_form.is_valid():
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')

    # Base querysets
    students_qs = User.objects.filter(tenant=request.tenant, role='student')
    professors_qs = User.objects.filter(tenant=request.tenant, role='professor')
    parents_qs = User.objects.filter(tenant=request.tenant, role='parent')
    enrollment_qs = RegistrationForm.objects.filter(tenant=request.tenant)

    # Apply date range filters where applicable
    if date_from:
        students_qs = students_qs.filter(date_joined__gte=date_from)
        professors_qs = professors_qs.filter(date_joined__gte=date_from)
        parents_qs = parents_qs.filter(date_joined__gte=date_from)
        enrollment_qs = enrollment_qs.filter(created_at__gte=date_from)
    if date_to:
        students_qs = students_qs.filter(date_joined__lte=date_to)
        professors_qs = professors_qs.filter(date_joined__lte=date_to)
        parents_qs = parents_qs.filter(date_joined__lte=date_to)
        enrollment_qs = enrollment_qs.filter(created_at__lte=date_to)

    # Student statistics
    total_students = students_qs.count()
    total_professors = professors_qs.count()
    total_parents = parents_qs.count()

    # Enrollment statistics
    enrollment_stats = enrollment_qs.values('status').annotate(count=Count('id'))

    # Gender distribution
    gender_stats = students_qs.values('gender').annotate(count=Count('id'))

    # Library statistics (if library app is installed)
    library_stats = {}
    try:
        from library.models import Book, BorrowRecord
        borrow_qs = BorrowRecord.objects.filter(tenant=request.tenant)
        if date_from:
            borrow_qs = borrow_qs.filter(borrowed_at__gte=date_from)
        if date_to:
            borrow_qs = borrow_qs.filter(borrowed_at__lte=date_to)

        library_stats = {
            'total_books': Book.objects.filter(tenant=request.tenant).count(),
            'borrowed': borrow_qs.filter(status='borrowed').count(),
            'overdue': borrow_qs.filter(status='overdue').count(),
        }
    except ImportError:
        pass

    # Discipline statistics
    discipline_stats = {}
    try:
        from discipline.models import DisciplinaryAction
        disc_qs = DisciplinaryAction.objects.filter(tenant=request.tenant)
        if date_from:
            disc_qs = disc_qs.filter(created_at__gte=date_from)
        if date_to:
            disc_qs = disc_qs.filter(created_at__lte=date_to)

        discipline_stats = {
            'total': disc_qs.count(),
            'unresolved': disc_qs.filter(is_resolved=False).count(),
        }
    except ImportError:
        pass

    # Attendance statistics (conditional import)
    attendance_stats = {}
    try:
        from attendance.models import Attendance
        att_qs = Attendance.objects.filter(tenant=request.tenant)
        if date_from:
            att_qs = att_qs.filter(date__gte=date_from)
        if date_to:
            att_qs = att_qs.filter(date__lte=date_to)

        attendance_stats = {
            'total_records': att_qs.count(),
            'present': att_qs.filter(status='present').count(),
            'absent': att_qs.filter(status='absent').count(),
            'late': att_qs.filter(status='late').count(),
        }
    except (ImportError, Exception):
        pass

    # Grade statistics (conditional import)
    grade_stats = {}
    try:
        from grading.models import RubricGrade
        grade_qs = RubricGrade.objects.all()
        if date_from:
            grade_qs = grade_qs.filter(graded_at__gte=date_from)
        if date_to:
            grade_qs = grade_qs.filter(graded_at__lte=date_to)

        avg_data = grade_qs.aggregate(
            avg_percentage=Avg('percentage'),
            total_entries=Count('id')
        )
        grade_stats = {
            'total_entries': avg_data['total_entries'] or 0,
            'avg_percentage': round(avg_data['avg_percentage'] or 0, 2),
        }
    except (ImportError, Exception):
        pass

    context = {
        'filter_form': filter_form,
        'date_from': date_from,
        'date_to': date_to,
        'total_students': total_students,
        'total_professors': total_professors,
        'total_parents': total_parents,
        'enrollment_stats': enrollment_stats,
        'gender_stats': gender_stats,
        'library_stats': library_stats,
        'discipline_stats': discipline_stats,
        'attendance_stats': attendance_stats,
        'grade_stats': grade_stats,
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
    """Export comprehensive dashboard data to CSV."""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="dashboard_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category', 'Metric', 'Value'])

    # ---- User statistics ----
    total_students = User.objects.filter(tenant=request.tenant, role='student').count()
    total_professors = User.objects.filter(tenant=request.tenant, role='professor').count()
    total_parents = User.objects.filter(tenant=request.tenant, role='parent').count()

    writer.writerow(['Users', 'Total Students', total_students])
    writer.writerow(['Users', 'Total Professors', total_professors])
    writer.writerow(['Users', 'Total Parents', total_parents])

    # ---- Enrollment statistics ----
    enrollment_stats = RegistrationForm.objects.filter(
        tenant=request.tenant
    ).values('status').annotate(count=Count('id'))

    for stat in enrollment_stats:
        writer.writerow(['Enrollment', f'Status: {stat["status"]}', stat['count']])

    total_enrollments = RegistrationForm.objects.filter(tenant=request.tenant).count()
    writer.writerow(['Enrollment', 'Total Enrollments', total_enrollments])

    # ---- Gender statistics ----
    gender_stats = User.objects.filter(
        tenant=request.tenant,
        role='student'
    ).values('gender').annotate(count=Count('id'))

    for stat in gender_stats:
        gender_label = stat['gender'] if stat['gender'] else 'Not Specified'
        writer.writerow(['Gender Distribution', gender_label, stat['count']])

    # ---- Library statistics ----
    try:
        from library.models import Book, BorrowRecord
        total_books = Book.objects.filter(tenant=request.tenant).count()
        borrowed_count = BorrowRecord.objects.filter(
            tenant=request.tenant, status='borrowed'
        ).count()
        overdue_count = BorrowRecord.objects.filter(
            tenant=request.tenant, status='overdue'
        ).count()
        returned_count = BorrowRecord.objects.filter(
            tenant=request.tenant, status='returned'
        ).count()
        lost_count = BorrowRecord.objects.filter(
            tenant=request.tenant, status='lost'
        ).count()

        writer.writerow(['Library', 'Total Books', total_books])
        writer.writerow(['Library', 'Currently Borrowed', borrowed_count])
        writer.writerow(['Library', 'Overdue', overdue_count])
        writer.writerow(['Library', 'Returned', returned_count])
        writer.writerow(['Library', 'Lost', lost_count])
    except ImportError:
        pass

    # ---- Discipline statistics ----
    try:
        from discipline.models import DisciplinaryAction
        disc_total = DisciplinaryAction.objects.filter(tenant=request.tenant).count()
        disc_unresolved = DisciplinaryAction.objects.filter(
            tenant=request.tenant, is_resolved=False
        ).count()
        disc_resolved = DisciplinaryAction.objects.filter(
            tenant=request.tenant, is_resolved=True
        ).count()

        writer.writerow(['Discipline', 'Total Actions', disc_total])
        writer.writerow(['Discipline', 'Resolved', disc_resolved])
        writer.writerow(['Discipline', 'Unresolved', disc_unresolved])
    except ImportError:
        pass

    # ---- Attendance statistics ----
    try:
        from attendance.models import Attendance
        att_qs = Attendance.objects.filter(tenant=request.tenant)
        att_total = att_qs.count()
        att_present = att_qs.filter(status='present').count()
        att_absent = att_qs.filter(status='absent').count()
        att_late = att_qs.filter(status='late').count()

        writer.writerow(['Attendance', 'Total Records', att_total])
        writer.writerow(['Attendance', 'Present', att_present])
        writer.writerow(['Attendance', 'Absent', att_absent])
        writer.writerow(['Attendance', 'Late', att_late])
    except (ImportError, Exception):
        pass

    # ---- Grade statistics ----
    try:
        from grading.models import RubricGrade
        grade_data = RubricGrade.objects.aggregate(
            total_entries=Count('id'),
            avg_percentage=Avg('percentage')
        )
        writer.writerow(['Grades', 'Total Grade Entries', grade_data['total_entries'] or 0])
        writer.writerow(['Grades', 'Average Percentage', round(grade_data['avg_percentage'] or 0, 2)])
    except (ImportError, Exception):
        pass

    return response
