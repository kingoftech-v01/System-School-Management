from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
from xhtml2pdf import pisa

from accounts.decorators import admin_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.forms import (
    ParentAddForm,
    ProfileUpdateForm,
    ProgramUpdateForm,
    StaffAddForm,
    StudentAddForm,
)
from accounts.models import Parent, Student, User
from core.models import Semester, Session
from course.models import Course
from result.models import TakenCourse

# ########################################################
# Utility Functions
# ########################################################


def render_to_pdf(template_name, context):
    """Render a given template to PDF format."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="profile.pdf"'
    template = render_to_string(template_name, context)
    pdf = pisa.CreatePDF(template, dest=response)
    if pdf.err:
        return HttpResponse("We had some problems generating the PDF")
    return response


# ########################################################
# Authentication and Registration
# ########################################################


def validate_username(request):
    username = request.GET.get("username", None)
    data = {"is_taken": User.objects.filter(username__iexact=username).exists()}
    return JsonResponse(data)


def register(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect("login")
        messages.error(
            request, "Something is not correct, please fill all fields correctly."
        )
    else:
        form = StudentAddForm()
    return render(request, "registration/register.html", {"form": form})


# ########################################################
# Profile Views
# ########################################################


@login_required
def profile(request):
    """Show profile of the current user."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    context = {
        "title": request.user.get_full_name,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if request.user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=request.user.id, semester=current_semester
        )
        context["courses"] = courses
        return render(request, "accounts/profile.html", context)

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        parent = Parent.objects.filter(student=student).first()
        courses = TakenCourse.objects.filter(
            student__student__id=request.user.id, course__level=student.level
        )
        context.update(
            {
                "parent": parent,
                "courses": courses,
                "level": student.level,
            }
        )
        return render(request, "accounts/profile.html", context)

    # For superuser or other staff
    staff = User.objects.filter(is_lecturer=True)
    context["staff"] = staff
    return render(request, "accounts/profile.html", context)


@login_required
@admin_required
def profile_single(request, user_id):
    """Show profile of any selected user."""
    if request.user.id == user_id:
        return redirect("profile")

    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()
    user = get_object_or_404(User, pk=user_id)

    context = {
        "title": user.get_full_name,
        "user": user,
        "current_session": current_session,
        "current_semester": current_semester,
    }

    if user.is_lecturer:
        courses = Course.objects.filter(
            allocated_course__lecturer__pk=user_id, semester=current_semester
        )
        context.update(
            {
                "user_type": "Lecturer",
                "courses": courses,
            }
        )
    elif user.is_student:
        student = get_object_or_404(Student, student__pk=user_id)
        courses = TakenCourse.objects.filter(
            student__student__id=user_id, course__level=student.level
        )
        context.update(
            {
                "user_type": "Student",
                "courses": courses,
                "student": student,
            }
        )
    else:
        context["user_type"] = "Superuser"

    if request.GET.get("download_pdf"):
        return render_to_pdf("pdf/profile_single.html", context)

    return render(request, "accounts/profile_single.html", context)


@login_required
@admin_required
def admin_panel(request):
    return render(request, "setting/admin_panel.html", {"title": "Admin Panel"})


# ########################################################
# Settings Views
# ########################################################


@login_required
def profile_update(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, "setting/profile_info_change.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect("profile")
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "setting/password_change.html", {"form": form})


# ########################################################
# Staff (Lecturer) Views
# ########################################################


