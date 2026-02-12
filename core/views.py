from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    linked_profiles = parent_profiles.filter(student__isnull=False)

    # If no profiles or no linked children, redirect to parent portal (has empty state)
    if not linked_profiles.exists():
        return redirect('frontend:accounts:parent_dashboard')

    # Support multi-child: use session-selected child or default to first
    active_child_id = request.session.get('active_child_id')
    parent = None
    if active_child_id:
        parent = linked_profiles.filter(student_id=active_child_id).first()
    if not parent:
        parent = linked_profiles.first()

    student = parent.student
    children = [p.student for p in linked_profiles]

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
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        title = form.cleaned_data.get("title", "Post") if form.is_valid() else None
        if form.is_valid():
            form.save()
            messages.success(request, f"{title} has been uploaded.")
            return redirect("home")
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
            return redirect("home")
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
    return redirect("home")


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
            return redirect("session_list")
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
            return redirect("session_list")
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
    return redirect("session_list")


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
            return redirect("semester_list")
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
            return redirect("semester_list")
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
    return redirect("semester_list")


def unset_current_semester():
    """Unset current semester"""
    current_semester = Semester.objects.filter(is_current_semester=True).first()
    if current_semester:
        current_semester.is_current_semester = False
        current_semester.save()
