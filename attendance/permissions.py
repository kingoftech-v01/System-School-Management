from rest_framework.permissions import BasePermission
from attendance.models import Attendance, Subject, Group
from django.contrib.auth import get_user_model

User = get_user_model()


class IsTeacher(BasePermission):
    """Permission class for teacher-only views."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Check if user is staff, lecturer, or admin
        return (
            request.user.is_lecturer or
            request.user.is_staff or
            request.user.is_superuser
        )

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        # Superusers and staff have full access
        if request.user.is_superuser or request.user.is_staff:
            return True
        # Lecturers can only access their own objects
        if request.user.is_lecturer:
            return request.user == obj
        return False