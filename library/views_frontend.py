from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import direction_only, librarian_only, tenant_required, role_required
from django_ratelimit.decorators import ratelimit
from datetime import date, timedelta
from .models import Book, BorrowRecord, BookCategory
from .forms import BookForm


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def book_list(request):
    """List all books with search, category filter, and pagination."""
    books = Book.objects.filter(tenant=request.tenant).select_related('category', 'publisher')

    # Search by title, author, isbn
    query = request.GET.get('q', '').strip()
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    # Category filter
    category_id = request.GET.get('category', '').strip()
    if category_id:
        books = books.filter(category_id=category_id)

    books = books.order_by('title')

    # Pagination (20 per page)
    paginator = Paginator(books, 20)
    page = request.GET.get('page')
    books_page = paginator.get_page(page)

    # Get categories for filter dropdown
    categories = BookCategory.objects.filter(is_active=True)

    # Inventory stats
    total_books = Book.objects.filter(tenant=request.tenant).count()
    available_count = Book.objects.filter(tenant=request.tenant, available__gt=0).count()

    return render(request, 'library/book_list.html', {
        'books': books_page,
        'query': query,
        'selected_category': category_id,
        'categories': categories,
        'total_books': total_books,
        'available_count': available_count,
        'title': _('Library Books'),
    })


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

    return redirect('frontend:library:book_list')


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
    return redirect('frontend:library:my_borrowed_books')


@login_required
@tenant_required
@ratelimit(key='user', rate='100/h')
def book_detail(request, pk):
    """Show a single book's details."""
    book = get_object_or_404(
        Book.objects.select_related('category', 'publisher', 'filiere'),
        pk=pk,
        tenant=request.tenant
    )

    # Get recent borrow records for this book (direction only)
    borrow_records = None
    if request.user.role in ('librarian', 'secretary', 'direction', 'admin') or request.user.is_superuser:
        borrow_records = BorrowRecord.objects.filter(
            book=book,
            tenant=request.tenant
        ).select_related('student').order_by('-borrowed_at')[:20]

    # Check if current user has already borrowed this book
    user_has_borrowed = False
    if request.user.role == 'student':
        user_has_borrowed = BorrowRecord.objects.filter(
            book=book, student=request.user, status='borrowed'
        ).exists()

    return render(request, 'library/book_detail.html', {
        'book': book,
        'borrow_records': borrow_records,
        'user_has_borrowed': user_has_borrowed,
        'title': book.title,
    })


@login_required
@librarian_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def book_create(request):
    """Create a new book in the library."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.tenant = request.tenant
            book.save()
            messages.success(request, _('Book added to library successfully.'))
            return redirect('frontend:library:book_detail', pk=book.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = BookForm()

    return render(request, 'library/book_form.html', {
        'form': form,
        'title': _('Add New Book'),
    })


@login_required
@librarian_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def book_edit(request, pk):
    """Edit an existing book."""
    book = get_object_or_404(Book, pk=pk, tenant=request.tenant)

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, _('Book updated successfully.'))
            return redirect('frontend:library:book_detail', pk=book.pk)
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = BookForm(instance=book)

    return render(request, 'library/book_form.html', {
        'form': form,
        'book': book,
        'title': _('Edit Book: %(title)s') % {'title': book.title},
    })


@login_required
@librarian_only
@tenant_required
@ratelimit(key='user', rate='50/h', method='POST')
def book_delete(request, pk):
    """Delete a book. GET shows confirmation, POST deletes."""
    book = get_object_or_404(Book, pk=pk, tenant=request.tenant)

    # Check for active borrows
    active_borrows = BorrowRecord.objects.filter(
        book=book,
        status__in=['borrowed', 'overdue']
    ).count()

    if request.method == 'POST':
        if active_borrows > 0:
            messages.error(
                request,
                _('Cannot delete book with %(count)d active borrow(s). Please resolve them first.')
                % {'count': active_borrows}
            )
            return redirect('frontend:library:book_detail', pk=book.pk)

        book.delete()
        messages.success(request, _('Book deleted successfully.'))
        return redirect('frontend:library:book_list')

    return render(request, 'library/book_confirm_delete.html', {
        'book': book,
        'active_borrows': active_borrows,
        'title': _('Delete Book: %(title)s') % {'title': book.title},
    })


@login_required
@librarian_only
@tenant_required
@ratelimit(key='user', rate='100/h')
def overdue_books(request):
    """List all overdue borrow records."""
    from django.utils import timezone

    overdue_records = BorrowRecord.objects.filter(
        tenant=request.tenant
    ).filter(
        Q(status='overdue') |
        Q(status='borrowed', due_date__lt=timezone.now().date())
    ).select_related('book', 'student').order_by('due_date')

    # Pagination
    paginator = Paginator(overdue_records, 20)
    page = request.GET.get('page')
    records_page = paginator.get_page(page)

    return render(request, 'library/overdue_books.html', {
        'records': records_page,
        'total_overdue': paginator.count,
        'title': _('Overdue Books'),
    })
