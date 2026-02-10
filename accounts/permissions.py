"""
Custom permissions for the accounts app.
"""

from rest_framework import permissions


class IsDirectionUser(permissions.BasePermission):
    """
    Permission to check if user is a direction/admin user.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_superuser or
            getattr(request.user, 'is_direction', False)
        )


class IsLecturerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is a lecturer or admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_lecturer
        )


class IsStudentOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is a student or admin.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_student
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is the object owner or admin.
    """
    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # Check if object has student attribute with user
        if hasattr(obj, 'student') and hasattr(obj.student, 'student'):
            return obj.student.student == request.user

        return False


class IsLecturerUser(permissions.BasePermission):
    """
    Permission to check if user is a lecturer.
    Alias for IsLecturerOrAdmin for backward compatibility.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_lecturer
        )


class IsProfessorUser(permissions.BasePermission):
    """
    Permission to check if user is a professor/lecturer.
    Alias for IsLecturerUser.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            request.user.is_lecturer or
            getattr(request.user, 'is_professor', False)
        )


class IsParentUser(permissions.BasePermission):
    """
    Permission to check if user is a parent.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or
            getattr(request.user, 'is_parent', False) or
            getattr(request.user, 'role', '') == 'parent'
        )


class IsStudentOrParent(permissions.BasePermission):
    """
    Permission for views accessible to students and parents (e.g., invoices).
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return (
            getattr(request.user, 'is_student', False) or
            getattr(request.user, 'is_parent', False)
        )
