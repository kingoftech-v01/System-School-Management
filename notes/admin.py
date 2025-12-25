from django.contrib import admin
from .models import ProfessorNote, NoteHistory, NoteComment


class NoteHistoryInline(admin.TabularInline):
    model = NoteHistory
    extra = 0
    readonly_fields = ('action', 'changed_by', 'changed_at', 'old_values', 'new_values', 'change_summary')
    can_delete = False


@admin.register(ProfessorNote)
class ProfessorNoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'professor', 'subject', 'note_type', 'score', 'weighted_score', 'status', 'created_at')
    list_filter = ('status', 'note_type', 'tenant', 'created_at')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'professor__username')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'approved_by', 'weighted_score')
    inlines = [NoteHistoryInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('tenant', 'student', 'professor', 'subject', 'note_type')
        }),
        ('Score Details', {
            'fields': ('score', 'max_score', 'coefficient', 'weighted_score', 'comment')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_at', 'approval_notes')
        }),
        ('Private Notes', {
            'fields': ('private_note',),
            'classes': ('collapse',)
        }),
        ('Audit Trail', {
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(NoteHistory)
class NoteHistoryAdmin(admin.ModelAdmin):
    list_display = ('note', 'action', 'changed_by', 'changed_at')
    list_filter = ('action', 'changed_at')
    readonly_fields = ('note', 'action', 'changed_by', 'changed_at', 'old_values', 'new_values', 'change_summary')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NoteComment)
class NoteCommentAdmin(admin.ModelAdmin):
    list_display = ('note', 'author', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
