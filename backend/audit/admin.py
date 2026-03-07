from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline

from .models import FieldChangeRecord


class AuditTrailInline(GenericTabularInline):
    """Add to any model's admin to show its field change history."""

    model = FieldChangeRecord
    ct_field = 'content_type'
    ct_fk_field = 'object_id'
    extra = 0
    readonly_fields = [
        'field_name', 'old_value', 'new_value',
        'changed_by', 'changed_at', 'change_reason', 'action',
    ]
    can_delete = False
    ordering = ['-changed_at']

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(FieldChangeRecord)
class FieldChangeRecordAdmin(admin.ModelAdmin):
    list_display = [
        'content_type', 'object_id', 'field_name',
        'old_value_short', 'new_value_short',
        'changed_by', 'changed_at', 'action',
    ]
    list_filter = ['content_type', 'action', 'changed_at']
    search_fields = ['field_name', 'old_value', 'new_value', 'change_reason']
    readonly_fields = [
        'content_type', 'object_id', 'field_name', 'field_verbose_name',
        'old_value', 'new_value', 'changed_by', 'changed_at',
        'change_reason', 'batch_id', 'action',
    ]
    date_hierarchy = 'changed_at'

    def old_value_short(self, obj):
        val = obj.old_value or ''
        return val[:50] + '...' if len(val) > 50 else val
    old_value_short.short_description = 'Old Value'

    def new_value_short(self, obj):
        val = obj.new_value or ''
        return val[:50] + '...' if len(val) > 50 else val
    new_value_short.short_description = 'New Value'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
