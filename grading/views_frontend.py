"""
Grading Frontend Views - Template-based HTML views.

This module provides frontend views for:
- Grading rubric management (create, edit, list, delete)
- Rubric criteria management
- Grade entry for student submissions
- Student gradebook views
- Peer review system
- Grade curve management

All views render HTML templates.
Frontend URL namespace: frontend:grading:view_name
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from accounts.decorators import lecturer_required, direction_only, tenant_required
from decimal import Decimal

from .models import (
    GradingRubric, RubricCriterion, RubricGrade, CriterionGrade,
    PeerReview, GradeCurve
)
from .forms import (
    GradingRubricForm, RubricCriterionForm, RubricGradeForm,
    CriterionGradeFormSet, PeerReviewForm, GradeCurveForm
)


# ============================================================================
# RUBRIC MANAGEMENT VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def rubric_list(request):
    """
    List all grading rubrics.
    Lecturers can see their own rubrics.
    Direction can see all rubrics.
    """
    if request.user.role in ('secretary', 'direction', 'admin'):
        rubrics = GradingRubric.objects.select_related('course', 'created_by').prefetch_related('criteria').all()
    else:
        rubrics = GradingRubric.objects.filter(created_by=request.user).select_related('course').prefetch_related('criteria')

    # Filtering
    course_id = request.GET.get('course')
    if course_id:
        rubrics = rubrics.filter(course_id=course_id)

    is_active = request.GET.get('is_active')
    if is_active:
        rubrics = rubrics.filter(is_active=(is_active == 'true'))

    # Pagination
    paginator = Paginator(rubrics, 20)
    page_num = request.GET.get('page', 1)
    rubrics_page = paginator.get_page(page_num)

    context = {
        'rubrics': rubrics_page,
        'total_count': paginator.count,
        'title': _('Grading Rubrics'),
        'meta_description': _('Manage grading rubrics for assignments'),
    }

    return render(request, 'grading/rubric_list.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def rubric_detail(request, pk):
    """
    Display rubric details with all criteria.
    """
    rubric = get_object_or_404(
        GradingRubric.objects.select_related('course', 'created_by').prefetch_related('criteria'),
        pk=pk
    )

    # Check permissions
    if request.user.role != 'direction' and rubric.created_by != request.user:
        messages.error(request, _('You do not have permission to view this rubric.'))
        return redirect('frontend:grading:rubric_list')

    # Get usage statistics
    total_grades = rubric.grades.count()
    avg_score = rubric.grades.aggregate(Avg('total_score'))['total_score__avg'] or 0

    context = {
        'rubric': rubric,
        'total_grades': total_grades,
        'avg_score': avg_score,
        'title': rubric.name,
    }

    return render(request, 'grading/rubric_detail.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def rubric_create(request):
    """
    Create new grading rubric.
    """
    if request.method == 'POST':
        form = GradingRubricForm(request.POST, user=request.user)
        if form.is_valid():
            rubric = form.save(commit=False)
            rubric.created_by = request.user
            rubric.save()
            messages.success(request, _('Rubric created successfully.'))
            return redirect('frontend:grading:rubric_detail', pk=rubric.pk)
    else:
        form = GradingRubricForm(user=request.user)

    context = {
        'form': form,
        'title': _('Create Grading Rubric'),
    }

    return render(request, 'grading/rubric_form.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def rubric_update(request, pk):
    """
    Update existing rubric.
    """
    rubric = get_object_or_404(GradingRubric, pk=pk)

    # Check permissions
    if request.user.role != 'direction' and rubric.created_by != request.user:
        messages.error(request, _('You do not have permission to edit this rubric.'))
        return redirect('frontend:grading:rubric_list')

    if request.method == 'POST':
        form = GradingRubricForm(request.POST, instance=rubric, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Rubric updated successfully.'))
            return redirect('frontend:grading:rubric_detail', pk=rubric.pk)
    else:
        form = GradingRubricForm(instance=rubric, user=request.user)

    context = {
        'form': form,
        'rubric': rubric,
        'title': _('Edit Rubric'),
    }

    return render(request, 'grading/rubric_form.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def rubric_delete(request, pk):
    """
    Delete rubric.
    """
    rubric = get_object_or_404(GradingRubric, pk=pk)

    # Check permissions
    if request.user.role != 'direction' and rubric.created_by != request.user:
        messages.error(request, _('You do not have permission to delete this rubric.'))
        return redirect('frontend:grading:rubric_list')

    if request.method == 'POST':
        rubric.delete()
        messages.success(request, _('Rubric deleted successfully.'))
        return redirect('frontend:grading:rubric_list')

    context = {
        'rubric': rubric,
        'title': _('Delete Rubric'),
    }

    return render(request, 'grading/rubric_confirm_delete.html', context)


# ============================================================================
# RUBRIC CRITERIA VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def criterion_create(request, rubric_pk):
    """
    Add criterion to rubric.
    """
    rubric = get_object_or_404(GradingRubric, pk=rubric_pk)

    # Check permissions
    if request.user.role != 'direction' and rubric.created_by != request.user:
        messages.error(request, _('You do not have permission to modify this rubric.'))
        return redirect('frontend:grading:rubric_detail', pk=rubric.pk)

    if request.method == 'POST':
        form = RubricCriterionForm(request.POST)
        if form.is_valid():
            criterion = form.save(commit=False)
            criterion.rubric = rubric
            criterion.save()
            messages.success(request, _('Criterion added successfully.'))
            return redirect('frontend:grading:rubric_detail', pk=rubric.pk)
    else:
        form = RubricCriterionForm()

    context = {
        'form': form,
        'rubric': rubric,
        'title': _('Add Criterion'),
    }

    return render(request, 'grading/criterion_form.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def criterion_update(request, pk):
    """
    Update criterion.
    """
    criterion = get_object_or_404(RubricCriterion.objects.select_related('rubric'), pk=pk)
    rubric = criterion.rubric

    # Check permissions
    if request.user.role != 'direction' and rubric.created_by != request.user:
        messages.error(request, _('You do not have permission to modify this criterion.'))
        return redirect('frontend:grading:rubric_detail', pk=rubric.pk)

    if request.method == 'POST':
        form = RubricCriterionForm(request.POST, instance=criterion)
        if form.is_valid():
            form.save()
            messages.success(request, _('Criterion updated successfully.'))
            return redirect('frontend:grading:rubric_detail', pk=rubric.pk)
    else:
        form = RubricCriterionForm(instance=criterion)

    context = {
        'form': form,
        'criterion': criterion,
        'rubric': rubric,
        'title': _('Edit Criterion'),
    }

    return render(request, 'grading/criterion_form.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def criterion_delete(request, pk):
    """
    Delete criterion.
    """
    criterion = get_object_or_404(RubricCriterion.objects.select_related('rubric'), pk=pk)
    rubric = criterion.rubric

    # Check permissions
    if request.user.role != 'direction' and rubric.created_by != request.user:
        messages.error(request, _('You do not have permission to delete this criterion.'))
        return redirect('frontend:grading:rubric_detail', pk=rubric.pk)

    if request.method == 'POST':
        criterion.delete()
        messages.success(request, _('Criterion deleted successfully.'))
        return redirect('frontend:grading:rubric_detail', pk=rubric.pk)

    context = {
        'criterion': criterion,
        'rubric': rubric,
        'title': _('Delete Criterion'),
    }

    return render(request, 'grading/criterion_confirm_delete.html', context)


# ============================================================================
# GRADE ENTRY VIEWS
# ============================================================================

@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_entry_list(request):
    """
    List all grade entries.
    Lecturers see their own grades.
    """
    if request.user.role in ('secretary', 'direction', 'admin'):
        grades = RubricGrade.objects.select_related('rubric', 'student', 'graded_by').prefetch_related('criterion_grades').all()
    else:
        grades = RubricGrade.objects.filter(graded_by=request.user).select_related('rubric', 'student').prefetch_related('criterion_grades')

    # Filtering
    rubric_id = request.GET.get('rubric')
    if rubric_id:
        grades = grades.filter(rubric_id=rubric_id)

    student_id = request.GET.get('student')
    if student_id:
        grades = grades.filter(student_id=student_id)

    # Pagination
    paginator = Paginator(grades, 50)
    page_num = request.GET.get('page', 1)
    grades_page = paginator.get_page(page_num)

    context = {
        'grades': grades_page,
        'total_count': paginator.count,
        'title': _('Grade Entries'),
    }

    return render(request, 'grading/grade_entry_list.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_entry_create(request, rubric_pk=None, student_id=None):
    """
    Create new grade entry using rubric.
    """
    rubric = None
    if rubric_pk:
        rubric = get_object_or_404(GradingRubric.objects.prefetch_related('criteria'), pk=rubric_pk)

    if request.method == 'POST':
        form = RubricGradeForm(request.POST, rubric=rubric, user=request.user)
        formset = CriterionGradeFormSet(request.POST, rubric=rubric)

        if form.is_valid() and formset.is_valid():
            grade = form.save(commit=False)
            grade.graded_by = request.user
            grade.save()

            # Save criterion grades
            for criterion_form in formset:
                if criterion_form.cleaned_data:
                    criterion_grade = criterion_form.save(commit=False)
                    criterion_grade.rubric_grade = grade
                    criterion_grade.save()

            # Calculate total score
            grade.calculate_grade()

            messages.success(request, _('Grade saved successfully.'))
            return redirect('frontend:grading:grade_entry_detail', pk=grade.pk)
    else:
        initial = {}
        if student_id:
            initial['student'] = student_id
        form = RubricGradeForm(initial=initial, rubric=rubric, user=request.user)
        formset = CriterionGradeFormSet(rubric=rubric)

    context = {
        'form': form,
        'formset': formset,
        'rubric': rubric,
        'title': _('Enter Grade'),
    }

    return render(request, 'grading/grade_entry_form.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_entry_detail(request, pk):
    """
    Display grade entry details.
    Students can view their own grades.
    Lecturers can view grades they assigned.
    Permission check is done via queryset filtering BEFORE fetch.
    """
    base_qs = RubricGrade.objects.select_related(
        'rubric', 'student', 'graded_by'
    ).prefetch_related('criterion_grades__criterion')

    # Filter by role before fetching - prevents IDOR
    if request.user.role == 'student':
        base_qs = base_qs.filter(student__student=request.user)
    elif request.user.role in ('lecturer', 'professor'):
        base_qs = base_qs.filter(graded_by=request.user)
    elif request.user.role not in ('secretary', 'direction', 'admin') and not request.user.is_superuser:
        base_qs = base_qs.none()

    grade = get_object_or_404(base_qs, pk=pk)

    context = {
        'grade': grade,
        'title': _('Grade Details'),
    }

    return render(request, 'grading/grade_entry_detail.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_entry_edit(request, pk):
    """
    Edit an existing grade entry.
    Lecturers can only edit grades they assigned.
    Direction can edit any grade.
    Permission check is done via queryset filtering BEFORE fetch.
    """
    base_qs = RubricGrade.objects.select_related('rubric', 'student', 'graded_by')

    # Filter by role before fetching - prevents IDOR
    if request.user.role not in ('direction', 'admin') and not request.user.is_superuser:
        base_qs = base_qs.filter(graded_by=request.user)

    grade = get_object_or_404(base_qs, pk=pk)

    rubric = grade.rubric

    if request.method == 'POST':
        form = RubricGradeForm(request.POST, instance=grade, rubric=rubric, user=request.user)
        formset = CriterionGradeFormSet(request.POST, rubric=rubric)

        if form.is_valid() and formset.is_valid():
            grade = form.save()

            # Update criterion grades
            # Remove existing criterion grades and re-create
            grade.criterion_grades.all().delete()
            for criterion_form in formset:
                if criterion_form.cleaned_data:
                    criterion_grade = criterion_form.save(commit=False)
                    criterion_grade.rubric_grade = grade
                    criterion_grade.save()

            # Recalculate total score
            grade.calculate_grade()

            messages.success(request, _('Grade updated successfully.'))
            return redirect('frontend:grading:grade_entry_detail', pk=grade.pk)
    else:
        form = RubricGradeForm(instance=grade, rubric=rubric, user=request.user)
        formset = CriterionGradeFormSet(rubric=rubric)

    context = {
        'form': form,
        'formset': formset,
        'grade': grade,
        'rubric': rubric,
        'title': _('Edit Grade Entry'),
    }

    return render(request, 'grading/grade_entry_form.html', context)


@login_required
@lecturer_required
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def grade_entry_delete(request, pk):
    """
    Delete a grade entry.
    Lecturers can only delete grades they assigned.
    Direction can delete any grade. GET shows confirmation, POST deletes.
    """
    # Filter by role before fetching - prevents IDOR
    base_qs = RubricGrade.objects.select_related('rubric', 'student', 'graded_by')
    if request.user.role not in ('direction', 'admin') and not request.user.is_superuser:
        base_qs = base_qs.filter(graded_by=request.user)

    grade = get_object_or_404(base_qs, pk=pk)

    if request.method == 'POST':
        grade.delete()
        messages.success(request, _('Grade entry deleted successfully.'))
        return redirect('frontend:grading:grade_entry_list')

    context = {
        'grade': grade,
        'title': _('Delete Grade Entry'),
    }

    return render(request, 'grading/grade_entry_confirm_delete.html', context)


# ============================================================================
# STUDENT GRADEBOOK VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def student_gradebook(request, student_id=None):
    """
    Display student gradebook.
    Students see their own grades.
    Lecturers and direction can view any student.
    """
    if request.user.role == 'student':
        from accounts.models import Student
        student = get_object_or_404(Student, student=request.user)
        grades = RubricGrade.objects.filter(student=student).select_related('rubric', 'graded_by').prefetch_related('criterion_grades')
    else:
        if student_id:
            from accounts.models import Student
            student = get_object_or_404(Student, pk=student_id)
            grades = RubricGrade.objects.filter(student=student).select_related('rubric', 'graded_by').prefetch_related('criterion_grades')
        else:
            messages.error(request, _('Student ID is required.'))
            return redirect('frontend:grading:grade_entry_list')

    # Calculate statistics
    total_grades = grades.count()
    avg_percentage = grades.aggregate(Avg('percentage'))['percentage__avg'] or 0

    context = {
        'student': student,
        'grades': grades,
        'total_grades': total_grades,
        'avg_percentage': avg_percentage,
        'title': _('Student Gradebook'),
    }

    return render(request, 'grading/student_gradebook.html', context)


# ============================================================================
# PEER REVIEW VIEWS
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def peer_review_list(request):
    """
    List peer reviews.
    Students see reviews they need to complete and reviews of their work.
    Lecturers see all reviews for their courses.
    """
    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)
        # Reviews to complete
        pending_reviews = PeerReview.objects.filter(
            reviewer=student,
            status__in=['pending', 'in_progress']
        ).select_related('reviewee', 'course')

        # Reviews received
        received_reviews = PeerReview.objects.filter(
            reviewee=student,
            status='completed'
        ).select_related('reviewer', 'course')

        context = {
            'pending_reviews': pending_reviews,
            'received_reviews': received_reviews,
            'title': _('Peer Reviews'),
        }
        return render(request, 'grading/peer_review_student_list.html', context)

    else:
        # Lecturers and direction see all reviews
        reviews = PeerReview.objects.select_related('reviewer', 'reviewee', 'course').all()

        # Filtering
        status_filter = request.GET.get('status')
        if status_filter:
            reviews = reviews.filter(status=status_filter)

        course_id = request.GET.get('course')
        if course_id:
            reviews = reviews.filter(course_id=course_id)

        # Pagination
        paginator = Paginator(reviews, 50)
        page_num = request.GET.get('page', 1)
        reviews_page = paginator.get_page(page_num)

        context = {
            'reviews': reviews_page,
            'total_count': paginator.count,
            'title': _('Peer Reviews'),
        }
        return render(request, 'grading/peer_review_list.html', context)


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def peer_review_submit(request, pk):
    """
    Submit peer review.
    """
    review = get_object_or_404(PeerReview.objects.select_related('reviewer', 'reviewee', 'course'), pk=pk)

    # Check permissions
    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)
        if review.reviewer != student:
            messages.error(request, _('You do not have permission to submit this review.'))
            return redirect('frontend:grading:peer_review_list')

    if review.status not in ['pending', 'in_progress']:
        messages.error(request, _('This review has already been submitted.'))
        return redirect('frontend:grading:peer_review_list')

    if request.method == 'POST':
        form = PeerReviewForm(request.POST, instance=review)
        if form.is_valid():
            peer_review = form.save(commit=False)
            peer_review.status = 'completed'
            peer_review.submitted_at = timezone.now()
            peer_review.save()
            messages.success(request, _('Peer review submitted successfully.'))
            return redirect('frontend:grading:peer_review_list')
    else:
        form = PeerReviewForm(instance=review)

    context = {
        'form': form,
        'review': review,
        'title': _('Submit Peer Review'),
    }

    return render(request, 'grading/peer_review_form.html', context)


# ============================================================================
# GRADE CURVE VIEWS
# ============================================================================

@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_curve_list(request):
    """
    List all grade curves.
    Direction only.
    """
    curves = GradeCurve.objects.select_related('course', 'applied_by').all()

    # Filtering
    course_id = request.GET.get('course')
    if course_id:
        curves = curves.filter(course_id=course_id)

    # Pagination
    paginator = Paginator(curves, 20)
    page_num = request.GET.get('page', 1)
    curves_page = paginator.get_page(page_num)

    context = {
        'curves': curves_page,
        'total_count': paginator.count,
        'title': _('Grade Curves'),
    }

    return render(request, 'grading/grade_curve_list.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_curve_create(request):
    """
    Apply grade curve.
    Direction only.
    """
    if request.method == 'POST':
        form = GradeCurveForm(request.POST)
        if form.is_valid():
            curve = form.save(commit=False)
            curve.applied_by = request.user
            curve.save()
            messages.success(request, _('Grade curve applied successfully.'))
            return redirect('frontend:grading:grade_curve_list')
    else:
        form = GradeCurveForm()

    context = {
        'form': form,
        'title': _('Apply Grade Curve'),
    }

    return render(request, 'grading/grade_curve_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_curve_detail(request, pk):
    """
    Display grade curve details.
    Direction only.
    """
    curve = get_object_or_404(GradeCurve.objects.select_related('course', 'applied_by'), pk=pk)

    context = {
        'curve': curve,
        'title': _('Grade Curve Details'),
    }

    return render(request, 'grading/grade_curve_detail.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def grade_curve_edit(request, pk):
    """
    Edit an existing grade curve.
    Direction only.
    """
    curve = get_object_or_404(GradeCurve, pk=pk)

    if request.method == 'POST':
        form = GradeCurveForm(request.POST, instance=curve)
        if form.is_valid():
            form.save()
            messages.success(request, _('Grade curve updated successfully.'))
            return redirect('frontend:grading:grade_curve_detail', pk=curve.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = GradeCurveForm(instance=curve)

    context = {
        'form': form,
        'curve': curve,
        'title': _('Edit Grade Curve'),
    }

    return render(request, 'grading/grade_curve_form.html', context)


@login_required
@direction_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def grade_curve_delete(request, pk):
    """
    Delete a grade curve.
    Direction only. GET shows confirmation, POST deletes.
    """
    curve = get_object_or_404(GradeCurve.objects.select_related('course', 'applied_by'), pk=pk)

    if request.method == 'POST':
        curve.delete()
        messages.success(request, _('Grade curve deleted successfully.'))
        return redirect('frontend:grading:grade_curve_list')

    context = {
        'curve': curve,
        'title': _('Delete Grade Curve'),
    }

    return render(request, 'grading/grade_curve_confirm_delete.html', context)


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def grading_dashboard(request):
    """
    Grading dashboard.
    Shows different information based on user role.
    """
    context = {
        'title': _('Grading Dashboard'),
    }

    if request.user.role == 'student':
        from accounts.models import Student
        student = Student.objects.get(student=request.user)

        # Recent grades
        recent_grades = RubricGrade.objects.filter(student=student).select_related('rubric', 'graded_by').order_by('-graded_at')[:5]

        # Pending peer reviews
        pending_reviews = PeerReview.objects.filter(
            reviewer=student,
            status__in=['pending', 'in_progress']
        ).count()

        context.update({
            'recent_grades': recent_grades,
            'pending_reviews': pending_reviews,
        })

    elif request.user.role == 'lecturer':
        # Recent grading activity
        recent_grades = RubricGrade.objects.filter(graded_by=request.user).select_related('rubric', 'student').order_by('-graded_at')[:10]

        # Active rubrics
        active_rubrics = GradingRubric.objects.filter(created_by=request.user, is_active=True).count()

        context.update({
            'recent_grades': recent_grades,
            'active_rubrics': active_rubrics,
        })

    else:  # direction
        # System-wide statistics
        total_rubrics = GradingRubric.objects.count()
        total_grades = RubricGrade.objects.count()
        pending_peer_reviews = PeerReview.objects.filter(status__in=['pending', 'in_progress']).count()
        applied_curves = GradeCurve.objects.filter(is_active=True).count()

        context.update({
            'total_rubrics': total_rubrics,
            'total_grades': total_grades,
            'pending_peer_reviews': pending_peer_reviews,
            'applied_curves': applied_curves,
        })

    return render(request, 'grading/dashboard.html', context)
