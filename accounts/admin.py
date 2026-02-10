from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import User, Student, Parent, InvitationCode


class UserAdmin(admin.ModelAdmin):
    list_display = [
        "get_full_name",
        "username",
        "email",
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "is_staff",
        "role",
        "must_change_password",
    ]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
    ]
    list_filter = [
        "is_active",
        "is_student",
        "is_lecturer",
        "is_parent",
        "role",
        "must_change_password",
    ]

    class Meta:
        managed = True
        verbose_name = "User"
        verbose_name_plural = "Users"


class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "role",
        "linked_student",
        "is_active",
        "created_by",
        "used_by",
        "expires_at",
        "created_at",
    ]
    list_filter = ["role", "is_active"]
    search_fields = ["code", "sent_to_email"]
    readonly_fields = ["code", "created_at", "used_at", "used_by"]
    raw_id_fields = ["linked_student", "created_by"]
    actions = ["generate_parent_codes", "generate_staff_codes", "generate_prefet_codes", "deactivate_codes"]

    def generate_parent_codes(self, request, queryset):
        """Generate 5 new parent invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='parent',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} parent invitation codes created.")
    generate_parent_codes.short_description = "Generate 5 parent invitation codes"

    def generate_staff_codes(self, request, queryset):
        """Generate 5 new professor invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='professor',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} professor invitation codes created.")
    generate_staff_codes.short_description = "Generate 5 professor invitation codes"

    def generate_prefet_codes(self, request, queryset):
        """Generate 5 new discipline officer invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='prefet',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} discipline officer invitation codes created.")
    generate_prefet_codes.short_description = "Generate 5 discipline officer invitation codes"

    def deactivate_codes(self, request, queryset):
        """Deactivate selected invitation codes."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} invitation codes deactivated.")
    deactivate_codes.short_description = "Deactivate selected codes"


admin.site.register(User, UserAdmin)
admin.site.register(Student)
admin.site.register(Parent)
admin.site.register(InvitationCode, InvitationCodeAdmin)
