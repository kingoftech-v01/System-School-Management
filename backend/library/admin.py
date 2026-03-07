from django.contrib import admin
from .models import Book, BorrowRecord


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'quantity', 'available', 'tenant')
    list_filter = ('filiere', 'category', 'tenant')
    search_fields = ('title', 'author', 'isbn')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'borrowed_at', 'due_date', 'status', 'tenant')
    list_filter = ('status', 'tenant')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request, 'tenant'):
            qs = qs.filter(tenant=request.tenant)
        return qs
