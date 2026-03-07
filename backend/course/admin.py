from django.contrib import admin
from django.contrib.auth.models import Group
from import_export.admin import ImportExportMixin

from .models import Program, Course, CourseAllocation, Upload
from .resources import ProgramResource, CourseResource
from modeltranslation.admin import TranslationAdmin


class ProgramAdmin(ImportExportMixin, TranslationAdmin):
    resource_class = ProgramResource


class CourseAdmin(ImportExportMixin, TranslationAdmin):
    resource_class = CourseResource
    search_fields = ['title', 'code', 'slug']
    list_display = ['title', 'code', 'credit', 'level', 'year', 'semester']
    list_filter = ['level', 'year', 'semester']


class UploadAdmin(TranslationAdmin):
    pass


admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAllocation)
admin.site.register(Upload, UploadAdmin)
