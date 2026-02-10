from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template, render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView
from xhtml2pdf import pisa

from accounts.decorators import admin_required, role_required
from accounts.filters import LecturerFilter, StudentFilter
from accounts.forms import (
    ForcePasswordResetForm,
    InvitationCodeForm,
    ParentAddForm,
    ParentInvitationSignupForm,
    ProfileUpdateForm,
    ProgramUpdateForm,
    StaffAddForm,
    StaffInvitationSignupForm,
    StudentActivationForm,
    StudentAddForm,
    StudentSetPasswordForm,
    StudentVerifyParentForm,
)
from accounts.models import InvitationCode, Parent, Student, User
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


@login_required
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
            return redirect("frontend:accounts:login")
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
        return redirect("frontend:accounts:profile")

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
            return redirect("frontend:accounts:profile")
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
            return redirect("frontend:accounts:profile")
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
            return redirect("frontend:accounts:lecturer_list")
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
            return redirect("frontend:accounts:lecturer_list")
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
    return redirect("frontend:accounts:lecturer_list")


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
            return redirect("frontend:accounts:student_list")
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
            return redirect("frontend:accounts:student_list")
        messages.error(request, "Please correct the error below.")
    else:
        form = ProfileUpdateForm(instance=student_user)
    return render(
        request, "accounts/edit_student.html", {"title": "Edit Student", "form": form}
    )


@method_decorator([login_required, role_required('admin', 'direction', 'secretary', 'prefet', 'accountant')], name="dispatch")
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
    return redirect("frontend:accounts:student_list")


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


@login_required
@admin_required
def parent_list(request):
    """List all parents with related student and user info."""
    parents = Parent.objects.select_related('student', 'user').all()
    paginator = Paginator(parents, 20)
    page_num = request.GET.get('page', 1)
    parents_page = paginator.get_page(page_num)
    return render(request, "accounts/parent_list.html", {
        "title": "Parents",
        "parents": parents_page,
    })


@login_required
@admin_required
def parent_detail(request, pk):
    """Show single parent with related student info."""
    parent = get_object_or_404(
        Parent.objects.select_related('student', 'user'),
        pk=pk
    )
    return render(request, "accounts/parent_detail.html", {
        "title": f"Parent: {parent.first_name} {parent.last_name}",
        "parent": parent,
    })


@login_required
@admin_required
def parent_edit(request, pk):
    """Edit parent using ParentAddForm with instance."""
    parent = get_object_or_404(Parent, pk=pk)
    user = parent.user
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Parent {parent.first_name} {parent.last_name} has been updated.")
            return redirect("frontend:accounts:parent_detail", pk=parent.pk)
        messages.error(request, "Please correct the error(s) below.")
    else:
        form = ProfileUpdateForm(instance=user)
    return render(request, "accounts/parent_form.html", {
        "title": "Edit Parent",
        "form": form,
        "parent": parent,
    })


@login_required
@admin_required
def parent_delete(request, pk):
    """Delete parent with GET confirmation and POST action."""
    parent = get_object_or_404(Parent, pk=pk)
    if request.method == "POST":
        name = f"{parent.first_name} {parent.last_name}"
        parent.delete()
        messages.success(request, f"Parent {name} has been deleted.")
        return redirect("frontend:accounts:parent_list")
    return render(request, "accounts/confirm_delete.html", {
        "title": "Delete Parent",
        "object": parent,
        "object_name": f"{parent.first_name} {parent.last_name}",
        "cancel_url": "frontend:accounts:parent_list",
    })


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


# ########################################################
# Two-Factor Authentication (2FA) Views
# ########################################################


