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
    actions = ["generate_parent_codes", "generate_staff_codes", "generate_prefet_codes", "generate_accountant_codes", "generate_secretary_codes", "generate_librarian_codes", "generate_registrar_codes", "deactivate_codes"]

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

    def generate_accountant_codes(self, request, queryset):
        """Generate 5 new accountant invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='accountant',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} accountant invitation codes created.")
    generate_accountant_codes.short_description = "Generate 5 accountant invitation codes"

    def generate_secretary_codes(self, request, queryset):
        """Generate 5 new secretary invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='secretary',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} secretary invitation codes created.")
    generate_secretary_codes.short_description = "Generate 5 secretary invitation codes"

    def generate_librarian_codes(self, request, queryset):
        """Generate 5 new librarian invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='librarian',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} librarian invitation codes created.")
    generate_librarian_codes.short_description = "Generate 5 librarian invitation codes"

    def generate_registrar_codes(self, request, queryset):
        """Generate 5 new registrar invitation codes."""
        expiry_days = getattr(settings, 'INVITATION_CODE_EXPIRY_DAYS', 7)
        created = 0
        for _ in range(5):
            InvitationCode.objects.create(
                code=InvitationCode.generate_code(),
                role='registrar',
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            created += 1
        self.message_user(request, f"{created} registrar invitation codes created.")
    generate_registrar_codes.short_description = "Generate 5 registrar invitation codes"

    def deactivate_codes(self, request, queryset):
        """Deactivate selected invitation codes."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} invitation codes deactivated.")
    deactivate_codes.short_description = "Deactivate selected codes"


class SecureAdminSite(admin.AdminSite):
    """Custom admin site requiring 2FA for access."""
    site_header = 'School Management Administration'
    site_title = 'School Admin'

    def has_permission(self, request):
        """Require 2FA for admin access."""
        if not super().has_permission(request):
            return False
        # Require 2FA
        has_2fa = False
        if hasattr(request.user, 'totpdevice_set'):
            has_2fa = request.user.totpdevice_set.filter(confirmed=True).exists()
        return has_2fa


secure_admin_site = SecureAdminSite(name='secure_admin')

# Register with both default and secure admin
admin.site.register(User, UserAdmin)
admin.site.register(Student)
admin.site.register(Parent)
admin.site.register(InvitationCode, InvitationCodeAdmin)

secure_admin_site.register(User, UserAdmin)
secure_admin_site.register(Student)
secure_admin_site.register(Parent)
secure_admin_site.register(InvitationCode, InvitationCodeAdmin)
