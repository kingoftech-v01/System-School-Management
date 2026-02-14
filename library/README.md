# Library App

Book inventory and lending management with hierarchical categories, ISBN validation, barcode support, and borrow/return tracking.

## Description

The library app manages the school's book inventory and lending operations. It provides book listing with search, category filtering, and pagination for all authenticated users. Students can borrow available books (with automatic 14-day due dates), view their personal borrow history, and return borrowed books. Librarians (and higher roles) can create, edit, and delete books, and view overdue borrow records. The app supports hierarchical book categories via django-mptt, ISBN-10/ISBN-13 checksum validation, barcode/RFID fields, and cover image uploads.

The app exposes two interfaces: a set of template-based frontend views (9 views) and a REST API via Django REST Framework (2 ViewSets). Both share the same models and database tables.

## Main Features

- **Book Listing**: Browse all books with search (title, author, ISBN), category filter dropdown, and pagination (20 per page). Shows inventory stats (total books, available count).
- **Book Detail**: View full book information including description, category, publisher, availability, cover image. Librarian/direction/admin roles see recent borrow history for the book; students see whether they currently have the book borrowed.
- **Book Create**: Librarians add new books via form with tenant auto-assignment.
- **Book Edit**: Librarians update existing book information.
- **Book Delete**: Librarians delete books with confirmation page. Active borrows prevent deletion.
- **Borrow Books**: Students borrow available books with automatic 14-day due date.
- **Return Books**: Students return borrowed books (status set to returned, available count incremented).
- **My Borrowed Books**: Students view their personal borrow history ordered by most recent.
- **Overdue Books**: Librarians view all overdue borrow records with pagination.
- **ISBN Validation**: ISBN-10 and ISBN-13 checksum validation (supports hyphens and spaces).
- **Hierarchical Categories**: MPTT-based category tree with recursive book counts.
- **Celery Task**: `send_overdue_reminders` marks overdue records and sends email notifications.

## User Roles

The system has 10 roles. The library app uses the following access patterns:

| Role | Frontend Permissions | Notes |
|------|----------------------|-------|
| student | View book list, view book detail, borrow books, view own borrowed books, return books | Uses `@role_required('student')` for borrow/return/my-books |
| professor | View book list, view book detail | No borrow or management access |
| direction | View book list, view book detail (with borrow history), create/edit/delete books, view overdue | Via `@librarian_only` decorator |
| parent | View book list, view book detail | No borrow or management access |
| admin | View book list, view book detail (with borrow history), create/edit/delete books, view overdue | Via `@librarian_only` decorator |
| prefet | View book list, view book detail | No borrow or management access |
| accountant | View book list, view book detail | No library-specific management access |
| secretary | View book list, view book detail (with borrow history), create/edit/delete books, view overdue | Via `@librarian_only` decorator |
| librarian | View book list, view book detail (with borrow history), create/edit/delete books, view overdue | Primary library management role via `@librarian_only` |
| registrar | View book list, view book detail | No library-specific management access |

**Decorator details**: `@librarian_only` is a shortcut for `@role_required('librarian', 'secretary', 'direction', 'admin')`. The `book_list` and `book_detail` views use only `@login_required` + `@tenant_required`, so all authenticated users can access them.

## CRUD Summary

| Entity | Create | Read | Update | Delete | Who |
|--------|--------|------|--------|--------|-----|
| Book | `book_create` | `book_list` + `book_detail` | `book_edit` | `book_delete` (with confirmation, blocks if active borrows) | librarian, secretary, direction, admin |
| BorrowRecord | `borrow_book` (student) | `my_borrowed_books` (student), `book_detail` borrow history (librarian+) | `return_book` (student) | No | Students borrow/return; librarian+ views history |
| BookCategory | No frontend CRUD | Filter dropdown in `book_list`, displayed in `book_detail` | No | No | Admin site only |
| Publisher | No frontend CRUD | Displayed in `book_detail` | No | No | Admin site only |

## Models

- **`BookCategory`** (MPTTModel) -- Hierarchical book categorization. Fields: `name` (CharField max 100, unique), `parent` (TreeForeignKey self, CASCADE), `description` (TextField), `is_active` (BooleanField, default True). Methods: `get_book_count()` (recursive). MPTT ordered by `name`.
- **`Publisher`** -- Publisher database. Fields: `name` (CharField max 200, unique), `country` (CharField max 100), `website` (URLField), `email` (EmailField), `phone` (CharField max 20), `created_at` (auto). Ordered by `name`.
- **`Book`** -- Book inventory. Fields: `tenant` (FK core.School, CASCADE), `title` (CharField max 300), `author` (CharField max 200), `isbn` (CharField max 20, unique, validated), `filiere` (FK filieres.Filiere, SET_NULL), `category` (TreeForeignKey BookCategory, SET_NULL), `publisher` (FK Publisher, SET_NULL), `publication_year` (IntegerField), `edition` (CharField max 50), `language` (CharField max 50, default "English"), `pages` (IntegerField), `barcode` (CharField max 50, unique), `quantity` (IntegerField, default 1), `available` (IntegerField, default 1), `shelf_location` (CharField max 50), `cover_image` (ImageField), `description` (TextField), `tags` (CharField max 200), `created_at` (auto), `updated_at` (auto). Indexed on `isbn`, `barcode`, `[category, title]`. Methods: `is_available()`, `borrow()`, `return_book()`. Ordered by `title`.
- **`BorrowRecord`** -- Book borrowing records. Fields: `tenant` (FK core.School, CASCADE), `book` (FK Book, CASCADE), `student` (FK AUTH_USER_MODEL, CASCADE), `borrowed_at` (DateTimeField auto), `due_date` (DateField), `returned_at` (DateTimeField, nullable), `status` (CharField max 20, choices: borrowed/returned/overdue/lost, default "borrowed"), `fine_amount` (DecimalField 6,2, default 0), `notes` (TextField). Methods: `is_overdue()`. Ordered by `-borrowed_at`.

