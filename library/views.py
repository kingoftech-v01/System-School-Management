from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from accounts.decorators import direction_only, tenant_required, role_required
from django_ratelimit.decorators import ratelimit
from datetime import date, timedelta
from .models import Book, BorrowRecord


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def book_list(request):
    """List all books."""
    books = Book.objects.filter(tenant=request.tenant).order_by('title')
    return render(request, 'library/book_list.html', {'books': books, 'title': _('Library Books')})


@login_required
@role_required('student')
@tenant_required
@ratelimit(key='user', rate='20/h', method='POST')
def borrow_book(request, book_id):
    """Borrow a book."""
    book = get_object_or_404(Book, id=book_id, tenant=request.tenant)

    if book.available > 0:
        BorrowRecord.objects.create(
            tenant=request.tenant,
            book=book,
            student=request.user,
            due_date=date.today() + timedelta(days=14)
        )
        book.available -= 1
        book.save()
        messages.success(request, f'Successfully borrowed {book.title}')
    else:
        messages.error(request, 'Book not available')

    return redirect('library:book_list')


@login_required
@role_required('student')
@tenant_required
def my_borrowed_books(request):
    """View student's borrowed books."""
    records = BorrowRecord.objects.filter(
        student=request.user,
        tenant=request.tenant
    ).order_by('-borrowed_at')

    return render(request, 'library/my_books.html', {
        'records': records,
        'title': _('My Borrowed Books')
    })


@login_required
@role_required('student')
@tenant_required
@ratelimit(key='user', rate='20/h', method='POST')
def return_book(request, record_id):
    """Return a borrowed book."""
    record = get_object_or_404(
        BorrowRecord,
        id=record_id,
        student=request.user,
        tenant=request.tenant,
        status__in=['borrowed', 'overdue']
    )

    record.status = 'returned'
    record.returned_at = date.today()
    record.save()

    # Increase available copies
    record.book.available += 1
    record.book.save()

    messages.success(request, f'Successfully returned {record.book.title}')
    return redirect('library:my_borrowed_books')
