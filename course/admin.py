from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Program, Course, CourseAllocation, Upload
from modeltranslation.admin import TranslationAdmin


class ProgramAdmin(TranslationAdmin):
    pass


class CourseAdmin(TranslationAdmin):
    search_fields = ['title', 'code', 'slug']
    list_display = ['title', 'code', 'credit', 'level', 'year', 'semester']
    list_filter = ['level', 'year', 'semester']


class UploadAdmin(TranslationAdmin):
    pass


admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseAllocation)
admin.site.register(Upload, UploadAdmin)
