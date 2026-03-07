"""
django-import-export Resource classes for accounts models.
Enables bulk CSV/Excel import and export of students and parents.
"""

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from accounts.models import Student, User, Parent
from course.models import Program


class StudentResource(resources.ModelResource):
    """Resource for bulk student import/export."""
    first_name = fields.Field(
        attribute='student__first_name',
        column_name='first_name',
    )
    last_name = fields.Field(
        attribute='student__last_name',
        column_name='last_name',
    )
    email = fields.Field(
        attribute='student__email',
        column_name='email',
    )
    program = fields.Field(
        attribute='program',
        column_name='program',
        widget=ForeignKeyWidget(Program, field='title'),
    )

    class Meta:
        model = Student
        import_id_fields = ['registration_number']
        fields = (
            'registration_number', 'first_name', 'last_name', 'email',
            'level', 'program', 'is_alumni', 'is_dropped',
        )
        export_order = fields

    def before_import_row(self, row, row_number=None, **kwargs):
        """Create or get the User for the student before import."""
        email = row.get('email', '')
        first_name = row.get('first_name', '')
        last_name = row.get('last_name', '')

        if email:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'student',
                    'is_student': True,
                }
            )
            if not created and first_name:
                user.first_name = first_name
                user.last_name = last_name
                user.save(update_fields=['first_name', 'last_name'])

            row['student'] = user.pk

    def after_import_row(self, row, row_result, row_number=None, **kwargs):
        """Link student to user after import."""
        if row_result.import_type in ('new', 'update'):
            reg_number = row.get('registration_number', '')
            if reg_number:
                try:
                    student = Student.objects.get(registration_number=reg_number)
                    if not student.student_id:
                        email = row.get('email', '')
                        user = User.objects.get(email=email)
                        student.student = user
                        student.save(update_fields=['student'])
                except Student.DoesNotExist:
                    pass


class ParentResource(resources.ModelResource):
    """Resource for bulk parent import/export."""
    first_name = fields.Field(
        attribute='user__first_name',
        column_name='first_name',
    )
    last_name = fields.Field(
        attribute='user__last_name',
        column_name='last_name',
    )
    email = fields.Field(
        attribute='user__email',
        column_name='email',
    )
    phone = fields.Field(
        attribute='user__phone',
        column_name='phone',
    )
    student_reg_number = fields.Field(
        attribute='student__registration_number',
        column_name='student_reg_number',
    )

    class Meta:
        model = Parent
        fields = (
            'id', 'first_name', 'last_name', 'email', 'phone',
            'student_reg_number', 'relation',
        )
