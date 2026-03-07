"""
Tests for forums app permissions.
"""

from unittest.mock import MagicMock

from django.contrib.auth.models import Group, Permission
from django.test import TestCase, RequestFactory

from forums.permissions import (
    CanAccessCategory,
    CanLockThreads,
    CanModerateThreads,
    CanPinThreads,
    IsAuthenticatedOrReadOnly,
    IsAuthorOrModeratorOrReadOnly,
    IsAuthorOrReadOnly,
    IsNotLocked,
)
from tests.helpers import TestDataMixin


class TestIsAuthenticatedOrReadOnly(TestDataMixin, TestCase):
    """Tests for IsAuthenticatedOrReadOnly permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAuthenticatedOrReadOnly()

    def test_unauthenticated_can_read(self):
        """Unauthenticated users should be able to read."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.get("/")
        request.user = AnonymousUser()
        self.assertTrue(self.permission.has_permission(request, None))

    def test_unauthenticated_cannot_write(self):
        """Unauthenticated users should not be able to write."""
        from django.contrib.auth.models import AnonymousUser
        request = self.factory.post("/")
        request.user = AnonymousUser()
        self.assertFalse(self.permission.has_permission(request, None))

    def test_authenticated_can_write(self):
        """Authenticated users should be able to write."""
        user = self.create_user()
        request = self.factory.post("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))


class TestIsAuthorOrReadOnly(TestDataMixin, TestCase):
    """Tests for IsAuthorOrReadOnly permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAuthorOrReadOnly()

    def test_read_permission_allowed_for_anyone(self):
        """Read access should be allowed for any user."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        obj = MagicMock()
        obj.author = self.create_user()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_author_can_write(self):
        """Authors should be able to edit their own content."""
        user = self.create_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.author = user
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_author_cannot_write(self):
        """Non-authors should not be able to edit content."""
        user = self.create_user()
        other = self.create_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.author = other
        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class TestIsAuthorOrModeratorOrReadOnly(TestDataMixin, TestCase):
    """Tests for IsAuthorOrModeratorOrReadOnly permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsAuthorOrModeratorOrReadOnly()

    def test_read_permission_allowed(self):
        """Read access should be allowed for any user."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        obj = MagicMock()
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_author_can_write(self):
        """Authors should be able to write."""
        user = self.create_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.author = user
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_moderator_can_write(self):
        """Users with moderation permission should be able to write."""
        user = self.create_user()
        perm = Permission.objects.get(codename='can_moderate_threads')
        user.user_permissions.add(perm)
        # Clear permission cache
        user = type(user).objects.get(pk=user.pk)

        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.author = self.create_user()  # different author
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_non_author_non_moderator_cannot_write(self):
        """Non-authors without moderation perms should be denied write access."""
        user = self.create_user()
        request = self.factory.put("/")
        request.user = user
        obj = MagicMock()
        obj.author = self.create_user()
        self.assertFalse(self.permission.has_object_permission(request, None, obj))


class TestCanModerateThreads(TestDataMixin, TestCase):
    """Tests for CanModerateThreads permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanModerateThreads()

    def test_user_with_perm_can_moderate(self):
        """Users with can_moderate_threads permission should be allowed."""
        user = self.create_user()
        perm = Permission.objects.get(codename='can_moderate_threads')
        user.user_permissions.add(perm)
        user = type(user).objects.get(pk=user.pk)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_without_perm_denied(self):
        """Users without the permission should be denied."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))


class TestCanPinThreads(TestDataMixin, TestCase):
    """Tests for CanPinThreads permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanPinThreads()

    def test_user_with_perm_can_pin(self):
        """Users with can_pin_threads permission should be allowed."""
        user = self.create_user()
        perm = Permission.objects.get(codename='can_pin_threads')
        user.user_permissions.add(perm)
        user = type(user).objects.get(pk=user.pk)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_without_perm_denied(self):
        """Users without the permission should be denied."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))


class TestCanLockThreads(TestDataMixin, TestCase):
    """Tests for CanLockThreads permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanLockThreads()

    def test_user_with_perm_can_lock(self):
        """Users with can_lock_threads permission should be allowed."""
        user = self.create_user()
        perm = Permission.objects.get(codename='can_lock_threads')
        user.user_permissions.add(perm)
        user = type(user).objects.get(pk=user.pk)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_without_perm_denied(self):
        """Users without the permission should be denied."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))


class TestIsNotLocked(TestDataMixin, TestCase):
    """Tests for IsNotLocked permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = IsNotLocked()

    def test_unlocked_thread_allowed(self):
        """Posting in an unlocked thread should be allowed."""
        user = self.create_user()
        request = self.factory.post("/")
        request.user = user
        obj = MagicMock()
        obj.is_locked = False
        self.assertTrue(self.permission.has_object_permission(request, None, obj))

    def test_locked_thread_denied(self):
        """Posting in a locked thread should be denied."""
        user = self.create_user()
        request = self.factory.post("/")
        request.user = user
        obj = MagicMock()
        obj.is_locked = True
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_post_in_locked_thread_denied(self):
        """Post objects with locked parent thread should be denied."""
        user = self.create_user()
        request = self.factory.post("/")
        request.user = user
        obj = MagicMock(spec=['thread'])
        obj.thread.is_locked = True
        # Remove is_locked from obj itself since spec=['thread']
        self.assertFalse(self.permission.has_object_permission(request, None, obj))

    def test_object_without_locked_attr_allowed(self):
        """Objects without is_locked or thread should be allowed."""
        user = self.create_user()
        request = self.factory.post("/")
        request.user = user
        obj = MagicMock(spec=[])  # no attributes
        self.assertTrue(self.permission.has_object_permission(request, None, obj))


class TestCanAccessCategory(TestDataMixin, TestCase):
    """Tests for CanAccessCategory permission."""

    def setUp(self):
        self.factory = RequestFactory()
        self.permission = CanAccessCategory()

    def test_category_without_groups_allows_access(self):
        """Categories without group restrictions should allow everyone."""
        user = self.create_user()
        request = self.factory.get("/")
        request.user = user
        category = self.create_forum_category()
        # category.allowed_groups is empty by default
        self.assertTrue(self.permission.has_object_permission(request, None, category))

    def test_user_in_allowed_group_has_access(self):
        """Users in an allowed group should have access."""
        user = self.create_user()
        group = Group.objects.create(name='test_forum_group')
        user.groups.add(group)

        category = self.create_forum_category()
        category.allowed_groups.add(group)

        request = self.factory.get("/")
        request.user = user
        self.assertTrue(self.permission.has_object_permission(request, None, category))

    def test_user_not_in_allowed_group_denied(self):
        """Users not in an allowed group should be denied."""
        user = self.create_user()
        group = Group.objects.create(name='restricted_group')

        category = self.create_forum_category()
        category.allowed_groups.add(group)

        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_object_permission(request, None, category))
