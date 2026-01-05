"""
Permissions for forums app.
"""

from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access to unauthenticated users,
    but require authentication for write operations.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Allow authors to edit/delete their own content,
    others can only read.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for author
        return obj.author == request.user


class IsAuthorOrModeratorOrReadOnly(permissions.BasePermission):
    """
    Allow authors and moderators to edit/delete content,
    others can only read.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions for author
        if obj.author == request.user:
            return True

        # Check moderator permissions
        return request.user.has_perm('forums.can_moderate_threads')


class CanModerateThreads(permissions.BasePermission):
    """
    Only users with moderation permissions can perform moderation actions.
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('forums.can_moderate_threads')


class CanPinThreads(permissions.BasePermission):
    """
    Only users with pin permission can pin threads.
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('forums.can_pin_threads')


class CanLockThreads(permissions.BasePermission):
    """
    Only users with lock permission can lock threads.
    """
    def has_permission(self, request, view):
        return request.user and request.user.has_perm('forums.can_lock_threads')


class IsNotLocked(permissions.BasePermission):
    """
    Prevent posting in locked threads.
    """
    def has_object_permission(self, request, view, obj):
        # Check if thread is locked
        if hasattr(obj, 'is_locked'):
            return not obj.is_locked
        elif hasattr(obj, 'thread'):
            return not obj.thread.is_locked
        return True


class CanAccessCategory(permissions.BasePermission):
    """
    Check if user has access to category based on group permissions.
    """
    def has_object_permission(self, request, view, obj):
        category = obj if hasattr(obj, 'allowed_groups') else obj.category

        # If no groups specified, everyone has access
        if not category.allowed_groups.exists():
            return True

        # Check if user belongs to any allowed group
        if request.user.is_authenticated:
            user_groups = request.user.groups.all()
            return category.allowed_groups.filter(id__in=user_groups).exists()

        return False