## URL Namespaces

- Frontend: `frontend:library:<view_name>`
- API: `api:v1:library:<resource-name>`

### Frontend Routes

| URL Pattern | View | Name | Decorator |
|-------------|------|------|-----------|
| `library/` | `book_list` | `book_list` | `@login_required`, `@tenant_required`, `@ratelimit(100/h)` |
| `library/create/` | `book_create` | `book_create` | `@login_required`, `@librarian_only`, `@tenant_required`, `@ratelimit(50/h POST)` |
| `library/overdue/` | `overdue_books` | `overdue_books` | `@login_required`, `@librarian_only`, `@tenant_required`, `@ratelimit(100/h)` |
| `library/<int:pk>/` | `book_detail` | `book_detail` | `@login_required`, `@tenant_required`, `@ratelimit(100/h)` |
| `library/<int:pk>/edit/` | `book_edit` | `book_edit` | `@login_required`, `@librarian_only`, `@tenant_required`, `@ratelimit(50/h POST)` |
| `library/<int:pk>/delete/` | `book_delete` | `book_delete` | `@login_required`, `@librarian_only`, `@tenant_required`, `@ratelimit(50/h POST)` |
| `library/my-borrowed/` | `my_borrowed_books` | `my_borrowed_books` | `@login_required`, `@role_required('student')`, `@tenant_required` |
| `library/borrow/<int:book_id>/` | `borrow_book` | `borrow_book` | `@login_required`, `@role_required('student')`, `@tenant_required`, `@ratelimit(20/h POST)` |
| `library/return/<int:record_id>/` | `return_book` | `return_book` | `@login_required`, `@role_required('student')`, `@tenant_required`, `@ratelimit(20/h POST)` |

### API Endpoints

| Prefix | ViewSet | Methods | Permission |
|--------|---------|---------|------------|
| `books/` | `BookViewSet` | GET (list), GET (detail), POST, PUT, PATCH, DELETE | `IsAuthenticated` |
| `borrow-records/` | `BorrowRecordViewSet` | GET (list), GET (detail), POST, PUT, PATCH, DELETE | `IsAuthenticated` |

**Note**: The API ViewSets use `ModelViewSet` which exposes full CRUD. There is no tenant scoping on the API -- `get_queryset` returns `Book.objects.all()` / `BorrowRecord.objects.all()` without filtering by tenant. This is a security issue (see TODO.md).

## Configuration

| Setting | Value | Source |
|---------|-------|--------|
| `DEFAULT_FROM_EMAIL` | Used by `send_overdue_reminders` task | `django.conf.settings` |
| Rate limits | 20-100 requests/hour per user depending on view | `django-ratelimit` |
| Borrow period | 14 days (hardcoded in `borrow_book` view) | `views_frontend.py:73` |
| Pagination | 20 items per page (book_list, overdue_books) | `views_frontend.py` |
| Cover image upload | `library/covers/%Y/%m/` | `models.py:168` |

## Dependencies

- **`core`** -- School model for tenant FK on Book and BorrowRecord
- **`accounts`** -- User model (for BorrowRecord.student FK), role decorators (`@login_required`, `@role_required`, `@tenant_required`, `@librarian_only`)
- **`filieres`** -- Optional Filiere FK on Book (SET_NULL)
- **`django-mptt`** -- Hierarchical BookCategory tree (MPTTModel, TreeForeignKey)
- **`django-ratelimit`** -- Rate limiting on all frontend views
- **`djangorestframework`** -- API ViewSets, serializers, permissions
- **`celery`** -- `send_overdue_reminders` task in `tasks.py`
- **`Pillow`** -- Required for `ImageField` on Book.cover_image

## File Structure

```
library/
    __init__.py
    admin.py                 # Admin registration for Book and BorrowRecord with tenant scoping
    apps.py                  # LibraryConfig (verbose_name='Library Management')
    forms.py                 # 2 ModelForms (BookForm, BorrowForm)
    models.py                # 4 models + 1 validator (BookCategory, Publisher, Book, BorrowRecord, validate_isbn)
    serializers.py           # 2 DRF serializers (BookSerializer, BorrowRecordSerializer) using fields='__all__'
    tasks.py                 # 1 Celery task (send_overdue_reminders)
    urls.py                  # Frontend (9 routes) + API (2 ViewSets via DefaultRouter) URL routing
    views_api.py             # 2 DRF ModelViewSets (BookViewSet, BorrowRecordViewSet)
    views_frontend.py        # 9 template-based views
    migrations/
        __init__.py
        0001_initial.py
    tests/
        __init__.py
        test_admin.py        # 8 tests for admin registration and configuration
        test_forms.py        # 6 tests for BookForm and BorrowForm
        test_models.py       # 25 tests for all models and ISBN validation
        test_serializers.py  # 4 tests for BookSerializer and BorrowRecordSerializer
        test_tasks.py        # 4 tests for send_overdue_reminders task
        test_views_api.py    # 6 tests for BookViewSet and BorrowRecordViewSet
        test_views_frontend.py  # 30 tests for all frontend views
```

### Templates

```
templates/library/
    book_list.html           # Book listing with search, category filter, pagination
    book_detail.html         # Single book details with borrow history (librarian+)
    book_form.html           # Shared create/edit form template
    book_confirm_delete.html # Delete confirmation with active borrow warning
    my_books.html            # Student's borrowed books list
    overdue_books.html       # Overdue borrow records list with pagination
```
