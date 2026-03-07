"""Tests for notes admin configuration."""

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from tests.helpers import TestDataMixin
from notes.models import ProfessorNote, NoteHistory, NoteComment
from notes.admin import ProfessorNoteAdmin, NoteHistoryAdmin, NoteCommentAdmin


class NotesAdminRegistrationTest(TestDataMixin, TestCase):
    """Test that all notes models are registered in the admin."""

    def test_professor_note_registered(self):
        self.assertIn(ProfessorNote, admin.site._registry)

    def test_note_history_registered(self):
        self.assertIn(NoteHistory, admin.site._registry)

    def test_note_comment_registered(self):
        self.assertIn(NoteComment, admin.site._registry)


class ProfessorNoteAdminTest(TestDataMixin, TestCase):
    """Test ProfessorNoteAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = ProfessorNoteAdmin(ProfessorNote, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('student', 'professor', 'subject', 'note_type', 'score', 'weighted_score', 'status', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('status', 'note_type', 'tenant', 'created_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_search_fields(self):
        expected = ('student__username', 'student__first_name', 'student__last_name', 'professor__username')
        self.assertEqual(self.admin.search_fields, expected)

    def test_readonly_fields(self):
        expected = ('created_at', 'updated_at', 'approved_at', 'approved_by', 'weighted_score')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_inlines(self):
        from notes.admin import NoteHistoryInline
        inline_classes = [type(i) for i in self.admin.get_inline_instances(None)]
        self.assertIn(NoteHistoryInline, inline_classes)

    def test_fieldsets_exist(self):
        self.assertIsNotNone(self.admin.fieldsets)
        fieldset_names = [f[0] for f in self.admin.fieldsets]
        self.assertIn('Basic Information', fieldset_names)
        self.assertIn('Score Details', fieldset_names)
        self.assertIn('Status & Approval', fieldset_names)

    def test_get_queryset_superuser(self):
        admin_user = self.create_admin_user()
        request = self.factory.get("/admin/")
        request.user = admin_user
        qs = self.admin.get_queryset(request)
        self.assertIsNotNone(qs)


class NoteHistoryAdminTest(TestDataMixin, TestCase):
    """Test NoteHistoryAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NoteHistoryAdmin(NoteHistory, self.site)
        self.factory = RequestFactory()

    def test_list_display(self):
        expected = ('note', 'action', 'changed_by', 'changed_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        expected = ('action', 'changed_at')
        self.assertEqual(self.admin.list_filter, expected)

    def test_readonly_fields(self):
        expected = ('note', 'action', 'changed_by', 'changed_at', 'old_values', 'new_values', 'change_summary')
        self.assertEqual(self.admin.readonly_fields, expected)

    def test_has_add_permission_returns_false(self):
        request = self.factory.get("/admin/")
        request.user = self.create_admin_user()
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_delete_permission_returns_false(self):
        request = self.factory.get("/admin/")
        request.user = self.create_admin_user()
        self.assertFalse(self.admin.has_delete_permission(request))


class NoteCommentAdminTest(TestDataMixin, TestCase):
    """Test NoteCommentAdmin configuration."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = NoteCommentAdmin(NoteComment, self.site)

    def test_list_display(self):
        expected = ('note', 'author', 'created_at')
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('created_at',))

    def test_readonly_fields(self):
        self.assertEqual(self.admin.readonly_fields, ('created_at',))
