"""
Permissions for analytics app.
"""

from rest_framework import permissions


class CanViewAnalytics(permissions.BasePermission):
    """
    Only staff and instructors can view analytics.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_lecturer))


class CanViewOwnAnalytics(permissions.BasePermission):
    """
    Students can view their own analytics.
    Staff and instructors can view all analytics.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff and instructors can view all
        if request.user.is_staff or request.user.is_lecturer:
            return True

        # Students can only view their own analytics
        if hasattr(obj, 'student'):
            return obj.student.student == request.user

        return False


class CanManageAtRiskStudents(permissions.BasePermission):
    """
    Only staff and instructors can manage at-risk student records.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return (request.user and request.user.is_authenticated and
                    (request.user.is_staff or request.user.is_lecturer))

        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_lecturer))


class CanViewActivityLogs(permissions.BasePermission):
    """
    Only staff can view detailed activity logs.
    Students can view their own activity logs.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view all logs
        if request.user.is_staff:
            return True

        # Students can only view their own logs
        return obj.student.student == request.user


class CanViewLearningOutcomes(permissions.BasePermission):
    """
    Staff and instructors can view learning outcomes.
    Students can view outcomes for their enrolled courses.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff and instructors can view all
        if request.user.is_staff or request.user.is_lecturer:
            return True

        # Students can view outcomes for enrolled courses
        if hasattr(obj, 'course'):
            from accounts.models import Student
            try:
                student = Student.objects.get(student=request.user)
                return student.enrollments.filter(course=obj.course).exists()
            except Student.DoesNotExist:
                return False

        return False


class CanManageLearningOutcomes(permissions.BasePermission):
    """
    Only staff and instructors can create/edit learning outcomes.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_lecturer))


class CanExportAnalytics(permissions.BasePermission):
    """
    Only staff and instructors can export analytics data.
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                (request.user.is_staff or request.user.is_lecturer))