@login_required
def setup_2fa(request):
    """
    Setup TOTP-based Two-Factor Authentication for users.
    Generates QR code for authenticator app scanning.
    """
    from django_otp import user_has_device
    from django_otp.plugins.otp_totp.models import TOTPDevice
    import qrcode
    import io
    import base64

    user = request.user

    # Check if user already has 2FA enabled
    if user_has_device(user):
        messages.info(request, "Two-Factor Authentication is already enabled for your account.")
        return redirect('frontend:accounts:profile')

    if request.method == 'POST':
        token = request.POST.get('token')
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()

        if device and device.verify_token(token):
            device.confirmed = True
            device.save()
            messages.success(request, "Two-Factor Authentication has been enabled successfully!")

            # Send email notification
            try:
                from accounts.email_utils import send_2fa_enabled_email
                send_2fa_enabled_email(user, request.tenant)
            except Exception as e:
                logger.error(f"Failed to send 2FA enabled email: {str(e)}")

            return redirect('frontend:accounts:profile')
        else:
            messages.error(request, "Invalid verification code. Please try again.")

    # Create or get unconfirmed device
    device, created = TOTPDevice.objects.get_or_create(
        user=user,
        confirmed=False,
        defaults={'name': 'default'}
    )

    # Generate QR code
    otpauth_url = device.config_url
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otpauth_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'title': 'Setup Two-Factor Authentication',
        'device': device,
        'qr_code': qr_code_data,
        'secret_key': device.key,
    }

    return render(request, 'auth/2fa/setup.html', context)


@login_required
def disable_2fa(request):
    """
    Disable Two-Factor Authentication for the user.
    Requires confirmation before disabling.
    """
    from django_otp.plugins.otp_totp.models import TOTPDevice
    from django_otp import user_has_device

    if not user_has_device(request.user):
        messages.info(request, "Two-Factor Authentication is not enabled for your account.")
        return redirect('frontend:accounts:profile')

    if request.method == 'POST':
        # Require password confirmation
        password = request.POST.get('password')

        if request.user.check_password(password):
            TOTPDevice.objects.filter(user=request.user).delete()
            messages.success(request, "Two-Factor Authentication has been disabled successfully.")

            # Send email notification
            try:
                from accounts.email_utils import send_2fa_disabled_email
                send_2fa_disabled_email(request.user, request.tenant)
            except Exception as e:
                logger.error(f"Failed to send 2FA disabled email: {str(e)}")

            return redirect('frontend:accounts:profile')
        else:
            messages.error(request, "Incorrect password. Please try again.")

    return render(request, 'auth/2fa/disable.html', {'title': 'Disable Two-Factor Authentication'})


@login_required
def manage_2fa(request):
    """
    Main 2FA management page showing status and options.
    """
    from django_otp import user_has_device
    from django_otp.plugins.otp_totp.models import TOTPDevice

    has_2fa = user_has_device(request.user)
    devices = TOTPDevice.objects.filter(user=request.user, confirmed=True)

    context = {
        'title': 'Two-Factor Authentication',
        'has_2fa': has_2fa,
        'devices': devices,
    }

    return render(request, 'auth/2fa/manage.html', context)


# ########################################################
# Signup Flow Views
# ########################################################

import random
import logging
from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.db import transaction

logger = logging.getLogger(__name__)