@login_required
@admin_required
def staff_add_view(request):
    if request.method == "POST":
        form = StaffAddForm(request.POST)
        if form.is_valid():
            lecturer = form.save()
            full_name = lecturer.get_full_name
            email = lecturer.email
            messages.success(
                request,
                f"Account for lecturer {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("lecturer_list")
    else:
        form = StaffAddForm()
    return render(
        request, "accounts/add_staff.html", {"title": "Add Lecturer", "form": form}
    )


@login_required
@admin_required
def edit_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=lecturer)
        if form.is_valid():
            form.save()
            full_name = lecturer.get_full_name
            messages.success(request, f"Lecturer {full_name} has been updated.")
            return redirect("lecturer_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=lecturer)
    return render(
        request, "accounts/edit_lecturer.html", {"title": "Edit Lecturer", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class LecturerFilterView(FilterView):
    filterset_class = LecturerFilter
    queryset = User.objects.filter(is_lecturer=True)
    template_name = "accounts/lecturer_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lecturers"
        return context


@login_required
@admin_required
def render_lecturer_pdf_list(request):
    lecturers = User.objects.filter(is_lecturer=True)
    template_path = "pdf/lecturer_list.html"
    context = {"lecturers": lecturers}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="lecturers_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_staff(request, pk):
    lecturer = get_object_or_404(User, is_lecturer=True, pk=pk)
    full_name = lecturer.get_full_name
    lecturer.delete()
    messages.success(request, f"Lecturer {full_name} has been deleted.")
    return redirect("lecturer_list")


# ########################################################
# Student Views
# ########################################################


@login_required
@admin_required
def student_add_view(request):
    if request.method == "POST":
        form = StudentAddForm(request.POST)
        if form.is_valid():
            student = form.save()
            full_name = student.get_full_name
            email = student.email
            messages.success(
                request,
                f"Account for {full_name} has been created. "
                f"An email with account credentials will be sent to {email} within a minute.",
            )
            return redirect("student_list")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = StudentAddForm()
    return render(
        request, "accounts/add_student.html", {"title": "Add Student", "form": form}
    )


@login_required
@admin_required
def edit_student(request, pk):
    student_user = get_object_or_404(User, is_student=True, pk=pk)
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=student_user)
        if form.is_valid():
            form.save()
            full_name = student_user.get_full_name
            messages.success(request, f"Student {full_name} has been updated.")
            return redirect("student_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=student_user)
    return render(
        request, "accounts/edit_student.html", {"title": "Edit Student", "form": form}
    )


@method_decorator([login_required, admin_required], name="dispatch")
class StudentListView(FilterView):
    queryset = Student.objects.all()
    filterset_class = StudentFilter
    template_name = "accounts/student_list.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Students"
        return context


@login_required
@admin_required
def render_student_pdf_list(request):
    students = Student.objects.all()
    template_path = "pdf/student_list.html"
    context = {"students": students}
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="students_list.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse(f"We had some errors <pre>{html}</pre>")
    return response


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    full_name = student.student.get_full_name
    student.delete()
    messages.success(request, f"Student {full_name} has been deleted.")
    return redirect("student_list")


@login_required
@admin_required
def edit_student_program(request, pk):
    student = get_object_or_404(Student, student_id=pk)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = ProgramUpdateForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            full_name = user.get_full_name
            messages.success(request, f"{full_name}'s program has been updated.")
            return redirect("profile_single", user_id=pk)
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProgramUpdateForm(instance=student)
    return render(
        request,
        "accounts/edit_student_program.html",
        {"title": "Edit Program", "form": form, "student": student},
    )


# ########################################################
# Parent Views
# ########################################################


@method_decorator([login_required, admin_required], name="dispatch")
class ParentAdd(CreateView):
    model = Parent
    form_class = ParentAddForm
    template_name = "accounts/parent_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Parent added successfully.")
        return super().form_valid(form)


# ########################################################
# NEW: Role-Based Dashboard Views for Multi-Tenant System
# ########################################################

from .decorators import student_only, parent_only, professor_only, direction_only
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
from django.utils import timezone


@login_required
@student_only
def dashboard_student(request):
    """Student dashboard with personal academic information."""
    student = get_object_or_404(Student, student=request.user)
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    # Get student's courses
    courses = TakenCourse.objects.filter(
        student=student,
        course__semester=current_semester
    ).select_related('course', 'course__allocated_course')

    # Get recent grades (last 5)
    recent_grades = TakenCourse.objects.filter(
        student=student,
        total__isnull=False
    ).order_by('-id')[:5]

    # Calculate GPA
    gpa = TakenCourse.objects.filter(
        student=student,
        total__isnull=False
    ).aggregate(Avg('total'))['total__avg'] or 0.0

    # Get borrowed books (if library app exists)
    borrowed_books = []
    try:
        from library.models import BorrowRecord
        borrowed_books = BorrowRecord.objects.filter(
            student=request.user,
            status='borrowed'
        ).select_related('book')[:5]
    except:
        pass

    # Get upcoming events
    upcoming_events = []
    try:
        from events.models import Event
        upcoming_events = Event.objects.filter(
            tenant=request.tenant,
            start_date__gte=timezone.now(),
            target_audience__in=['all', 'students']
        ).order_by('start_date')[:5]
    except:
        pass

    # Get attendance summary
    attendance_summary = {}
    try:
        from attendance.models import AttendanceRecord
        total_classes = AttendanceRecord.objects.filter(
            student=request.user,
            session=current_session
        ).count()
        present_classes = AttendanceRecord.objects.filter(
            student=request.user,
            session=current_session,
            status='present'
        ).count()
        if total_classes > 0:
            attendance_percentage = (present_classes / total_classes) * 100
        else:
            attendance_percentage = 0
        attendance_summary = {
            'total': total_classes,
            'present': present_classes,
            'percentage': round(attendance_percentage, 2)
        }
    except:
        pass

    context = {
        'title': 'Student Dashboard',
        'student': student,
        'courses': courses,
        'recent_grades': recent_grades,
        'gpa': round(gpa, 2),
        'borrowed_books': borrowed_books,
        'upcoming_events': upcoming_events,
        'attendance_summary': attendance_summary,
        'current_session': current_session,
        'current_semester': current_semester,
    }

    return render(request, 'accounts/dashboard_student.html', context)


@login_required
@parent_only
def dashboard_parent(request):
    """Parent dashboard with children's academic information."""
    parent = get_object_or_404(Parent, user=request.user)
    student = parent.student
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    # Get student's recent grades
    recent_grades = TakenCourse.objects.filter(
        student=student,
        total__isnull=False
    ).order_by('-id')[:10]

    # Calculate GPA
    gpa = TakenCourse.objects.filter(
        student=student,
        total__isnull=False
    ).aggregate(Avg('total'))['total__avg'] or 0.0

    # Get attendance summary
    attendance_summary = {}
    try:
        from attendance.models import AttendanceRecord
        total_classes = AttendanceRecord.objects.filter(
            student=student.student,
            session=current_session
        ).count()
        present_classes = AttendanceRecord.objects.filter(
            student=student.student,
            session=current_session,
            status='present'
        ).count()
        if total_classes > 0:
            attendance_percentage = (present_classes / total_classes) * 100
        else:
            attendance_percentage = 0
        attendance_summary = {
            'total': total_classes,
            'present': present_classes,
            'percentage': round(attendance_percentage, 2)
        }
    except:
        pass

    # Get payment status
    payment_status = {}
    try:
        from payments.models import PaymentRecord
        total_fees = PaymentRecord.objects.filter(
            student=student.student,
            session=current_session
        ).aggregate(
            total=models.Sum('amount'),
            paid=models.Sum('amount', filter=Q(status='paid'))
        )
        payment_status = {
            'total': total_fees['total'] or 0,
            'paid': total_fees['paid'] or 0,
            'balance': (total_fees['total'] or 0) - (total_fees['paid'] or 0)
        }
    except:
        pass

    # Get upcoming events
    upcoming_events = []
    try:
        from events.models import Event
        upcoming_events = Event.objects.filter(
            tenant=request.tenant,
            start_date__gte=timezone.now(),
            target_audience__in=['all', 'parents']
        ).order_by('start_date')[:5]
    except:
        pass

    # Get disciplinary actions (if any)
    disciplinary_actions = []
    try:
        from discipline.models import DisciplinaryAction
        disciplinary_actions = DisciplinaryAction.objects.filter(
            tenant=request.tenant,
            student=student.student
        ).order_by('-incident_date')[:5]
    except:
        pass

    context = {
        'title': 'Parent Dashboard',
        'parent': parent,
        'student': student,
        'recent_grades': recent_grades,
        'gpa': round(gpa, 2),
        'attendance_summary': attendance_summary,
        'payment_status': payment_status,
        'upcoming_events': upcoming_events,
        'disciplinary_actions': disciplinary_actions,
        'current_session': current_session,
        'current_semester': current_semester,
    }

    return render(request, 'accounts/dashboard_parent.html', context)


@login_required
@professor_only
def dashboard_professor(request):
    """Professor dashboard with teaching information."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    # Get professor's courses
    my_courses = Course.objects.filter(
        allocated_course__lecturer=request.user,
        semester=current_semester
    ).distinct()

    # Get pending grade entries
    pending_grades = TakenCourse.objects.filter(
        course__allocated_course__lecturer=request.user,
        total__isnull=True
    ).count()

    # Get pending notes approval
    pending_notes = 0
    try:
        from notes.models import ProfessorNote
        pending_notes = ProfessorNote.objects.filter(
            professor=request.user,
            status='pending'
        ).count()
    except:
        pass

    # Get today's classes
    today_classes = []
    try:
        from course.models import Timetable
        today = timezone.now().strftime('%A')
        today_classes = Timetable.objects.filter(
            course__in=my_courses,
            day=today
        ).select_related('course')
    except:
        pass

    # Get attendance summary for today
    today_attendance = {}
    try:
        from attendance.models import AttendanceRecord
        today_date = timezone.now().date()
        total_students = Student.objects.filter(
            takencourse__course__in=my_courses
        ).distinct().count()
        marked_attendance = AttendanceRecord.objects.filter(
            course__in=my_courses,
            date=today_date
        ).count()
        today_attendance = {
            'total': total_students,
            'marked': marked_attendance,
            'pending': total_students - marked_attendance
        }
    except:
        pass

    # Get student count
    student_count = Student.objects.filter(
        takencourse__course__in=my_courses
    ).distinct().count()

    context = {
        'title': 'Professor Dashboard',
        'my_courses': my_courses,
        'student_count': student_count,
        'pending_grades': pending_grades,
        'pending_notes': pending_notes,
        'today_classes': today_classes,
        'today_attendance': today_attendance,
        'current_session': current_session,
        'current_semester': current_semester,
    }

    return render(request, 'accounts/dashboard_professor.html', context)


@login_required
@direction_only
def dashboard_direction(request):
    """Direction dashboard with school-wide statistics and management."""
    current_session = Session.objects.filter(is_current_session=True).first()
    current_semester = Semester.objects.filter(
        is_current_semester=True, session=current_session
    ).first()

    # Student statistics
    total_students = Student.objects.filter(student__tenant=request.tenant).count()
    total_professors = User.objects.filter(
        tenant=request.tenant,
        is_lecturer=True
    ).count()
    total_staff = User.objects.filter(
        tenant=request.tenant,
        is_staff=True
    ).count()

    # Gender distribution
    gender_stats = Student.objects.filter(
        student__tenant=request.tenant
    ).values('student__gender').annotate(count=Count('id'))

    # Enrollment by level
    level_stats = Student.objects.filter(
        student__tenant=request.tenant
    ).values('level').annotate(count=Count('id'))

    # Pending enrollments
    pending_enrollments = 0
    try:
        from enrollment.models import RegistrationForm
        pending_enrollments = RegistrationForm.objects.filter(
            tenant=request.tenant,
            status='pending'
        ).count()
    except:
        pass

    # Pending note approvals
    pending_notes = 0
    try:
        from notes.models import ProfessorNote
        pending_notes = ProfessorNote.objects.filter(
            tenant=request.tenant,
            status='pending'
        ).count()
    except:
        pass

    # Recent disciplinary actions
    recent_disciplinary = []
    try:
        from discipline.models import DisciplinaryAction
        recent_disciplinary = DisciplinaryAction.objects.filter(
            tenant=request.tenant
        ).order_by('-created_at')[:5]
    except:
        pass

    # Payment collection status
    payment_stats = {}
    try:
        from payments.models import PaymentRecord
        payment_summary = PaymentRecord.objects.filter(
            tenant=request.tenant,
            session=current_session
        ).aggregate(
            total=models.Sum('amount'),
            collected=models.Sum('amount', filter=Q(status='paid')),
            pending=models.Sum('amount', filter=Q(status='pending'))
        )
        payment_stats = {
            'total': payment_summary['total'] or 0,
            'collected': payment_summary['collected'] or 0,
            'pending': payment_summary['pending'] or 0,
            'percentage': round((payment_summary['collected'] or 0) / (payment_summary['total'] or 1) * 100, 2)
        }
    except:
        pass

    # Library statistics
    library_stats = {}
    try:
        from library.models import BorrowRecord
        library_stats = {
            'borrowed': BorrowRecord.objects.filter(
                tenant=request.tenant,
                status='borrowed'
            ).count(),
            'overdue': BorrowRecord.objects.filter(
                tenant=request.tenant,
                status='overdue'
            ).count()
        }
    except:
        pass

    # Upcoming events
    upcoming_events = []
    try:
        from events.models import Event
        upcoming_events = Event.objects.filter(
            tenant=request.tenant,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:5]
    except:
        pass

    # Recent activity logs
    recent_activities = []
    try:
        from core.models import ActivityLog
        recent_activities = ActivityLog.objects.filter(
            tenant=request.tenant
        ).order_by('-timestamp')[:10]
    except:
        pass

    context = {
        'title': 'Direction Dashboard',
        'total_students': total_students,
        'total_professors': total_professors,
        'total_staff': total_staff,
        'gender_stats': gender_stats,
        'level_stats': level_stats,
        'pending_enrollments': pending_enrollments,
        'pending_notes': pending_notes,
        'recent_disciplinary': recent_disciplinary,
        'payment_stats': payment_stats,
        'library_stats': library_stats,
        'upcoming_events': upcoming_events,
        'recent_activities': recent_activities,
        'current_session': current_session,
        'current_semester': current_semester,
    }

    return render(request, 'accounts/dashboard_direction.html', context)
