"""
Permissions for certificates app.
"""

from rest_framework import permissions


class CanIssueCertificates(permissions.BasePermission):
    """
    Only staff members can issue certificates.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class CanVerifyCertificates(permissions.BasePermission):
    """
    Anyone can verify certificates (public endpoint).
    """
    def has_permission(self, request, view):
        return True


class CanRevokeCertificates(permissions.BasePermission):
    """
    Only staff members can revoke certificates.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsStudentOrStaffReadOnly(permissions.BasePermission):
    """
    Students can view their own certificates.
    Staff can view and modify all certificates.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True

        # Students can only view their own certificates
        if request.method in permissions.SAFE_METHODS:
            return obj.student.student == request.user

        return False


class CanManageTemplates(permissions.BasePermission):
    """
    Only staff can manage certificate templates.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and request.user.is_staff