def signup_hub(request):
    """Main signup page with role selection cards."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")
    return render(request, "account/signup.html", {"title": "Create Your Account"})


def student_activate(request):
    """Step 1: Student enters registration number + name."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    if request.method == "POST":
        form = StudentActivationForm(request.POST)
        if form.is_valid():
            student = form.student

            # Generate 6-digit verification code
            code = f"{random.randint(0, 999999):06d}"

            # Store in session with timestamp for expiry
            request.session["activation_student_id"] = student.pk
            request.session["activation_code"] = code
            request.session["activation_attempts"] = 0
            request.session["activation_timestamp"] = timezone.now().isoformat()

            # Send code to parent(s) email
            parents = Parent.objects.filter(student=student)
            parent_emails = [p.email for p in parents if p.email]
            parent_emails += [p.user.email for p in parents if p.user and p.user.email]
            parent_emails = list(set(filter(None, parent_emails)))

            if not parent_emails:
                messages.error(
                    request,
                    "No parent/guardian email on file. "
                    "Please contact the school administration to complete your registration.",
                )
                return render(request, "account/student_activate.html", {
                    "form": form, "title": "Activate Student Account",
                })

            try:
                student_name = student.student.get_full_name
                from_email = getattr(
                    django_settings, "EMAIL_FROM_ADDRESS",
                    getattr(django_settings, "DEFAULT_FROM_EMAIL", "noreply@school.local"),
                )
                send_mail(
                    subject="Student Account Verification Code",
                    message=(
                        f"Dear Parent/Guardian,\n\n"
                        f"Your child {student_name} is activating their school account.\n\n"
                        f"Verification Code: {code}\n\n"
                        f"If you did not expect this request, please contact the school "
                        f"administration immediately.\n\n"
                        f"This code expires in 15 minutes."
                    ),
                    from_email=from_email,
                    recipient_list=parent_emails,
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")
                messages.error(
                    request,
                    "Failed to send the verification code. Please try again later.",
                )
                return render(request, "account/student_activate.html", {
                    "form": form, "title": "Activate Student Account",
                })

            messages.success(
                request,
                "A verification code has been sent to your parent/guardian's email.",
            )
            return redirect("frontend:accounts:student_verify_parent")
    else:
        form = StudentActivationForm()

    return render(request, "account/student_activate.html", {
        "form": form, "title": "Activate Student Account",
    })


def student_verify_parent(request):
    """Step 2: Student enters verification code sent to parent's email."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    student_id = request.session.get("activation_student_id")
    stored_code = request.session.get("activation_code")

    if not student_id or not stored_code:
        messages.error(request, "Please start the activation process from the beginning.")
        return redirect("frontend:accounts:student_activate")

    # Check session expiry (15 minutes)
    timestamp_str = request.session.get("activation_timestamp")
    if timestamp_str:
        try:
            created_at = timezone.datetime.fromisoformat(timestamp_str)
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            expiry_minutes = getattr(django_settings, "STUDENT_VERIFICATION_CODE_EXPIRY_MINUTES", 15)
            if timezone.now() > created_at + timedelta(minutes=expiry_minutes):
                for key in [
                    "activation_student_id", "activation_code",
                    "activation_attempts", "activation_verified", "activation_timestamp",
                ]:
                    request.session.pop(key, None)
                messages.error(request, "Your verification code has expired. Please start over.")
                return redirect("frontend:accounts:student_activate")
        except (ValueError, TypeError):
            pass

    if request.method == "POST":
        form = StudentVerifyParentForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data["verification_code"]
            attempts = request.session.get("activation_attempts", 0)
            max_attempts = getattr(django_settings, "STUDENT_VERIFICATION_MAX_ATTEMPTS", 3)

            if entered_code == stored_code:
                request.session["activation_verified"] = True
                return redirect("frontend:accounts:student_set_password")
            else:
                attempts += 1
                request.session["activation_attempts"] = attempts

                if attempts >= max_attempts:
                    for key in [
                        "activation_student_id", "activation_code",
                        "activation_attempts", "activation_verified",
                        "activation_timestamp",
                    ]:
                        request.session.pop(key, None)
                    messages.error(
                        request,
                        "Too many incorrect attempts. Please start the activation process again.",
                    )
                    return redirect("frontend:accounts:student_activate")

                remaining = max_attempts - attempts
                messages.error(
                    request,
                    f"Incorrect verification code. {remaining} attempt(s) remaining.",
                )
    else:
        form = StudentVerifyParentForm()

    return render(request, "account/student_verify_parent.html", {
        "form": form, "title": "Verify Your Identity",
    })


def student_set_password(request):
    """Step 3: Student sets email and password to complete activation."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    student_id = request.session.get("activation_student_id")
    verified = request.session.get("activation_verified")

    if not student_id or not verified:
        messages.error(request, "Please complete the verification step first.")
        return redirect("frontend:accounts:student_activate")

    # Check session expiry (15 minutes)
    timestamp_str = request.session.get("activation_timestamp")
    if timestamp_str:
        try:
            created_at = timezone.datetime.fromisoformat(timestamp_str)
            if timezone.is_naive(created_at):
                created_at = timezone.make_aware(created_at)
            expiry_minutes = getattr(django_settings, "STUDENT_VERIFICATION_CODE_EXPIRY_MINUTES", 15)
            if timezone.now() > created_at + timedelta(minutes=expiry_minutes):
                for key in [
                    "activation_student_id", "activation_code",
                    "activation_attempts", "activation_verified", "activation_timestamp",
                ]:
                    request.session.pop(key, None)
                messages.error(request, "Your session has expired. Please start the activation process again.")
                return redirect("frontend:accounts:student_activate")
        except (ValueError, TypeError):
            pass

    student = get_object_or_404(Student, pk=student_id)
    user = student.student

    if request.method == "POST":
        form = StudentSetPasswordForm(request.POST, user_pk=user.pk)
        if form.is_valid():
            user.email = form.cleaned_data["email"]
            user.set_password(form.cleaned_data["password1"])
            user.is_active = True
            user.must_change_password = False
            user.save()

            # Create allauth EmailAddress if allauth is installed
            try:
                from allauth.account.models import EmailAddress
                EmailAddress.objects.get_or_create(
                    user=user,
                    email=form.cleaned_data["email"],
                    defaults={"verified": True, "primary": True},
                )
            except ImportError:
                pass

            # Clean session
            for key in [
                "activation_student_id", "activation_code",
                "activation_attempts", "activation_verified",
                "activation_timestamp",
            ]:
                request.session.pop(key, None)

            messages.success(
                request,
                "Your account has been activated successfully! You can now sign in.",
            )
            return redirect("account_login")
    else:
        form = StudentSetPasswordForm(user_pk=user.pk)

    return render(request, "account/student_set_password.html", {
        "form": form,
        "title": "Set Your Password",
        "student": student,
        "student_user": user,
    })


def parent_invitation_step1(request):
    """Step 1: Parent enters invitation code."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    if request.method == "POST":
        form = InvitationCodeForm(request.POST)
        if form.is_valid():
            invitation = form.invitation
            if invitation.role != "parent":
                messages.error(request, "This is not a parent invitation code.")
                return render(request, "account/parent_invitation_step1.html", {
                    "form": form, "title": "Parent Registration",
                })
            request.session["invitation_code"] = invitation.code
            return redirect("frontend:accounts:parent_invitation_step2")
    else:
        form = InvitationCodeForm()

    return render(request, "account/parent_invitation_step1.html", {
        "form": form, "title": "Parent Registration",
    })


def parent_invitation_step2(request):
    """Step 2: Parent fills in details after code validation."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    code = request.session.get("invitation_code")
    if not code:
        messages.error(request, "Please enter your invitation code first.")
        return redirect("frontend:accounts:parent_invitation_step1")

    try:
        invitation = InvitationCode.objects.get(code=code)
        if not invitation.is_valid:
            raise InvitationCode.DoesNotExist
    except InvitationCode.DoesNotExist:
        request.session.pop("invitation_code", None)
        messages.error(request, "Invalid or expired invitation code. Please try again.")
        return redirect("frontend:accounts:parent_invitation_step1")

    if request.method == "POST":
        form = ParentInvitationSignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                username = f"parent_{form.cleaned_data['first_name'].lower()}_{User.objects.count()}"
                user = User.objects.create_user(
                    username=username,
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password1"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    phone=form.cleaned_data.get("phone", ""),
                    is_parent=True,
                    role="parent",
                )

                Parent.objects.create(
                    user=user,
                    student=invitation.linked_student,
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    phone=form.cleaned_data.get("phone", ""),
                    email=form.cleaned_data["email"],
                    relation_ship=form.cleaned_data["relation_ship"],
                )

                invitation.redeem(user)

                try:
                    from allauth.account.models import EmailAddress
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=form.cleaned_data["email"],
                        defaults={"verified": True, "primary": True},
                    )
                except ImportError:
                    pass

            request.session.pop("invitation_code", None)
            messages.success(
                request,
                "Your parent account has been created! You can now sign in.",
            )
            return redirect("account_login")
    else:
        form = ParentInvitationSignupForm()

    context = {
        "form": form,
        "title": "Complete Your Registration",
        "invitation": invitation,
    }
    if invitation.linked_student:
        context["linked_student"] = invitation.linked_student

    return render(request, "account/parent_invitation_step2.html", context)


