from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.utils import timezone

from accounts.decorators import admin_required, lecturer_required
from accounts.models import User, Student, Parent
from .forms import SessionForm, SemesterForm, NewsAndEventsForm
from .models import NewsAndEvents, ActivityLog, Session, Semester


# ########################################################
# News & Events
# ########################################################
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_date")
    context = {
        "title": "News & Events",
        "items": items,
    }
    return render(request, "core/index.html", context)


@login_required
def unified_dashboard(request):
    """
    Single dashboard view that displays role-specific content.
    Routes based on user_role set by RoleMiddleware.
    """
    user_role = getattr(request, 'user_role', 'student')

    # Common context for all roles
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True,
        session=current_session
    ).first()

    base_context = {
        'current_session': current_session,
        'current_semester': current_semester,
        'user_role': user_role,
    }

    # Route to role-specific dashboard renderer
    if user_role == 'student':
        return render_student_dashboard(request, base_context)
    elif user_role == 'parent':
        return render_parent_dashboard(request, base_context)
    elif user_role == 'professor':
        return render_professor_dashboard(request, base_context)
    elif user_role == 'prefet':
        return render_prefet_dashboard(request, base_context)
    elif user_role == 'accountant':
        return render_accountant_dashboard(request, base_context)
    elif user_role == 'direction':
        return render_direction_dashboard(request, base_context)
    elif user_role == 'admin':
        return render_admin_dashboard(request, base_context)
    else:
        # Fallback
        return render(request, 'dashboards/student_dashboard.html', base_context)


def render_student_dashboard(request, base_context):
    """Render student-specific dashboard with course, grade, attendance data."""
    try:
        student = Student.objects.select_related('student').get(student=request.user)
    except Student.DoesNotExist:
        context = {
            **base_context,
            'title': 'Student Dashboard',
            'error': 'Student profile not found. Please contact administration.',
            'gpa': 0,
            'courses_count': 0,
            'attendance_summary': {'total': 0, 'present': 0, 'percentage': 0},
        }
        return render(request, 'dashboards/student_dashboard.html', context)

    # Get current courses
    try:
        from result.models import TakenCourse
        courses = TakenCourse.objects.filter(
            student=student,
            course__semester=base_context['current_semester']
        ).select_related('course')

        # Calculate GPA
        gpa = TakenCourse.objects.filter(
            student=student,
            total__isnull=False
        ).aggregate(Avg('total'))['total__avg'] or 0.0

        # Get recent grades
        recent_grades = TakenCourse.objects.filter(
            student=student,
            total__isnull=False
        ).order_by('-id')[:5]
    except:
        courses = []
        gpa = 0.0
        recent_grades = []

    # Attendance summary
    try:
        from attendance.models import Attendance
        total_classes = Attendance.objects.filter(
            student=request.user,
            session=base_context['current_session']
        ).count()
        present_count = Attendance.objects.filter(
            student=request.user,
            session=base_context['current_session'],
            status='present'
        ).count()
        attendance_percentage = round((present_count / total_classes * 100) if total_classes > 0 else 0, 2)
        attendance_summary = {
            'total': total_classes,
            'present': present_count,
            'percentage': attendance_percentage
        }
    except:
        attendance_summary = {'total': 0, 'present': 0, 'percentage': 0}

    context = {
        **base_context,
        'title': 'Student Dashboard',
        'student': student,
        'courses': courses,
        'courses_count': len(courses),
        'gpa': round(gpa, 2),
        'recent_grades': recent_grades,
        'attendance_summary': attendance_summary,
    }

    return render(request, 'dashboards/student_dashboard.html', context)


def render_parent_dashboard(request, base_context):
    """Render parent-specific dashboard with child monitoring data."""
    parent_profiles = Parent.objects.select_related('student').filter(user=request.user)
    if not parent_profiles.exists():
        context = {
            **base_context,
            'title': 'Parent Dashboard',
            'error': 'Parent profile not found. Please contact administration.'
        }
        return render(request, 'dashboards/parent_dashboard.html', context)

    # Support multi-child: use session-selected child or default to first
    active_child_id = request.session.get('active_child_id')
    parent = None
    if active_child_id:
        parent = parent_profiles.filter(student_id=active_child_id).first()
    if not parent:
        parent = parent_profiles.first()

    student = parent.student
    children = [p.student for p in parent_profiles if p.student]

    context = {
        **base_context,
        'title': 'Parent Dashboard',
        'parent': parent,
        'student': student,
        'children': children,
        'active_child_id': parent.student_id if parent.student else None,
    }

    return render(request, 'dashboards/parent_dashboard.html', context)


