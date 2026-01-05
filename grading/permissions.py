"""
Permissions for grading app.
"""

from rest_framework import permissions


class CanCreateRubrics(permissions.BasePermission):
    """
    Only instructors and staff can create rubrics.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_teacher))


class CanGradeSubmissions(permissions.BasePermission):
    """
    Only instructors and staff can grade submissions.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_teacher))


class CanApplyCurves(permissions.BasePermission):
    """
    Only instructors and staff can apply grade curves.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_teacher))


class IsReviewerOrReadOnly(permissions.BasePermission):
    """
    Reviewers can edit their own reviews.
    Others can only read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Only the reviewer can edit
        return obj.reviewer.student == request.user


class CanViewGrades(permissions.BasePermission):
    """
    Students can view their own grades.
    Instructors and staff can view all grades.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff and instructors can view all
        if request.user.is_staff or request.user.is_teacher:
            return True

        # Students can only view their own grades
        return obj.student.student == request.user


class CanManageRubric(permissions.BasePermission):
    """
    Only rubric creator or staff can manage rubric.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Creator or staff can modify
        return obj.created_by == request.user or request.user.is_staff