def staff_invitation_step1(request):
    """Step 1: Staff enters invitation code."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    if request.method == "POST":
        form = InvitationCodeForm(request.POST)
        if form.is_valid():
            invitation = form.invitation
            if invitation.role not in ("professor", "direction", "prefet", "accountant", "secretary"):
                messages.error(request, "This is not a staff invitation code.")
                return render(request, "account/staff_invitation_step1.html", {
                    "form": form, "title": "Staff Registration",
                })
            request.session["invitation_code"] = invitation.code
            return redirect("frontend:accounts:staff_invitation_step2")
    else:
        form = InvitationCodeForm()

    return render(request, "account/staff_invitation_step1.html", {
        "form": form, "title": "Staff Registration",
    })


def staff_invitation_step2(request):
    """Step 2: Staff fills in details after code validation."""
    if request.user.is_authenticated:
        return redirect("frontend:accounts:profile")

    code = request.session.get("invitation_code")
    if not code:
        messages.error(request, "Please enter your invitation code first.")
        return redirect("frontend:accounts:staff_invitation_step1")

    try:
        invitation = InvitationCode.objects.get(code=code)
        if not invitation.is_valid:
            raise InvitationCode.DoesNotExist
    except InvitationCode.DoesNotExist:
        request.session.pop("invitation_code", None)
        messages.error(request, "Invalid or expired invitation code. Please try again.")
        return redirect("frontend:accounts:staff_invitation_step1")

    if request.method == "POST":
        form = StaffInvitationSignupForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                username = f"staff_{form.cleaned_data['first_name'].lower()}_{User.objects.count()}"
                user = User.objects.create_user(
                    username=username,
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password1"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    phone=form.cleaned_data.get("phone", ""),
                    role=invitation.role,
                    is_lecturer=(invitation.role == "professor"),
                )

                invitation.redeem(user)

                try:
                    from allauth.account.models import EmailAddress
                    EmailAddress.objects.get_or_create(
                        user=user,
                        email=form.cleaned_data["email"],
                        defaults={"verified": True, "primary": True},
                    )
                except ImportError:
                    pass

            request.session.pop("invitation_code", None)
            role_displays = {"professor": "Professor", "prefet": "Discipline Officer", "accountant": "Accountant", "secretary": "Secretary", "direction": "Direction Staff"}
            role_display = role_displays.get(invitation.role, "Staff")
            messages.success(
                request,
                f"Your {role_display} account has been created! You can now sign in.",
            )
            return redirect("account_login")
    else:
        form = StaffInvitationSignupForm()

    return render(request, "account/staff_invitation_step2.html", {
        "form": form,
        "title": "Complete Your Registration",
        "invitation": invitation,
    })


def force_password_reset(request):
    """Force password reset for users with temporary passwords."""
    if not request.user.is_authenticated:
        return redirect("account_login")

    if not request.user.must_change_password:
        return redirect("frontend:accounts:profile")

    if request.method == "POST":
        form = ForcePasswordResetForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["password1"])
            request.user.must_change_password = False
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Your password has been updated successfully!")
            return redirect("frontend:accounts:profile")
    else:
        form = ForcePasswordResetForm()

    return render(request, "account/force_password_reset.html", {
        "form": form, "title": "Change Your Password",
    })


# ########################################################
# Custom Error Handlers
# ########################################################


def custom_403_view(request, exception=None):
    """
    Custom 403 Forbidden error page.
    """
    context = {
        'title': '403 - Access Forbidden',
        'error_code': '403',
        'error_title': 'Access Forbidden',
        'error_message': 'You do not have permission to access this resource.',
    }
    return render(request, 'errors/403.html', context, status=403)


def custom_404_view(request, exception=None):
    """
    Custom 404 Not Found error page.
    """
    context = {
        'title': '404 - Page Not Found',
        'error_code': '404',
        'error_title': 'Page Not Found',
        'error_message': 'The page you are looking for does not exist or has been moved.',
    }
    return render(request, 'errors/404.html', context, status=404)


def custom_500_view(request):
    """
    Custom 500 Internal Server Error page.
    """
    context = {
        'title': '500 - Server Error',
        'error_code': '500',
        'error_title': 'Internal Server Error',
        'error_message': 'Something went wrong on our end. Our team has been notified and is working on a fix.',
    }
    return render(request, 'errors/500.html', context, status=500)