def render_professor_dashboard(request, base_context):
    """Render professor-specific dashboard with teaching data."""
    try:
        from course.models import Course
        my_courses = Course.objects.filter(
            allocated_course__lecturer=request.user,
            semester=base_context['current_semester']
        ).distinct()

        total_students = 0
        for course in my_courses:
            try:
                total_students += course.students.count()
            except:
                pass
    except:
        my_courses = []
        total_students = 0

    context = {
        **base_context,
        'title': 'Professor Dashboard',
        'my_courses': my_courses,
        'courses_count': my_courses.count() if my_courses else 0,
        'total_students': total_students,
    }

    return render(request, 'dashboards/professor_dashboard.html', context)


def render_direction_dashboard(request, base_context):
    """Render direction-specific dashboard with school-wide analytics."""
    total_students = Student.objects.filter(student__tenant=request.tenant).count()
    total_professors = User.objects.filter(
        tenant=request.tenant,
        role='professor'
    ).count()

    try:
        from payments.models import Invoice
        total_invoices = Invoice.objects.filter(
            tenant=request.tenant,
            session=base_context['current_session']
        ).count()
        paid_invoices = Invoice.objects.filter(
            tenant=request.tenant,
            session=base_context['current_session'],
            status='paid'
        ).count()
        payment_collection_rate = round((paid_invoices / total_invoices * 100) if total_invoices > 0 else 0, 2)
    except:
        payment_collection_rate = 0

    context = {
        **base_context,
        'title': 'Direction Dashboard',
        'total_students': total_students,
        'total_professors': total_professors,
        'payment_collection_rate': payment_collection_rate,
    }

    return render(request, 'dashboards/direction_dashboard.html', context)


def render_prefet_dashboard(request, base_context):
    """Render discipline officer dashboard with discipline and attendance focus."""
    from discipline.models import DisciplinaryAction
    from django.db.models import Count

    # Discipline stats
    all_actions = DisciplinaryAction.objects.filter(tenant=request.tenant)
    total_actions = all_actions.count()
    pending_actions = all_actions.filter(is_resolved=False).count()
    resolved_actions = all_actions.filter(is_resolved=True).count()

    # Severity breakdown
    severity_breakdown = list(
        all_actions.values('severity').annotate(count=Count('id')).order_by('severity')
    )

    # Recent incidents (last 10)
    recent_incidents = all_actions.select_related(
        'student', 'reported_by'
    ).order_by('-incident_date')[:10]

    # Attendance overview
    attendance_stats = {}
    try:
        from attendance.models import Attendance, AttendanceReport, Satus
        today = timezone.now().date()
        today_sessions = Attendance.objects.filter(date=today).count()
        today_reports = AttendanceReport.objects.filter(attendance__date=today)
        attendance_stats = {
            'today_sessions': today_sessions,
            'today_present': today_reports.filter(status=Satus.PRESENT).count() if hasattr(Satus, 'PRESENT') else 0,
            'today_absent': today_reports.filter(status=Satus.ABSENT).count() if hasattr(Satus, 'ABSENT') else 0,
        }
    except Exception:
        pass

    # Student count
    total_students = Student.objects.filter(student__tenant=request.tenant).count()

    context = {
        **base_context,
        'title': 'Discipline Officer Dashboard',
        'total_actions': total_actions,
        'pending_actions': pending_actions,
        'resolved_actions': resolved_actions,
        'severity_breakdown': severity_breakdown,
        'recent_incidents': recent_incidents,
        'attendance_stats': attendance_stats,
        'total_students': total_students,
    }

    return render(request, 'dashboards/prefet_dashboard.html', context)


def render_accountant_dashboard(request, base_context):
    """Render accountant dashboard with financial data focus."""
    from payments.models import Invoice, Payment, FeeStructure
    from django.db.models import Sum, Q

    # Invoice stats
    all_invoices = Invoice.objects.all()
    total_invoices = all_invoices.count()
    paid_invoices = all_invoices.filter(payment_complete=True).count()
    unpaid_invoices = all_invoices.filter(payment_complete=False).count()

    # Overdue invoices
    today = timezone.now().date()
    overdue_invoices = all_invoices.filter(
        payment_complete=False,
        due_date__lt=today
    ).count()

    # Collection rate
    collection_rate = round((paid_invoices / total_invoices * 100), 2) if total_invoices > 0 else 0

    # Financial totals
    amount_stats = all_invoices.aggregate(
        total_billed=Sum('amount'),
        total_collected=Sum('amount', filter=Q(payment_complete=True)),
    )
    total_billed = amount_stats['total_billed'] or 0
    total_collected = amount_stats['total_collected'] or 0
    total_outstanding = total_billed - total_collected

    # Recent payments (last 10)
    recent_payments = Payment.objects.select_related(
        'invoice', 'invoice__user'
    ).order_by('-payment_date')[:10]

    # Overdue invoices list (last 10)
    overdue_invoice_list = all_invoices.filter(
        payment_complete=False,
        due_date__lt=today
    ).select_related('user', 'student').order_by('due_date')[:10]

    # Active fee structures count
    active_fee_structures = FeeStructure.objects.filter(is_active=True).count()

    # Student count
    total_students = Student.objects.count()

    context = {
        **base_context,
        'title': 'Accountant Dashboard',
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'unpaid_invoices': unpaid_invoices,
        'overdue_invoices': overdue_invoices,
        'collection_rate': collection_rate,
        'total_billed': total_billed,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'recent_payments': recent_payments,
        'overdue_invoice_list': overdue_invoice_list,
        'active_fee_structures': active_fee_structures,
        'total_students': total_students,
    }

    return render(request, 'dashboards/accountant_dashboard.html', context)


