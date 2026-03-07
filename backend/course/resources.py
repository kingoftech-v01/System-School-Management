"""
django-import-export Resource classes for course models.
Enables bulk CSV/Excel import and export of programs and courses.
"""

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget

from course.models import Course, Program


class ProgramResource(resources.ModelResource):
    """Resource for bulk program import/export."""

    class Meta:
        model = Program
        import_id_fields = ['title']
        fields = ('title', 'summary')


class CourseResource(resources.ModelResource):
    """Resource for bulk course import/export."""
    program = fields.Field(
        attribute='program',
        column_name='program',
        widget=ForeignKeyWidget(Program, field='title'),
    )

    class Meta:
        model = Course
        import_id_fields = ['code']
        fields = (
            'code', 'title', 'credit', 'summary', 'program',
            'level', 'year', 'semester', 'is_elective',
        )
        export_order = fields