def render_admin_dashboard(request, base_context):
    """Render admin dashboard with system-wide controls."""
    from core.models import School

    total_tenants = School.objects.count()
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]

    context = {
        **base_context,
        'title': 'Admin Dashboard',
        'total_tenants': total_tenants,
        'logs': logs,
    }

    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
@admin_required
def dashboard_view(request):
    """Legacy dashboard view - kept for backward compatibility"""
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()
    context = {
        "student_count": User.objects.get_student_count(),
        "lecturer_count": User.objects.get_lecturer_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
    }
    return render(request, "core/dashboard.html", context)


@login_required
@lecturer_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been uploaded.")
            return redirect("frontend:core:home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm()
    return render(request, "core/post_add.html", {"title": "Add Post", "form": form})


@login_required
@lecturer_required
def edit_post(request, pk):
    instance = get_object_or_404(NewsAndEvents, pk=pk)
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=instance)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been updated.")
            return redirect("frontend:core:home")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = NewsAndEventsForm(instance=instance)
    return render(request, "core/post_add.html", {"title": "Edit Post", "form": form})


@login_required
@lecturer_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    post_title = post.title
    post.delete()
    messages.success(request, f"{post_title} has been deleted.")
    return redirect("frontend:core:home")


@login_required
def post_detail(request, pk):
    """Show a single news or event post."""
    post = get_object_or_404(NewsAndEvents, pk=pk)
    return render(request, "core/post_detail.html", {
        "title": post.title,
        "post": post,
    })


@login_required
def news_search(request):
    """Search news and events by query string."""
    query = request.GET.get('q', '').strip()
    results = NewsAndEvents.objects.none()

    if query:
        results = NewsAndEvents.objects.search(query)

    paginator = Paginator(results, 20)
    page_num = request.GET.get('page', 1)
    results_page = paginator.get_page(page_num)

    return render(request, "core/news_search.html", {
        "title": "Search News & Events",
        "query": query,
        "results": results_page,
    })


# ########################################################
# Session
# ########################################################
@login_required
@lecturer_required
def session_list_view(request):
    """Show list of all sessions"""
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@lecturer_required
def session_add_view(request):
    """Add a new session"""
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session added successfully.")
            return redirect("frontend:core:session_list")
    else:
        form = SessionForm()
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, instance=session)
        if form.is_valid():
            if form.cleaned_data.get("is_current_session"):
                unset_current_session()
            form.save()
            messages.success(request, "Session updated successfully.")
            return redirect("frontend:core:session_list")
    else:
        form = SessionForm(instance=session)
    return render(request, "core/session_update.html", {"form": form})


@login_required
@lecturer_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if session.is_current_session:
        messages.error(request, "You cannot delete the current session.")
    else:
        session.delete()
        messages.success(request, "Session successfully deleted.")
    return redirect("frontend:core:session_list")


def unset_current_session():
    """Unset current session"""
    current_session = Session.objects.filter(is_current_session=True).first()
    if current_session:
        current_session.is_current_session = False
        current_session.save()


# ########################################################
# Semester
# ########################################################
@login_required
@lecturer_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(request, "core/semester_list.html", {"semesters": semesters})


@login_required
@lecturer_required
def semester_add_view(request):
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester added successfully.")
            return redirect("frontend:core:semester_list")
    else:
        form = SemesterForm()
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_update_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            if form.cleaned_data.get("is_current_semester"):
                unset_current_semester()
                unset_current_session()
            form.save()
            messages.success(request, "Semester updated successfully!")
            return redirect("frontend:core:semester_list")
    else:
        form = SemesterForm(instance=semester)
    return render(request, "core/semester_update.html", {"form": form})


@login_required
@lecturer_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if semester.is_current_semester:
        messages.error(request, "You cannot delete the current semester.")
    else:
        semester.delete()
        messages.success(request, "Semester successfully deleted.")
    return redirect("frontend:core:semester_list")


def unset_current_semester():
    """Unset current semester"""
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if current_semester:
        current_semester.is_current_semester = False
        current_semester.save()
